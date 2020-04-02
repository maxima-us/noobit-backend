import talib

from engine.strategy import BaseStrategy



class TestStrat(BaseStrategy):


    def __init__(self, exchange, pair, timeframe, volume):
        super().__init__(exchange, pair, timeframe, volume)


    def long_condition(self):
        self.df["long"] = (self.df["RSI"] < 70) & (self.df["CROSSUP_MAMA0_MAMA1"])


    def short_condition(self):
        self.df["short"] = (self.df["RSI"] > 30) & (self.df["CROSSDOWN_MAMA0_MAMA1"])


    def user_setup(self):
        self.add_indicator(func=talib.MAMA, source="close", fastlimit=0.5, slowlimit=0.05)
        self.add_indicator(func=talib.RSI, source="close", timeperiod=14)
        self.add_crossup("MAMA0", "MAMA1")
        self.add_crossdown("MAMA0", "MAMA1")

    def user_tick(self):
        last = self.df.iloc[-2]

        if last["long"]:
            print("We go long !")

        if last["short"]:
            print("We go short !")