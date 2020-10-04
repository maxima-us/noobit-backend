import websockets
import asyncio
from typing import List, Optional

import ujson
from pydantic import ValidationError

from noobit.logger.structlogger import get_logger, log_exception, log_exc_to_db

# models
from noobit.models.data.base.response import ErrorResponse, OKResponse
from noobit.models.data.base.types import PAIR, WS_ROUTE
from noobit.models.data.websockets.status import HeartBeat, SubscriptionStatus, ConnectionStatus
from noobit.models.data.websockets.stream.trade import TradesList
from noobit.models.data.response.order import OrdersByID

# runtime config
from noobit import runtime

# from noobit.central_objects.app import App
# app = App()
# FIXME!!!
#! this will create circular import error: app will first try to instantiate this, but this refers to app at import
#! ===> solution: pass the app as an argument in __init__ and have a self.app argument


logger = get_logger(__name__)


class PrivateFeedReaderBase():


    # self.sub_parser = sthg_sthg

    def __init__(self, ws: websockets.WebSocketClientProtocol = None):

        self.ws = ws
        self.terminate = False

        # private feeds are "global" i.e not specific to a symbol
        self.subscribed_feeds = set()

        # we need to append order updates to order snapshot
        self.all_orders = {}
        self.feed_counters = {}

        self.route_to_method = {
            "heartbeat": self.publish_heartbeat,
            "connection_status": self.publish_status_connection,
            "subscription_status": self.publish_status_subscription,
            "trade": self.publish_data_trade,
            "order": self.publish_data_order,
        }

    async def connect(self, ping_interval: int, ping_timeout: int):
        """connect to websocket"""
        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )


    async def subscribe(self, feed: str):
        """subscribe to feed"""

        if not self.ws:
            raise ValueError("No valid Websocket Connection")

        try:
            if feed in self.subscribed_feeds:
                msg = f"Can not sub: {feed} is already subscribed"
                logger.info(msg)

            else:
                self.subscribed_feeds.add(feed)

                data = await self.subscription_parser.private(feed)
                payload = ujson.dumps(data)

                await self.ws.send(payload)
                await asyncio.sleep(0.1)

                # # register to config
                # if not runtime.Config.subscribed_feeds.get(self.exchange, None):
                #     runtime.Config.subscribed_feeds[self.exchange] = {
                #         "public": {
                #             "trade": set(),
                #             "orderbook": set(),
                #             "instrument": set(),
                #             "spread": set(),
                #             "subscription_status": set(),
                #         },
                #         "private": set()
                #     }
                # # update the set = same as push to list
                # runtime.Config.subscribed_feeds[self.exchange]["private"].add(feed)

                #! Should we return sthg in the form of OK(symbol=symbol, feed=feed)
                #! That way we will be able to easily inform API of success and failure

        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



    async def unsubscribe(self, feed: str):
        """unsubscribe from feed"""

        # if we already have a ws connection and we pass it along
        if not self.ws:
            raise ValueError("No valid Websocket Connection")   #! improve error handling

        try:
            if feed not in self.subscribed_feeds:
                msg = f"Can not unsub: {feed} is not subscribed"
                logger.info(msg)

            else:
                self.subscribed_feeds.remove(feed)
            data = await self.unsubscription_parser.private(feed)

            payload = ujson.dumps(data)
            await self.ws.send(payload)
            await asyncio.sleep(0.1)

            # runtime.Config.subscribed_feeds[self.exchange]["private"].remove(feed)

        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)


    async def close(self):
        try:
            # await self.ws.wait_closed()
            await self.ws.close()
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)


    async def msg_handler(self, msg, redis_pool):
        """feedhandler will async iterate over message
        we need to route them to each publish method
        """

        #! should this return a NoobitResponse object ?

        route = await self.route_message(msg)

        if route not in WS_ROUTE:
            return # some error message

        logger.debug(f"msg handler routing to {route}")
        try:
            await self.route_to_method[route](ujson.loads(msg), redis_pool)
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)




    # ================================================================================


    async def publish_heartbeat(self, msg, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:private:heartbeat:{self.exchange}"

        try:
            # TODO replace with parser
            # msg = ujson.loads(msg)
            heartbeat = HeartBeat(exchange=self.exchange)
            # await redis_pool.publish(channel, ujson.dumps(heartbeat.dict()))

        except ValidationError as e:
            logger.error(e)
            await log_exc_to_db(logger, e)
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



    async def publish_status_connection(self, msg, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"ws:private:status:system:{self.exchange}"

        try:
            parsed = self.stream_parser.connection_status(msg)
            # should return dict that we validates vs Trade Model
            validated = ConnectionStatus(**parsed, exchange=self.exchange)
            await redis_pool.publish(channel, ujson.dumps(validated.dict()))

        except ValidationError as e:
            logger.error(e)
            await log_exc_to_db(logger, e)
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



    async def publish_status_subscription(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:private:status:subscription:{self.exchange}"

        try:
            parsed = self.stream_parser.subscription_status(msg)
            # should return dict that we validates vs Trade Model
            validated = SubscriptionStatus(**parsed, exchange=self.exchange)
            await redis_pool.publish(channel, ujson.dumps(validated.dict()))

            if validated.status == "subscribed":
                # register to config
                if not runtime.Config.subscribed_feeds.get(self.exchange, None):
                    runtime.Config.subscribed_feeds[self.exchange] = {
                        "public": {
                            "trade": set(),
                            "orderbook": set(),
                            "instrument": set(),
                            "spread": set(),
                            "subscription_status": set(),
                        },
                        "private": set()
                    }
                runtime.Config.subscribed_feeds[self.exchange]["private"][validated.feed].add(validated.symbol)

            elif validated.status == "unsubscribed":
                # remove from runtime.Config
                runtime.Config.subscribed_feeds[self.exchange]["private"][validated.feed].remove(validated.symbol)
            else:
                # its an error and we add it to the list of errors encountered
                # append to error deque in runtime.Config
                pass

        except ValidationError as e:
            logger.error(e)
            await log_exc_to_db(logger, e)
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



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
            await log_exc_to_db(logger, e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



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
            await log_exc_to_db(logger, e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)