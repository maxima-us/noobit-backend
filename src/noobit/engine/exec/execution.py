from pydantic import ValidationError
import time
import asyncio

import aioredis
import ujson

from noobit.logging.structlogger import get_logger, log_exception
from noobit.models.data.websockets.deprecated_orders import AddOrder, CancelOrder

logger = get_logger(__name__)



class AsyncState():

    #! should we use a pydantic model for this too ? 
    #! ==> probably !!!

    def __init__(self, pair):
        self.current = {
            pair:{"side": None,
                  "volume": {"total": 0, "executed": 0},
                  "spread": {"best_bid": 0, "best_ask": 0},
                  "orders": {"open": {}}
                  }
        }

    def __aiter__(self):
        return self

    async def __anext__(self):
        return self.current


class LimitChaseExecution():
    """
    basic example of a limit chase execution
    """

    def __init__(self, exchange, pair, ws, ws_token, strat_id, pair_decimals, order_life: float = None, sub_map: dict = None):
        #! map exchange to exchange parsers
        #! for that we will need to map all parsers in exchanges.mappings / or in models.data
        self.exchange = exchange
        self.pair = pair[0].lower()
        self.aioredis_pool = None

        self.ws = ws
        self.ws_token = ws_token
        self.strat_id = strat_id

        # decimal precision allowed for given pair
        # see kraken doc : https://support.kraken.com/hc/en-us/articles/360001389366-Price-and-volume-decimal-precision
        #! we should get this at init of strat like for api
        self.pair_decimals = pair_decimals

        # how long an order should be allowed to stay alive before we cancel it
        # convert from seconds to nanoseconds (kraken timestamp is in nanoseconds)
        if order_life is None:
            self.order_life = 0.1 * 10**9
        else:
            self.order_life = order_life

        # self.state = {self.pair:{"side": None,
        #                          "volume": {"total": 0, "executed": 0},
        #                          "spread": {"best_bid": 0, "best_ask": 0},
        #                          "orders": {"open": {}}
        #                          }
        # }

        self.state = AsyncState(self.pair)

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
            self.sub_map = {"heartbeat": "ws:heartbeat:*",
                            "status": "ws:status:*",
                            "system": "ws:system:*",
                            "user_order_updates": f"ws:private:data:update:{self.exchange}:openOrders",
                            "user_trade_updates": f"ws:private:data:update:{self.exchange}:ownTrades",
                            "public_trade_updates": f"ws:public:data:update:{self.exchange}:trade:{self.pair}",
                            "public_ticker_updates": f"ws:public:data:update:{self.exchange}:ticker",
                            "public_spread_updates": f"ws:public:data:update:{self.exchange}:spread:{self.pair}",
                            }
        else:
            self.sub_map = sub_map




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
        self.state.current[self.pair] = {
            "side": side,
            "volume": {"total": total_vol, "executed": 0},
            "spread": {"best_bid": 0, "best_ask": 0},
            "orders": {"open": {}}
        }


    def add_long_order(self, total_vol):
        # be careful that decimal places is within tolerance of exchange API
        self.add_order(total_vol, side="buy")


    def add_short_order(self, total_vol):
        # be careful that decimal places is within tolerance of exchange API
        self.add_order(total_vol, side="sell")




    # ================================================================================
    # ==== TRADING VIA WEBSOCKET ACCORDING TO STATE
    # ================================================================================


    async def print_state(self):
        """
        Just a function to test that we are able to continuously read from state
        """
        pair = self.pair
        try:
            async for current_state in self.state:
                if self.should_exit:
                    break
                else:
                    state = current_state[pair]
                    logger.info(state["spread"])
                    # prevent blocking
                    await asyncio.sleep(0)
        except Exception as e:
            log_exception(logger, e)


    async def place_order(self, testing: bool=False):
        """
        place an order over the ws connection with exchange
        """
        pair = self.pair

        async for current_state in self.state:
            if self.should_exit:
                break

            info = current_state[pair]

            # no total volume = no orders passed => skip
            if info["volume"]["total"] == 0:
                # prevent blocking
                await asyncio.sleep(0)
                continue

            remaining_vol = info["volume"]["total"] - info["volume"]["executed"]
            if remaining_vol > 0:

                ask = info["spread"]["best_ask"]
                bid = info["spread"]["best_bid"]
                # we need to make sure to not cross the spread
                spread = abs(ask-bid)

                if info["side"] == "buy":
                    side = "buy"
                    # max price precision for kraken btcusd is 0.1 usd
                    if spread > self.pair_decimals:
                        price = bid + self.pair_decimals
                    else:
                        price = bid
                    leverage = None

                else:
                    side = "sell"
                    # max price precision for kraken btcusd is 0.1 usd
                    if spread > self.pair_decimals:
                        price = ask - self.pair_decimals
                    else:
                        price = ask
                    leverage = 4


                #! noobit format => then call exchange parser
                try:
                    data = {
                        "event": "addOrder",
                        "token": self.ws_token["token"],     # we need to get this from strat instance that Exec is binded to
                        "userref": self.strat_id,    # we need to get this from strat instance that Exec is binded to
                        "ordertype": "limit",
                        "type": side,
                        "pair": pair.replace("-", "/").upper(),
                        "volume": remaining_vol,
                    }



                    #! will have to use the exchange parser somehow
                    #! validate against standard Order model
                    try:
                        validated = AddOrder(**data)
                        validated_data = validated.dict()
                    except ValidationError as e:
                        log_exception(logger, e)
                    except Exception as e:
                        log_exception(logger, e)

                    #! pass parsed data instead
                    payload = ujson.dumps(validated_data)
                    await self.ws.send(payload)

                except Exception as e:
                    log_exception(logger, e)

                await asyncio.sleep(0)


            if testing:
                break


    async def cancel_order(self):
        """
        cancel all orders that are older than a treshold
        compare current time with posted timestamp
        """
        # kraken returns timestamp in nanoseconds
        current_ts = time.time_ns()
        pair = self.pair

        async for current_state in self.state:
            if self.should_exit:
                break

            info = current_state[pair]

            if not info["orders"]["open"]:
                await asyncio.sleep(0)
                continue

            for order_id, timestamp in info["orders"]["open"]:
                if current_ts - timestamp > self.order_life:

                    data = {
                        "event": "cancelOrder",
                        "token": self.ws_token,
                        "txid": order_id
                    }


                    try:
                        validated = CancelOrder(**data)
                        validated_data = validated.dict()
                    except ValidationError as e:
                        log_exception(logger, e)
                    except Exception as e:
                        log_exception(logger, e)

                    payload = ujson.dumps(validated_data)
                    self.ws.send(payload)
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
            json = msg.decode("utf-8")
            new_order = ujson.loads(json)
            logger.info(new_order)

            for order_id, order_info in new_order.items():
                status = order_info["status"]
                open_time = order_info["opentm"]
                pair = order_info["descr"]["pair"]
                pair = pair.replace("/", "-").lower()
                self.state.current[pair]["orders"][status][order_id] = open_time


    async def on_trade_update(self):

        channel = self.subscribed_channels["user_trade_updates"]

        async for _chan, msg in channel.iter():
            json = msg.decode("utf-8")
            new_trade = ujson.loads(json)
            logger.info(new_trade)

            for _order_id, trade_info in new_trade.items():
                pair = trade_info["pair"]
                pair = pair.replace("/", "-").lower()
                executed_volume = trade_info["vol"]
                side = trade_info["side"]

                self.state.current[pair]["volume"]["executed"] += executed_volume


    async def on_spread_update(self):

        channel = self.subscribed_channels["public_spread_updates"]

        async for _chan, msg in channel.iter():
            json = msg.decode("utf-8")
            new_spread = ujson.loads(json)

            bid = new_spread[0]
            ask = new_spread[1]
            timestamp = new_spread[2]

            pair = self.pair    #! get pair also from redis feed as confirmation ?

            self.state.current[pair]["spread"]["best_ask"] = ask
            self.state.current[pair]["spread"]["best_bid"] = bid

            logger.info(self.state.current)
