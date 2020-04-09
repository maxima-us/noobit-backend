from engine.strat_runner import StratRunner
from strategies.mock_strat import MockStrat


# ==================== WITHOUT STRATRUNNER

# async def main():
#     strat = BaseStrategy(exchange="kraken",
#                          pair=["xbt-usd"],
#                          timeframe=240,
#                          volume=0,
#                          )

#     # data = await strat.get_ohlc()
#     # data["mama"], data["fama"] = talib.MAMA(data['close'], fastlimit=0.5, slowlimit=0.05)
#     # crossdf = await strat.crossup(col1="mama", col2="fama", df=data)
#     # print(crossdf)

#     # strat.data["mama"], strat.data["fama"] = talib.MAMA(strat.data["close"], fastlimit=0.5, slowlimit=0.05)
#     # strat.long = strat.crossup(strat.data["mama"], strat.data["fama"], strat.data)

#     await strat.setup_df()
#     # add_signals can only be run after we have set up our df
#     strat.add_indicator(talib.MAMA, "close", fastlimit=0.5, slowlimit=0.05)
#     strat.add_indicator(talib.RSI, "close", timeperiod=14)
#     print(strat.df)
#     # crossup and down needs to have the signals already added to the df
#     crossdf = await strat.crossup(col1="MAMA_0", col2="MAMA_1", df=strat.df)
#     print(crossdf)



# asyncio.run(main())


# ==================== WITH STRATRUNNER

# strat = BaseStrategy(exchange="kraken",
#                      pair=["eth-usd"],
#                      timeframe=240,
#                      volume=0,
#                      )
# strat.add_indicator(func=talib.MAMA, source="close", fastlimit=0.5, slowlimit=0.05)
# strat.add_indicator(func=talib.RSI, source="close", timeperiod=14)
# strat.add_crossunder("RSI", 45)
# strat.add_crossunder("RSI", 60)
# strat.add_crossup("MAMA0", "MAMA1")
# # strat.add_long_condition(condition=(("RSI" < 60) & "CROSSOVER_MAMA0_MAMA1"))


# strat2 = BaseStrategy(exchange="kraken",
#                       pair=["eth-usd"],
#                       timeframe=60,
#                       volume=0,
#                       )
# strat2.add_indicator(func=talib.MAMA, source="close", fastlimit=0.5, slowlimit=0.05)
# strat2.add_indicator(func=talib.RSI, source="close", timeperiod=14)
# strat2.add_indicator(func=talib.HT_TRENDMODE, source="close")
# strat2.add_crossover("RSI", 60)

strat3 = MockStrat(exchange="kraken",
                   pair=["xbt-usd"],
                   timeframe=1,
                   volume=0
                   )

runner = StratRunner(strats=[strat3])
runner.run()