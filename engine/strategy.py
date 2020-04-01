import random
import asyncio
from typing import List
from abc import ABC, abstractmethod, abstractproperty
from functools import partial
import signal

import httpx
import talib
import ujson
import stackprinter

from server import settings
from exchanges.mappings import rest_api_map
from models.orm_models import Strategy

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

class BaseStrategy():
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

    def __init__(self, exchange: str, pair: str, timeframe: int, volume: int):
        self.exchange = exchange
        self.pair = pair
        self.timeframe = timeframe
        self.volume = volume

        self.api = rest_api_map[exchange]()
        if settings.SESSION:
            self.api.session = settings.SESSION
        else:
            self.api.session = httpx.AsyncClient()   # or settings.SESSION if not None

        self.df = None

        self.should_exit = False

        self._tick_coros = []
        self._tick_args = []
        self._id = random.getrandbits(32)
        self._name = self.__class__.__name__


    async def register(self):
        """register strategy into db
        check if strategy table contains our strategy
        if not, create it
        """
        check = await Strategy.filter(name=self._name).values()
        if not check:
            print(f"Strategy : {self._name} --- Add to Db")
            await Strategy.create(id=self._id,
                                  name=self._name,
                                  )
        else:
            print(f"Strategy : {self._name} --- Already in DB")

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
            print(stackprinter.format(e, style="darkbg2"))

        i=0
        func_name = str(func.__name__)
        try:
            if isinstance(result, tuple):
                for item in result:
                    col_name = f"{func_name}_{i}"
                    self.df[col_name] = item
                    i += 1
            else:
                self.df[func_name] = result
        except Exception as e:
            print(stackprinter.format(e, style="darkbg2"))


    @property
    def long(self):
        raise NotImplementedError

    @property
    def short(self):
        raise NotImplementedError



    async def crossup(self, col1: str, col2: str, df):
        """
        when col1 crosses above col2

        df refers to the coroutine that will fetch a pandas df with data
        for ex df = api.get_ohlc_as_pandas()
        """
        # df = await df_coro
        # we need all values on one row to use df masks
        df[f"previous_{col1}"] = df[col1].shift(1)
        df[f"previous_{col2}"] = df[col2].shift(1)

        df["crossup"] = ((df[col1] > df[col2]) & (df[f"previous_{col1}"] < df[f"previous_{col2}"]))
        return df


    async def crossdown(self, col1: str, col2: str, df_coro: asyncio.coroutine):
        """
        when col1 crosses under col2
        """
        df = await df_coro
        # we need all values on one row to use df masks
        df[f"previous_{col1}"] = df[col1].shift(1)
        df[f"previous_{col2}"] = df[col2].shift(1)

        df["crossdown"] = ((df[col1] < df[col2]) & (df[f"previous_{col1}"] > df[f"previous_{col2}"]))
        return df


    async def crossover(self):
        pass


    async def crossunder(self):
        pass


    async def main_loop(self, tick_interval=1):
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

            print(self.df.iloc[-2])

        # Determine if we should exit.
        if self.should_exit:
            return True

        return False
