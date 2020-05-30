import talib
# import inspect

from noobit.engine.base import BaseStrategy
from noobit.engine.exec.execution import LimitChaseExecution
from noobit.models.data.base.types import PAIR, TIMEFRAME

# in every strategy file we need to define a Strategy class for cli endpoint to work
class Strategy(BaseStrategy):


    def __init__(self,
                 exchange: str,
                 symbol: PAIR,
                 timeframe: TIMEFRAME,
                 volume: float = 0
                 ):

        # name = inspect.getfile(self)
        description = "describe your strategy"
        super().__init__(description, exchange, symbol, timeframe, volume)

        # for now we only accept one execution model
        # we can access the minimum tick for volume and price through api
        # how to we pass the name of the strategy to the execution model
        self.execution_models = {
            "limit_chase": LimitChaseExecution(exchange, symbol, self.ws, self.ws_token, self.api.exchange_pair_specs[symbol])
        }


    def user_setup(self):
        #! later we might want to add the possibility to choose different timeframes too
        self.add_indicator(func=talib.MAMA, source="close", fastlimit=0.1, slowlimit=0.05)
        self.add_indicator(func=talib.RSI, source="close", timeperiod=14)
        self.add_crossup("MAMA0", "MAMA1")
        self.add_crossdown("MAMA0", "MAMA1")


    def long_condition(self):
        self.df["long"] = (self.df["RSI"] < 70) & (self.df["CROSSUP_MAMA0_MAMA1"])


    def short_condition(self):
        self.df["short"] = (self.df["RSI"] > 30) & (self.df["CROSSDOWN_MAMA0_MAMA1"])


    def user_tick(self):
        last = self.df.iloc[-2]

        if last["long"]:
            print("We go long !")
            self.execution_models["limit_chase"].add_long_order(total_vol=0.0234567)

        if last["short"]:
            print("We go short !")