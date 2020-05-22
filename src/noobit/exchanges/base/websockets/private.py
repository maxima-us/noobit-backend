import websockets
import asyncio
from typing import List

import ujson
from pydantic import ValidationError

from noobit.logging.structlogger import get_logger, log_exception

# models
from noobit.models.data.base.response import ErrorResponse, OKResponse
from noobit.models.data.base.types import PAIR, WS_ROUTE
from noobit.models.data.websockets.status import HeartBeat, SubscriptionStatus, SystemStatus
from noobit.models.data.websockets.stream.trade import TradesList
from noobit.models.data.response.order import OrdersByID

logger = get_logger(__name__)


class PrivateFeedReaderBase():


    # self.sub_parser = sthg_sthg

    def __init__(self,
                 pairs: List[PAIR] = None,
                 feeds: List[str] = ["trade", "order"]
                 ):
        self.pairs = pairs
        self.feeds = feeds

        self.ws = None
        self.terminate = False

        # we need to append order updates to order snapshot
        self.all_orders = {}
        self.feed_counters = {}

        self.route_to_method = {
            "heartbeat": self.publish_heartbeat,
            "system_status": self.publish_status_system,
            "subscription_status": self.publish_status_subscription,
            "trade": self.publish_data_trade,
            "order": self.publish_data_order,
        }



    async def subscribe(self, ping_interval: int, ping_timeout: int):

        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )

        for feed in self.feeds:
            try:

                # if we need to get an auth token, handle it in parser
                data = await self.subscription_parser.private(self.pairs, feed)


                payload = ujson.dumps(data)
                await self.ws.send(payload)
                await asyncio.sleep(0.1)

            except Exception as e:
                log_exception(logger, e)


    async def close(self):
        try:
            # await self.ws.wait_closed()
            await self.ws.close()
        except Exception as e:
            log_exception(logger, e)


    async def msg_handler(self, msg, redis_pool):
        """feedhandler will async iterate over message
        we need to route them to each publish method
        """

        #! should this return a NoobitResponse object ?

        route = await self.route_message(msg)

        if route not in WS_ROUTE:
            return # some error message

        logger.debug(f"msg handler routing to {route}")
        await self.route_to_method[route](ujson.loads(msg), redis_pool)



    async def route_message(self, msg):
        """route message to appropriate method to publish
        one of coros :
            - publish_heartbeat
            - publish_system_status
            - publish_subscription_status
            - publish_data

        To be implemented by ExchangeFeedReader
        """
        raise NotImplementedError



    async def publish_heartbeat(self, msg, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:private:heartbeat:{self.exchange}"

        try:
            # TODO replace with parser
            # msg = ujson.loads(msg)
            heartbeat = HeartBeat(**msg)
            await redis_pool.publish(channel, ujson.dumps(heartbeat.dict()))

        except ValidationError as e:
            logger.error(e)
        except Exception as e:
            log_exception(logger, e)



    async def publish_status_system(self, msg, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"ws:private:status:system:{self.exchange}"

        try:
            # TODO replace with parser
            # msg = ujson.loads(msg)
            msg["connection_id"] = msg.pop("connectionID")
            logger.info(msg)
            system_status = SystemStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(system_status.dict()))

        except ValidationError as e:
            logger.error(e)
        except Exception as e:
            log_exception(logger, e)



    async def publish_status_subscription(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:private:status:subscription:{self.exchange}"

        try:
            # msg = ujson.loads(msg)
            msg["channel_name"] = msg.pop("channelName")
            logger.info(msg)
            subscription_status = SubscriptionStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(subscription_status.dict()))

        except ValidationError as e:
            logger.error(e)
        except Exception as e:
            log_exception(logger, e)



    # ================================================================================



    async def publish_data_trade(self, msg, redis_pool):
        # public trades
        # ignore snapshot as it will only give us past 50 trades (useless)
        try:
            try:
                self.feed_counters["trade"] += 1
                parsed = self.stream_parser.trade(msg)
            except KeyError:
                self.feed_counters["trade"] = 0

            parsed = self.stream_parser.user_trade(msg)
            # should return dict that we validates vs Trade Model
            validated = TradesList(data=parsed)
            # then we want to return a response

            value = validated.data

            resp = OKResponse(
                status_code=200,
                value=value
            )

            # resp value is a list of pydantic Trade Models
            # we need to check symbol for each item of list and dispatch accordingly
            for item in resp.value:
                logger.info(item)
                update_chan = f"ws:private:data:trade:update:{self.exchange}:{item.symbol}"
                await redis_pool.publish(update_chan, ujson.dumps(item.dict()))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)



    async def publish_data_order(self, msg, redis_pool):
        try:
            #! we need to sort between snapshot / new order update / order status update
            #! like for orderbook we want to return a full image of current orders, not just a single status update for ex
            #! ==> ideally we want to publish to two redis channels, one with the full list of current orders, one with just the incoming updates
            try:
                self.feed_counters["order"] += 1

                # this should return a dict with 2 keys:
                # new_orders and status_changes each being a dict
                parsed = self.stream_parser.order_update(msg)
                # updating the dict will override the value if the key is already present
                self.all_orders.update(parsed["insert"])
                for order_id, info in parsed["update"].items():
                    # e.g info = {"status": "filled", "leavesQty": 0}
                    for key, value in info.items():
                        self.all_orders[order_id][key] = value

            # first message == it's a snapshot (!! this is true for kraken but we have not checked for other exchanges)
            except KeyError:
                self.feed_counters["order"] = 0
                parsed = self.stream_parser.order_snapshot(msg)
                self.all_orders.update(parsed)

            # should return dict that we validates vs order Model
            validated = OrdersByID(data=self.all_orders)
            # then we want to return a response

            value = validated.data

            resp = OKResponse(
                status_code=200,
                value=value
            )

            # resp value is a dict of pydantic Order Models
            # we need to check symbol for each item of dict and dispatch accordingly
            for key, value in resp.value.items():
                logger.info(value)
                update_chan = f"ws:private:data:order:update:{self.exchange}:{value.symbol}"
                await redis_pool.publish(update_chan, ujson.dumps(value.dict()))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)