import talib

from engine.base import BaseStrategy
from engine.exec.execution import LimitChaseExecution



class MockStrat(BaseStrategy):


    def __init__(self, exchange, pair, timeframe, volume):
        super().__init__(exchange, pair, timeframe, volume)
        #!  for now we only accept one execution
        self.execution_models = {
            "limit_chase": LimitChaseExecution(exchange, pair, self.ws, self.ws_token, self.strat_id, 0.1)
        }


    def user_setup(self):
        self.add_indicator(func=talib.MAMA, source="close", fastlimit=0.5, slowlimit=0.05)
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
            # self.execution.add_short_orde(total_vol=0.0234567)