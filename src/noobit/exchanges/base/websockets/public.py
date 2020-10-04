from noobit.models.data.base.response import ErrorResponse, OKResponse
import websockets
import asyncio
from typing import List, Optional, Dict
from collections import Counter, deque

import ujson
from pydantic import ValidationError
from decimal import Decimal

from noobit.logger.structlogger import get_logger, log_exc_to_db, log_exception

# models
from noobit.models.data.base.types import PAIR, WS_ROUTE
from noobit.models.data.websockets.status import ConnectionStatus, SubscriptionStatus, HeartBeat

from noobit.models.data.websockets.stream import (
    TradesList, Instrument, OrderBook, Spread, Ohlc, OhlcItem
)
from noobit import runtime
from noobit.exchanges.mappings import rest_api_map # FIXME need to replace this with new api design
# from noobit.central_objects.app import App
# app = App()

logger = get_logger(__name__)


class PublicFeedReaderBase():


    # self.sub_parser = sthg_sthg

    def __init__(self, ws: websockets.WebSocketClientProtocol = None):

        self.ws = ws
        self.terminate = False

        self.subscribed_feeds = {
            "orderbook": set(),
            "instrument": set(),
            "trade": set(),
            "ohlc": set(),
            "spread": set()
        }

        self.feed_counters = {}

        # recreate full orderbook
        self.full_orderbook: Dict[PAIR, Dict[str, dict]] = {}

        # ohlc msg counter (we want to pass on the snapshot)
        self.ohlc_msg_counter = {}

        # recreate full ohlc
        self.full_ohlc: Dict[PAIR, Dict[str, Decimal]] = {}

        # create a deque to store only X last trades
        self.store = deque([], 500)

        self.route_to_method = {
            "heartbeat": self.publish_heartbeat,
            "connection_status": self.publish_status_connection,
            "subscription_status": self.publish_status_subscription,
            "instrument": self.publish_data_instrument,
            "trade": self.publish_data_trade,
            "orderbook": self.publish_data_orderbook,
            "spread": self.publish_data_spread,
            "ohlc": self.publish_data_ohlc
        }


    async def connect(self, ping_interval: int, ping_timeout: int):
        """connec to websocket"""
        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )


    async def subscribe(self, symbol: PAIR, feed: str, timeframe: Optional[int] = 60, depth: Optional[int] = 50):
        """subscribe to feed"""

        # if we already have a ws connection and we pass it along
        if not self.ws:
            raise ValueError("No valid Websocket Connection")   #! improve error handling

        try:
            if symbol in self.subscribed_feeds[feed]:
                msg = f"Can not sub: {symbol} is already subscribed"
                logger.info(msg)

            else:
                self.subscribed_feeds[feed].add(symbol)

                data = await self.subscription_parser.public(symbol, timeframe, depth, feed)
                payload = ujson.dumps(data)

                await self.ws.send(payload)
                await asyncio.sleep(0.1)

                # ==> BELOW BLOCK MOVED TO PUBLISH_STATUS_CONNECTION
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
                # runtime.Config.subscribed_feeds[self.exchange]["public"][feed].add(symbol)

                #! Should we return sthg in the form of OK(symbol=symbol, feed=feed)
                #! That way we will be able to easily inform API of success and failure

        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)


    async def unsubscribe(self, symbol: PAIR, feed: str, timeframe: Optional[int] = None, depth: Optional[int] = 50):
        """unsubscribe from feed"""

        # if we already have a ws connection and we pass it along
        if not self.ws:
            raise ValueError("No valid Websocket Connection")   #! improve error handling

        try:
            if feed not in self.subscribed_feeds:
                msg = f"Can not unsub: {symbol} is not subscribed"
                logger.info(msg)
            else:
                self.subscribed_feeds[feed].remove(symbol)
                data = await self.unsubscription_parser.public(symbol, timeframe, depth, feed)

                payload = ujson.dumps(data)
                await self.ws.send(payload)
                await asyncio.sleep(0.1)

                # MOVED TO PUBLISH_CONNECTION_STATUS
                # runtime.Config.subscribed_feeds[self.exchange]["public"][feed].remove(symbol)

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

        channel = f"ws:public:heartbeat:{self.exchange}"

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

        publish noobit <ConnectionStatus> model and update runtime.Config

        """

        channel = f"ws:public:status:system:{self.exchange}"

        try:
            parsed = self.stream_parser.connection_status(msg)
            # should return dict that we validates vs Trade Model
            validated = ConnectionStatus(**parsed, exchange=self.exchange)
            await redis_pool.publish(channel, ujson.dumps(validated.dict()))

        except ValidationError as e:
            logger.error(e.errors)
            await log_exc_to_db(logger, e)
        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)



    async def publish_status_subscription(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:public:status:subscription:{self.exchange}"

        try:
            parsed = self.stream_parser.subscription_status(msg)
            # should return dict that we validates vs Trade Model
            notification_msg = f"{parsed['status']} : {self.exchange}-{parsed['feed']}-{parsed['symbol']}"
            validated = SubscriptionStatus(**parsed, exchange=self.exchange, msg=notification_msg)
            await redis_pool.publish(channel, ujson.dumps(validated.dict()))
            logger.info(validated.dict())

            if validated.status == "subscribed":
                # register to config
                if not runtime.Config.subscribed_feeds.get(self.exchange, None):
                    runtime.Config.subscribed_feeds[self.exchange] = {
                        "public": {
                            "trade": set(),
                            "orderbook": set(),
                            "instrument": set(),
                            "spread": set(),
                            "ohlc": set(),
                            "subscription_status": set(),
                        },
                        "private": set()
                    }
                runtime.Config.subscribed_feeds[self.exchange]["public"][validated.feed].add(validated.symbol)

            elif validated.status == "unsubscribed":
                # remove from runtime.Config
                runtime.Config.subscribed_feeds[self.exchange]["public"][validated.feed].remove(validated.symbol)
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
        # no snapshots
        try:
            parsed = self.stream_parser.trade(msg)
            # should return dict that we validates vs Trade Model
            parsed = [{**msg, 'exchange':self.exchange} for msg in parsed]
            validated = TradesList(data=parsed)
            # then we want to return a response

            for trade in validated.data:
                snapshot_chan = f"ws:public:data:trade:snapshot:{trade.exchange}:{trade.symbol}"
                self.store.append(trade.dict())
                msg = {"channel": validated.channel, "data": self.store}
                await redis_pool.publish(snapshot_chan, ujson.dumps(msg))

            # value = validated.dict()

            # resp = OKResponse(
            #     status_code=200,
            #     value=value
            # )

            # # resp value is a list of pydantic Trade Models
            # # we need to check symbol for each item of list and dispatch accordingly
            # for item in resp.value:
            #     update_chan = f"ws:public:data:trade:update:{item.data.exchange}:{item.data.symbol}"
            #     snapshot_chan = f"ws:public:data:trade:snapshot:{item.data.exchange}:{item.data.symbol}"

            #     await redis_pool.publish(update_chan, ujson.dumps(item.dict()))

            #     # deque will automatically limit itself to 500 items
            #     self.store.append(item.data.dict())
            #     await redis_pool.publish(snapshot_chan, ujson.dumps(self.store))


        except ValidationError as e:
            logger.error(e.errors)
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
            # logger.info(resp.value)
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
            validated = OrderBook(**parsed, exchange=self.exchange)
            # then we want to return a response

            if validated.is_snapshot:
                self.full_orderbook[validated.symbol] = {}
                self.full_orderbook[validated.symbol]["asks"] = validated.asks
                self.full_orderbook[validated.symbol]["bids"] = validated.bids
            else:
                self.full_orderbook[validated.symbol]["asks"].update(validated.asks)
                self.full_orderbook[validated.symbol]["bids"].update(validated.bids)
                # will throw ValueError if other side is empty dict
                #! is incorrect since asks are calculated first will always only limit asks
                self.full_orderbook[validated.symbol]["asks"] = {k: v for k, v in self.full_orderbook[validated.symbol]["asks"].items() if v > 0 and k > max(list(self.full_orderbook[validated.symbol]["bids"].keys()))}
                self.full_orderbook[validated.symbol]["bids"] = {k: v for k, v in self.full_orderbook[validated.symbol]["bids"].items() if v > 0 and k < min(list(self.full_orderbook[validated.symbol]["asks"].keys()))}

            snapshot_chan = f"ws:public:data:orderbook:snapshot:{validated.exchange}:{validated.symbol}"
            update_chan = f"ws:public:data:orderbook:update:{validated.exchange}:{validated.symbol}"

            payload = OrderBook(
                exchange=validated.exchange,
                symbol=validated.symbol,
                asks=self.full_orderbook[validated.symbol]["asks"],
                bids=self.full_orderbook[validated.symbol]["bids"],
                is_snapshot=validated.is_snapshot,
                is_update=validated.is_update
            )

            resp = OKResponse(
                status_code=200,
                value=payload.dict()
            )

            # full snapshot of orderbook
            await redis_pool.publish(snapshot_chan, ujson.dumps(resp.value))

            # only updates of orderbook
            await redis_pool.publish(update_chan, ujson.dumps(resp.value))


        except ValidationError as e:
            #! always use ValidatonError.error to get more precise msg
            logger.error(e.errors)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)


    async def publish_data_ohlc(self, msg, redis_pool):
        print(msg)

        # FIXME this will only work for one feed (one snapshot)
        # self.ohlc_msg_counter += 1
        # if self.ohlc_msg_counter == 1:
        #     return
        api = rest_api_map[self.exchange]()
        # api = getattr(app.api.rest, self.exchange)()
        try:
            # msg contains data only for a single candle
            parsed = self.stream_parser.ohlc(msg)
            validated = OhlcItem(**parsed)

            if not self.ohlc_msg_counter.get(validated.symbol, None):
                self.ohlc_msg_counter[validated.symbol] = 1
            else:
                self.ohlc_msg_counter[validated.symbol] += 1

            if self.ohlc_msg_counter[validated.symbol] == 1:
                return

            if not self.full_ohlc.get(validated.symbol, None):
                print("Need to fetch REST")
                response = await api.get_ohlc(symbol=validated.symbol, timeframe=60)
                if response.is_ok:
                    # print("RESPONSE IS :", response.value[1])
                    self.full_ohlc[validated.symbol] = response.value
            else:
                # print("VALIDATED IS :", validated)
                print("Updating running candle from WS")
                self.full_ohlc[validated.symbol][-1] = validated.dict()

            # print("FULL ORDERBOOK IS :", self.full_ohlc[validated.symbol][1])

            for symbol, full_ohlc in self.full_ohlc.items():
                # print("FULL OHLC FOR SYMBOL", symbol, full_ohlc[-1])
                # FIXME for some reason this always throws a ValidationError
                # payload = Ohlc(data=full_ohlc, exchange=self.exchange)
                payload = {
                    "channel": "ohlc",
                    "exchange": self.exchange,
                    "data": full_ohlc
                }
                # logger.info(payload)
                resp = OKResponse(
                    status_code=200,
                    value=payload
                )

                snapshot_chan = f"ws:public:data:ohlc:snapshot:{self.exchange}:{symbol}"
                await redis_pool.publish(snapshot_chan, ujson.dumps(resp.value))

        except ValidationError as e:
            #! always use ValidatonError.error to get more precise msg
            logger.error(e.errors)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)



    async def publish_data_spread(self, msg, redis_pool):
        try:
            parsed = self.stream_parser.spread(msg)

            validated = Spread(**parsed)

            resp = OKResponse(
                status_code=200,
                value=validated
            )
            # logger.info(resp.value)
            update_chan = f"ws:public:data:spread:update:{self.exchange}:{resp.value.symbol}"
            await redis_pool.publish(update_chan, ujson.dumps(resp.value.dict()))


        except ValidationError as e:
            logger.error(e)
            return ErrorResponse(
                status_code=404,
                value=str(e)
            )
        except Exception as e:
            log_exception(logger, e)


