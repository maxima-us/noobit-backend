from noobit.engine.base import BaseStrategy


class Strategy(BaseStrategy):


    def __init__(self, exchange, pair, timeframe, volume):
        super().__init__(exchange, pair, timeframe, volume)
        # For now we only accept one execution
        # User needs to define custom executions models
        # self.execution_models = {
        #     "limit_chase": UserExecutionModel(exchange, pair, self.ws, self.ws_token, self.strat_id, 0.1)
        # }


    def user_setup(self):
        # Tools:
        # self.add_indicator()
        # self.add_crossup()
        # self.add_crossdown()
        # self.add_crossover()
        # self.add_crossunder
        pass

    def long_condition(self):
        # Example:
        # self.df["long"] = (self.df["RSI"] < 70) & (self.df["CROSSUP_SMA0_SMA1"])
        # Need to use pandas operators
        pass


    def short_condition(self):
        # Example:
        # self.df["short"] = (self.df["RSI"] > 30) & (self.df["CROSSDOWN_SMA0_SMA1"])
        # Need to use pandas operators
        pass


    def user_tick(self):
        # Example:
        # last = self.df.iloc[-2] ==> last row is current candle

        # if last["long"]:
        #     print("We go long !")
        #     self.execution_models["user_execution"].add_long_order(total_vol=0.0234567)

        # if last["short"]:
        #     print("We go short !")
        #     self.execution_models["user_execution"].add_short_order(total_vol=0.0234567)
        pass