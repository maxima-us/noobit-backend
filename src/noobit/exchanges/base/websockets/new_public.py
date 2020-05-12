from abc import ABC, abstractmethod
from noobit.models.data.base.response import ErrorResponse, OKResponse
import websockets
import logging
import asyncio
from typing import List
from collections import Counter

import ujson
import stackprinter
from pydantic import ValidationError

# from noobit.models.data.websockets.subscribe.parse
from noobit.models.data.base.types import PAIR, WS_ROUTE

from noobit.logging.structlogger import get_logger, log_exception
from noobit.models.data.receive.websockets import (HeartBeat, SubscriptionStatus, SystemStatus,
                                                   Ticker, Trade, Spread, Book)

from noobit.models.data.websockets.stream.trade import TradesList
from noobit.models.data.websockets.stream.instrument import Instrument
from noobit.models.data.websockets.stream.orderbook import OrderBook

logger = get_logger(__name__)

DATA_MODELS_MAP = {"ticker": Ticker,
                   "trade": Trade,
                   "spread": Spread,
                   "book": Book
                   }

#! FOR NOW this doesnt publish to redis yet, we are just seeing how things work with logging
class BasePublicFeedReader():


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

                data = self.subscription_parser.parse(self.pairs, self.timeframe, self.depth, feed)


                payload = ujson.dumps(data)
                await self.ws.send(payload)
                await asyncio.sleep(0.1)

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))


    async def close(self):
        try:
            # await self.ws.wait_closed()
            await self.ws.close()
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))



    async def msg_handler(self, msg, redis_pool):
        """feedhandler will async iterate over message
        we need to route them to each publish method
        """

        #! should this return a NoobitResponse object ?

        route = await self.route_message(msg)

        if route not in WS_ROUTE:
            return # some error message

        logger.info(f"routing to {route}")
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

        channel = f"ws:public:heartbeat:{self.exchange}"

        try:
            # TODO replace with parser
            # msg = ujson.loads(msg)
            heartbeat = HeartBeat(**msg)
            await redis_pool.publish(channel, ujson.dumps(heartbeat.dict()))

        except ValidationError as e:
            logger.error(e)



    async def publish_status_system(self, msg, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"ws:public:system:{self.exchange}"

        try:
            # TODO replace with parser
            # msg = ujson.loads(msg)
            msg["connection_id"] = msg.pop("connectionID")
            logger.info(msg)
            system_status = SystemStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(system_status.dict()))

        except ValidationError as e:
            logger.error(e)



    async def publish_status_subscription(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:public:status:{self.exchange}"

        try:
            # msg = ujson.loads(msg)
            msg["channel_name"] = msg.pop("channelName")
            logger.info(msg)
            subscription_status = SubscriptionStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(subscription_status.dict()))

        except ValidationError as e:
            logger.error(e)



    async def publish_data_trade(self, msg, redis_pool):
        try:
            parsed = self.stream_parser.trade(msg)
            # should return dict that we validates vs Trade Model
            validated = TradesList(data=parsed)
            # then we want to return a response

            value = validated.data

            resp = OKResponse(
                status_code=200,
                value=value
            )

            logger.info(resp)

        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )



    async def publish_data_instrument(self, msg, redis_pool):
        try:
            parsed = self.stream_parser.instrument(msg)
            # should return dict that we validates vs Trade Model
            validated = Instrument(**parsed)
            # then we want to return a response

            value = validated.dict()

            resp = OKResponse(
                status_code=200,
                value=value
            )

            logger.info(resp)

        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )



    #! we still need to aggregate updates to snapshot
    async def publish_data_orderbook(self, msg, redis_pool):
        try:
            parsed = self.stream_parser.orderbook(msg)
            # should return dict that we validates vs Trade Model
            validated = OrderBook(**parsed)
            # then we want to return a response

            if validated.is_snapshot:
                self.full_orderbook["asks"] = Counter(validated.asks)
                self.full_orderbook["bids"] = Counter(validated.bids)
            else:
                self.full_orderbook["asks"] += Counter(validated.asks)
                self.full_orderbook["bids"] += Counter(validated.bids)


            resp = OKResponse(
                status_code=200,
                value=self.full_orderbook
            )

            logger.info(resp)

        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )



    async def publish_data_spread(self, msg, redis_pool):
        pass




    async def publish_data(self, msg, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        # TODO replace with parser
        try:
            msg = ujson.loads(msg)
            feed_id = msg[0]
            feed = msg[2]
            data = msg[1]
            pair = msg[3].replace("/", "-")
            channel = f"ws:public:data:{self.exchange}:{feed}"
            ws_data = DATA_MODELS_MAP[feed](channel_id=feed_id, data=data, channel_name=feed, pair=pair)
        except ValidationError as e:
            log_exception(logger, e)

        try:
            self.feed_counters[channel] += 1
            update_chan = f"ws:public:data:update:{self.exchange}:{feed}:{pair}"
            data_to_publish = ws_data.dict()
            data_to_publish = data_to_publish["data"]
            logger.info(f"data : {data_to_publish}")
            await redis_pool.publish(update_chan, ujson.dumps(data_to_publish))
        except KeyError:
            self.feed_counters[channel] = 0
            snapshot_chan = f"ws:public:data:snapshot:{self.exchange}:{feed}:{pair}"
            data_to_publish = ws_data.dict()
            data_to_publish = data_to_publish["data"]
            await redis_pool.publish(snapshot_chan, ujson.dumps(data_to_publish))
        except Exception as e:
            log_exception(logger, e)
        # try:
        #     #!  how to we know which model we need to load ? should we use a mapping again ?
        #     #!  we could try to look up <feed> key in a model mapping defined in data_models.websockets ?
        #     ws_data = data_models_map[feed](data=data, channel_name=feed)
        #     redis_pool.publish(channel, ujson.dumps(ws_data.dict()))

        # except ValidationError as e:
        #     logging.error(stackprinter.format(e, style="darkbg2"))
