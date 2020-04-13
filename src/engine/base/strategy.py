import random
import asyncio

import httpx
import ujson
import websockets


from structlogger import get_logger, log_exception
from exchanges.mappings import rest_api_map
from models.orm import Strategy

logger = get_logger(__name__)

WS_URI_MAP = {
    "kraken": "wss://ws-auth.kraken.com"
}


class StratBase():
    """
    Syntax should be similar to Tradingview
    How we would like to call it :

    mesa = Strategy("kraken", ["xbt-usd", "eth-usd"])

    data = mesa.ohlc ==> instance property that calls get_ohlc_as_pandas
                         + needs to already have long and short columns populated with 0s,
                         so we later just change the values to 1 using pandas masks for signals

                     ==> how do we make sure this updates continually ? do we just append new data ?
                             do we write all the historical ohlc for the strat to db ?

                     ==> MAYBE we should have different base classes for diff trading style
                            obviously this setup would not be useful for market making

    data["mama"], data["fama"] = talib.MAMA(data['hl2'], fastlimit=0.5, slowlimit=0.05)

    mesa.long = crossup(ohlc["mama], ohlc["fama]) => define crossup, mesa.long is property of type pd.Series
    OR
    data[long] = [...] ==> data is a pandas dataframe where we store all the data we need for the strategy

    The Strategy class is only meant to generate signals, not handle execution.
    Once we have signals, they are passed alond to self.execution.buy or self.execution.sell,
    where self.execution is an instance subclassing BaseExecution
    """

    def __init__(self, exchange: str, pair: list, timeframe: int, volume: int):
        self.exchange = exchange.lower()
        self.pair = pair
        self.timeframe = timeframe
        self.volume = volume

        self.api = rest_api_map[exchange]()
        self.api.session = httpx.AsyncClient()   # or settings.SESSION if not None

        self.df = None

        self.should_exit = False

        self._tick_coros = []
        self._tick_args = []
        self._crossups_to_calc = []
        self._crossdowns_to_calc = []
        self._crossovers_to_calc = []
        self._crossunders_to_calc = []

        self._long_conditions = []

        self.strat_id = random.getrandbits(32)
        self._name = self.__class__.__name__

        self._ws_uri = WS_URI_MAP[self.exchange]

        self.ws = None
        self.ws_token = None

        self.execution_models = {}



    # ================================================================================
    # ==== SETUP
    # ================================================================================


    async def subscribe_to_ws(self, ping_interval: int = 10, ping_timeout: int = 30):
        """Subscribe to websocket.
        """

        feeds = ["addOrder", "cancelOrder"]

        self.ws = await websockets.connect(uri=self._ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )

        self.ws_token = await self.api.get_websocket_auth_token()

        for feed in feeds:
            try:
                data = {"event": "subscribe", "subscription": {"name": feed, "token": self.ws_token['token']}}
                payload = ujson.dumps(data)
                await self.ws.send(payload)
                await asyncio.sleep(0.1)

            except Exception as e:
                log_exception(logger, e)

        for _key, model in self.execution_models.items():
            await self.setup_execution_ws(model)


    async def setup_execution_ws(self, execution_instance):
        execution_instance.ws = self.ws
        execution_instance.ws_token = self.ws_token


    async def close(self):
        """Close websocket connection
        """
        try:
            # await self.ws.wait_closed()
            await self.ws.close()
        except Exception as e:
            log_exception(logger, e)


    async def register_to_db(self):
        """register strategy into db
        check if strategy table contains our strategy
        if not, create it

        also bind strat runner ws to strat instance
        """
        check = await Strategy.filter(name=self._name).values()
        if not check:
            logger.info(f"Strategy : {self._name} --- Add to Db")
            await Strategy.create(id=self.strat_id,
                                  name=self._name,
                                  )
        else:
            logger.info(f"Strategy : {self._name} --- Already in DB")


    async def get_decimal_precision(self):
        """check price and volume decimal precision allowed by exchange api
        """
        pass



    # ================================================================================
    # ==== DATA
    # ================================================================================

    #!  This should actually be read from cache, feed processor/handler should already have calculated
    #!  some data points like price quote, available volume etc etc for use by strategy and execution modules

    #!  If OHLC is a problem maybe we can poll this one via rest api


    async def setup_df(self):
        self.df = await self.get_ohlc()


    async def update_df(self):
        self.df = await self.get_ohlc()


    async def get_ohlc(self):
        """get data from api
        ideally we would want to share the data cross different strategies
        ==> waste to poll for each, if they have the same pairs for ex
        ==> that was a stupid comment, we prob wont be running multiple strats on same exch/pair
        """
        ohlc = await self.api.get_ohlc_as_pandas(self.pair, self.timeframe)
        return ohlc["data"]

    # @property
    # def ohlc(self):
    #     """
    #     Returns:
    #         coroutine
    #     """
    #     ohlc_coro = self.api.get_ohlc_as_pandas(self.pair, self.timeframe)
    #     return ohlc_coro




    # ================================================================================
    # ==== INDICATOR
    # ================================================================================


    def add_indicator(self, *args, func, source, **kwargs):
        # self._tick_coros.append(self.calculate_indicator(talib_func, source, **kwargs))
        tick_args = {"func": func, "source": source, **kwargs}
        self._tick_args.append(tick_args)


    def calculate_indicator(self, func, source, **kwargs):
        """
        Args:
            talib_func: TA-Lib function
            source: column of self.ohlc we want to use as input
            args: args specific to TA-Lib function

        Notes:
        add signals into the instance data dataframe

        Example:
        self.add_signals(talib.MAMA, "close", fastlimit=0.5, slowlimit=0.05)
        """
        try:
            result = func(self.df[source], **kwargs)
        except Exception as e:
            log_exception(logger, e)
        i = 0
        func_name = str(func.__name__)
        try:
            if isinstance(result, tuple):
                for item in result:
                    col_name = f"{func_name}{i}"
                    self.df[col_name] = item
                    i += 1
            else:
                self.df[func_name] = result
        except Exception as e:
            log_exception(logger, e)



    # ================================================================================
    # ==== CROSS UP
    # ================================================================================


    def add_crossup(self, col1: str, col2: str):
        """
        add crossup of cols to df
        """
        self._crossups_to_calc.append((col1, col2))


    def calculate_crossups(self):
        for i in self._crossups_to_calc:
            self.df = self.crossup(col1=i[0], col2=i[1], df=self.df)


    def crossup(self, col1: str, col2: str, df):
        """
        when col1 crosses above col2
        """
        # df = await df_coro
        # we need all values on one row to use df masks
        df[f"previous_{col1}"] = df[col1].shift(1)
        df[f"previous_{col2}"] = df[col2].shift(1)

        df[f"CROSSUP_{col1}_{col2}"] = ((df[col1] > df[col2]) & (df[f"previous_{col1}"] < df[f"previous_{col2}"]))
        df = df.drop(columns=[f"previous_{col1}", f"previous_{col2}"], axis=1)
        return df




    # ================================================================================
    # ==== CROSS DOWN
    # ================================================================================


    def add_crossdown(self, col1: str, col2: str):
        """
        add crossup of cols to df
        """
        self._crossdowns_to_calc.append((col1, col2))


    def calculate_crossdowns(self):
        for i in self._crossdowns_to_calc:
            self.df = self.crossdown(col1=i[0], col2=i[1], df=self.df)


    def crossdown(self, col1: str, col2: str, df):
        """
        when col1 crosses under col2
        """
        # we need all values on one row to use df masks
        df[f"previous_{col1}"] = df[col1].shift(1)
        df[f"previous_{col2}"] = df[col2].shift(1)

        df[f"CROSSDOWN_{col1}_{col2}"] = ((df[col1] < df[col2]) & (df[f"previous_{col1}"] > df[f"previous_{col2}"]))
        df = df.drop(columns=[f"previous_{col1}", f"previous_{col2}"], axis=1)
        return df




    # ================================================================================
    # ==== CROSS OVER
    # ================================================================================


    def add_crossover(self, col: str, value: float):
        self._crossovers_to_calc.append((col, value))


    def calculate_crossovers(self):
        for i in self._crossovers_to_calc:
            self.df = self.crossover(col=i[0], value=i[1], df=self.df)


    def crossover(self, col: str, value: float, df):
        df[f"previous_{col}"] = df[col].shift(1)

        df[f"CROSSOVER_{col}_{value}"] = ((df[f"previous_{col}"] < value) & (df[col] > value))
        df = df.drop(columns=[f"previous_{col}"], axis=1)
        return df




    #================================================================================
    # ==== CROSS UNDER
    #================================================================================


    def add_crossunder(self, col: str, value: float):
        self._crossunders_to_calc.append((col, value))


    def calculate_crossunders(self):
        for i in self._crossunders_to_calc:
            self.df = self.crossunder(col=i[0], value=i[1], df=self.df)


    def crossunder(self, col: str, value: float, df):
        df[f"previous_{col}"] = df[col].shift(1)

        df[f"CROSSUNDER_{col}_{value}"] = ((df[f"previous_{col}"] > value) & (df[col] < value))
        df = df.drop(columns=[f"previous_{col}"], axis=1)
        return df




    # ================================================================================
    # ==== LONG
    # ================================================================================

    def long_condition(self):
        pass

    def short_condition(self):
        pass


    # def add_long_condition(self, condition: str):
    #     return
    #     condition = f"{condition}"
    #     # condition = re.sub(r'"(.*?)"', self.df[])

    #     # self._long_conditions.append(condition)


    # def calculate_long_condition(self):
    #     return
    #     for i in self._long_conditions:
    #         self.df = self.long(i[0])


    # def long(self, condition, df):
    #     pass




    # ================================================================================
    # ==== TICK
    # ================================================================================


    def user_tick(self):
        pass

    def user_setup(self):
        pass


    async def main_loop(self, tick_interval=1):
        self.user_setup()

        counter = 0
        should_exit = await self.on_tick(counter, tick_interval)
        while not should_exit:
            counter += 1

            # do we need to change 864000 to some other number ?
            counter = counter % 864000
            await asyncio.sleep(tick_interval)
            should_exit = await self.on_tick(counter, tick_interval)


    async def on_tick(self, counter, tick_interval) -> bool:

        # heartbeat once per second
        # self.heartbeat.beat()

        # Check indicators every minute
        if counter % (60/tick_interval) == 0:
            await self.update_df()
            # for coro in self._tick_coros:
            #     print(coro)
            #     await coro
            for func_args in self._tick_args:
                self.calculate_indicator(**func_args)
            self.calculate_crossups()
            self.calculate_crossdowns()
            self.calculate_crossovers()
            self.calculate_crossunders()

            self.long_condition()
            self.short_condition()

            self.user_tick()

            # print(self.df.iloc[-2])
            print(self.df[["close", "MAMA0", "MAMA1", "RSI", "CROSSUP_MAMA0_MAMA1", "long"]].tail(20))
        # Determine if we should exit.
        if self.should_exit:
            return True

        return False




    # ================================================================================
    # ==== BACKTESTER
    # ================================================================================


    async def backtest(self):
        """
        fetch all historical data as pandas, mask signals, pass to backtrader
        """
        pass