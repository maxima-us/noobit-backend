from pydantic import ValidationError
import time
import asyncio

import aioredis
import ujson

from noobit.logger.structlogger import get_logger, log_exception
from noobit.engine.exec.base import AsyncState
from noobit.models.data.request import AddOrder, CancelOrder
from noobit.models.data.websockets.stream.parse.kraken import KrakenStreamParser
# from noobit.models.data.request.parse.kraken import KrakenRequestParser

logger = get_logger(__name__)



class ExecutionModel():
    """
    basic example of a limit chase execution
    """

    def __init__(self, exchange, symbol, ws, ws_token, exchange_pair_specs, order_life: float = None, sub_map: dict = None):
        # TODO map exchange to exchange parsers ( in exchanges.mappings ?)

        self.exchange = exchange
        self.symbol = symbol
        self.aioredis_pool = None

        self.ws = ws
        self.ws_token = ws_token
        # self.strat_id = strat_id

        # decimal precision allowed for given pair
        # see kraken doc : https://support.kraken.com/hc/en-us/articles/360001389366-Price-and-volume-decimal-precision
        self.price_decimals = exchange_pair_specs["price_decimals"]
        self.volume_decimals = exchange_pair_specs["volume_decimals"]
        self.leverage_available = exchange_pair_specs["leverage_available"]

        # how long an order should be allowed to stay alive before we cancel it
        # convert from seconds to nanoseconds (kraken timestamp is in nanoseconds)
        # 0.1 = it will stay alive for 0.1 secs max before we cancel and replaceit
        if order_life is None:
            self.order_life = 0.1 * 10**9
        else:
            self.order_life = order_life

        self.state = AsyncState(self.symbol)

        # we use state as the link between all websockets
        # should contain info about all the orders we want to get filled, and update them constantly
        # ex : state = {"XBT-USD": {"side":"buy",
        #                           "vol":{"total":1, "executed":0.5},
        #                           "spread":{"best_bid":6788.9, "best_ask":6790},
        #                           "orders":{"open":{"txid": timestamp, "txid": timestamp}
        #                                    }
        #               }
        # TODO      for now this is OK, but later we might want to be able to have several orders
        # TODO          for the same pair simultaneously ==> maybe index by some sort of ID instead or pair

        self.should_exit = False

        # redis
        self.redis_tasks = []
        self.subscribed_channels = {}

        if sub_map is None:
            self.sub_map = {
                "heartbeat": "ws:heartbeat:*",
                "status": "ws:status:*",
                "system": "ws:system:*",
                "user_order_updates": f"ws:private:data:update:{self.exchange}:openOrders",
                "user_trade_updates": f"ws:private:data:update:{self.exchange}:ownTrades",
                "public_trade_updates": f"ws:public:data:update:{self.exchange}:trade:{self.symbol}",
                "public_ticker_updates": f"ws:public:data:update:{self.exchange}:ticker",
                "public_spread_updates": f"ws:public:data:update:{self.exchange}:spread:{self.symbol}",
            }
        else:
            self.sub_map = sub_map

        self.streamparser = KrakenStreamParser()




    # ================================================================================
    # ==== SETUP
    # ================================================================================


    async def setup(self):
        await self.setup_redis_pool()
        await self.sub_redis_channels()


    async def setup_redis_pool(self):
        self.aioredis_pool = await aioredis.create_redis_pool('redis://localhost')


    async def sub_redis_channels(self):
        for key, channel_name in self.sub_map.items():
            subd_chan = await self.aioredis_pool.psubscribe(channel_name)
            # subscription always returns a list
            self.subscribed_channels[key] = subd_chan[0]

        self.redis_tasks.append(self.on_order_update())
        self.redis_tasks.append(self.on_trade_update())
        self.redis_tasks.append(self.on_spread_update())
        # self.redis_tasks.append(self.print_state())
        self.redis_tasks.append(self.place_order())
        self.redis_tasks.append(self.cancel_order())




    # ================================================================================
    # ==== ADD ORDERS TO STATE
    # ================================================================================


    def add_order(self, total_vol, side):
        """
        submit an order to the execution engine
        order info gets added to execution state
        """
        self.state.current[self.symbol] = {
            "side": side,
            "volume": {"orderQty": total_vol, "cumQty": 0, "leavesQty": 0},
            "spread": {"best_bid": 0, "best_ask": 0},
            "orders": {"open": {}},
        }


    def add_long_order(self, total_vol):
        # be careful that decimal places is within tolerance of exchange API
        try:
            orderQty = round(total_vol, self.volume_decimals)
        except Exception as e:
            log_exception(logger, e)
        self.add_order(orderQty, side="buy")


    def add_short_order(self, total_vol):
        # be careful that decimal places is within tolerance of exchange API
        try:
            orderQty = round(total_vol, self.volume_decimals)
        except Exception as e:
            log_exception(logger, e)
        self.add_order(orderQty, side="sell")




    # ================================================================================
    # ==== TRADING VIA WEBSOCKET ACCORDING TO STATE
    # ================================================================================


    async def print_state(self):
        """
        Just a function to test that we are able to continuously read from state
        """
        try:
            async for current_state in self.state:
                if self.should_exit:
                    break
                else:
                    state = current_state[self.symbol]
                    logger.info(state["spread"])
                    # prevent blocking
                    await asyncio.sleep(0)
        except Exception as e:
            log_exception(logger, e)



    async def place_order(self, testing: bool = False):
        """
        place an order over the ws connection with exchange
        """

        # continuously watch over state
        async for current_state in self.state:
            if self.should_exit:
                break

            info = current_state[self.symbol]

            # no total volume = no orders passed => skip
            if info["volume"]["orderQty"] == 0:
                # prevent blocking
                await asyncio.sleep(0)
                continue

            remaining_vol = info["volume"]["leavesQty"]
            if remaining_vol > 0:

                ask = info["spread"]["best_ask"]
                bid = info["spread"]["best_bid"]
                # we need to make sure to not cross the spread
                spread = abs(ask-bid)

                if info["side"] == "buy":
                    side = "buy"
                    # max price precision for kraken btcusd is 0.1 usd
                    if spread > self.price_decimals: #! get pair max decimals from api
                        price = bid + self.price_decimals
                    else:
                        price = bid
                    leverage = None

                else:
                    side = "sell"
                    # max price precision for kraken btcusd is 0.1 usd
                    if spread > self.price_decimals:
                        price = ask - self.price_decimals
                    else:
                        price = ask
                    leverage = 4

                try:

                    data = {
                        "symbol": self.symbol,
                        "side": side,
                        "ordType": "limit",
                        "execInst": None,
                        "clOrdID": None,
                        "timeInForce": None,
                        "effectiveTime": None,
                        "expireTime": None,
                        "orderQty": remaining_vol,
                        "orderPercent": None,
                        "marginRatio": 1/leverage,
                        "price": price,
                        "stopPx": None,
                        "targetStrategy": None,
                        "targetStrategyParameters": None
                    }

                    try:
                        validated_data = AddOrder(**data)
                    except ValidationError as e:
                        log_exception(logger, e)
                    except Exception as e:
                        log_exception(logger, e)

                    payload = self.streamparser.add_order(validated_data, self.ws_token["token"])
                    await self.ws.send(ujson.dumps(payload))

                except Exception as e:
                    log_exception(logger, e)

                # this is needed to not block the thread entirely
                await asyncio.sleep(0)

            # when testing we only want to place the trade once without updating it
            if testing:
                break


    async def cancel_order(self):
        """
        cancel all orders that are older than a treshold
        compare current time with posted timestamp
        """
        # kraken returns timestamp in nanoseconds
        current_ts = time.time_ns()

        async for current_state in self.state:
            if self.should_exit:
                break

            info = current_state[self.symbol]

            if not info["orders"]["open"]:
                await asyncio.sleep(0)
                continue

            for order_id, timestamp in info["orders"]["open"]:
                if current_ts - timestamp > self.order_life:

                    data = {
                        "clOrdID": None,
                        "orderID": [order_id]
                    }

                    try:
                        validated_data = CancelOrder(**data)
                    except ValidationError as e:
                        log_exception(logger, e)
                    except Exception as e:
                        log_exception(logger, e)

                    payload = self.streamparser.cancel_order(validated_data, self.ws_token["token"])

                    self.ws.send(ujson.dumps(payload))

            await asyncio.sleep(0)




    # ================================================================================
    # ==== CONSUME WS DATA AND CONTINUOUSLY UPDATE STATE
    # ================================================================================


    async def on_order_update(self):
        """
        how to we retrieve subd channels ??
        """
        channel = self.subscribed_channels["user_order_updates"]

        async for _chan, msg in channel.iter():
            if self.should_exit:
                break

            json = msg.decode("utf-8")
            new_order = ujson.loads(json)
            logger.info(new_order)


            for order_id, order_info in new_order.items():
                status = order_info["ordStatus"]
                open_time = order_info["effectiveTime"]
                symbol = order_info["symbol"]
                self.state.current[symbol]["orders"][status][order_id] = open_time


    async def on_trade_update(self):

        channel = self.subscribed_channels["user_trade_updates"]

        async for _chan, msg in channel.iter():
            if self.should_exit:
                break

            json = msg.decode("utf-8")
            new_trades = ujson.loads(json)
            logger.info(new_trades)

            for trade in new_trades:
                symbol = trade["symbol"]
                executed_volume = trade["cumQty"]
                side = trade["side"]

                if side == self.state.current[symbol]["side"]:
                    self.state.current[symbol]["volume"]["cumQty"] += executed_volume


    async def on_spread_update(self):

        channel = self.subscribed_channels["public_spread_updates"]

        async for _chan, msg in channel.iter():
            if self.should_exit:
                break

            json = msg.decode("utf-8")
            new_spread = ujson.loads(json)

            logger.info(new_spread)

            self.state.current[new_spread["symbol"]]["spread"]["best_ask"] = new_spread["bestAsk"]
            self.state.current[new_spread["symbol"]]["spread"]["best_bid"] = new_spread["bestBid"]

            logger.info(self.state.current)
