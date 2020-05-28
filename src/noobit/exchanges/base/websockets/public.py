from noobit.models.data.base.response import ErrorResponse, OKResponse
import websockets
import asyncio
from typing import List
from collections import Counter

import ujson
from pydantic import ValidationError

from noobit.logging.structlogger import get_logger, log_exception

# models
from noobit.models.data.base.types import PAIR, WS_ROUTE
from noobit.models.data.websockets.status import HeartBeat, SubscriptionStatus, SystemStatus
from noobit.models.data.websockets.stream.trade import TradesList
from noobit.models.data.websockets.stream.instrument import Instrument
from noobit.models.data.websockets.stream.orderbook import OrderBook

logger = get_logger(__name__)


class PublicFeedReaderBase():


    # self.sub_parser = sthg_sthg

    def __init__(self,
                 pairs: List[PAIR],
                 timeframe: int = 1,
                 depth: int = 10,
                 feeds: List[str] = ["instrument", "trade", "orderbook"]
                 ):
        self.pairs = pairs
        self.feeds = feeds
        self.timeframe = timeframe
        self.depth = depth

        self.ws = None
        self.terminate = False

        # we need to append book updates to book snapshot
        self.full_orderbook = {"asks": Counter(), "bids": Counter()}
        self.feed_counters = {}

        self.route_to_method = {
            "heartbeat": self.publish_heartbeat,
            "system_status": self.publish_status_system,
            "subscription_status": self.publish_status_subscription,
            "instrument": self.publish_data_instrument,
            "trade": self.publish_data_trade,
            "orderbook": self.publish_data_orderbook,
            "spread": self.publish_data_spread
        }



    async def subscribe(self, ping_interval: int, ping_timeout: int):

        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )

        for feed in self.feeds:
            try:

                data = await self.subscription_parser.public(self.pairs, self.timeframe, self.depth, feed)


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



    async def publish_heartbeat(self, msg, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:public:heartbeat:{self.exchange}"

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

        channel = f"ws:public:status:system:{self.exchange}"

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

        channel = f"ws:public:status:subscription:{self.exchange}"

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
        # no snapshots
        try:
            parsed = self.stream_parser.trade(msg)
            # should return dict that we validates vs Trade Model
            validated = TradesList(data=parsed, last=None)
            # then we want to return a response

            value = validated.data

            resp = OKResponse(
                status_code=200,
                value=value
            )

            # resp value is a list of pydantic Trade Models
            # we need to check symbol for each item of list and dispatch accordingly
            for item in resp.value:
                # logger.info(ujson.dumps(item.dict()))
                update_chan = f"ws:public:data:trade:update:{self.exchange}:{item.symbol}"
                await redis_pool.publish(update_chan, ujson.dumps(item.dict()))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)



    async def publish_data_instrument(self, msg, redis_pool):
        # no snapshots
        try:
            parsed = self.stream_parser.instrument(msg)
            # should return dict that we validates vs Trade Model
            validated = Instrument(**parsed)
            # then we want to return a response

            resp = OKResponse(
                status_code=200,
                value=validated
            )
            logger.info(resp.value)
            update_chan = f"ws:public:data:instrument:update:{self.exchange}:{resp.value.symbol}"
            await redis_pool.publish(update_chan, ujson.dumps(resp.value.dict()))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)



    #! use a message counter to determine snapshot instead of conditional for each message
    async def publish_data_orderbook(self, msg, redis_pool):
        try:
            # with current logic parser needs to return a dict
            # that has bool values for keys is_snapshot and is_update
            parsed = self.stream_parser.orderbook(msg)
            # should return dict that we validates vs Trade Model
            validated = OrderBook(**parsed)
            # then we want to return a response

            if validated.is_snapshot:
                self.full_orderbook["asks"] = Counter(validated.asks)
                self.full_orderbook["bids"] = Counter(validated.bids)
                update_chan = f"ws:public:data:orderbook:snapshot:{self.exchange}:{validated.symbol}"
            else:
                self.full_orderbook["asks"] += Counter(validated.asks)
                self.full_orderbook["bids"] += Counter(validated.bids)
                update_chan = f"ws:public:data:orderbook:update:{self.exchange}:{validated.symbol}"


            resp = OKResponse(
                status_code=200,
                value=self.full_orderbook
            )

            await redis_pool.publish(update_chan, ujson.dumps(resp.value))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)



    async def publish_data_spread(self, msg, redis_pool):
        pass
