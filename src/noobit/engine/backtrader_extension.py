# -*- coding: utf-8; py-indent-offset:4 -*-
import csv
import uuid

import backtrader as bt
from backtrader.feeds import PandasData

from noobit.logging.structlogger import get_logger
from noobit_user import get_abs_path


logger = get_logger(__name__)


# ! We sometimes get problems when plotting cerebro
# TODO should also be able take pandas Series containing Size of the order as param
# TODO change the logic for buy and sell orders, this is not flexible enough

# ! get a unique id for each backtest we run so we can match backtest logs (csv files) to
# !     backtest final account value (which we will probably want to store in db)


#! EVENTUALLY : replace this entirely with a live replay of all trades/orderbook through a backtesting websocket
#!      (since our execution engines reads in data from websocket this should be relatively straight-forward)


backtest_id_placeholder = None


class ExtendedFeed(PandasData):

    lines = ('long', 'short',)

    # for params, None = column not present, -1 = autodetect

    params = (
        ('datetime', 0),
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('long', 5),
        ('short', 6),
        ('volume', 7),
    )
    datafields = PandasData.datafields + (['long', 'short'])


user_dir = get_abs_path()
# Create a Stratey
class Strategy(bt.Strategy):

    fieldnames = [
        'datetime',
        'close',
        'side',
        'avgPx',
        'grossAmt',
        'profit',
        'commission',
        'drawdown',
        'max_drawdown',
        'totalNetValue',
        'text'
    ]

    def log(self, col_values: dict, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)

        with open(self.file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            col_values["datetime"] = dt
            writer.writerow(col_values)


    # def log_rejection(self, text, dt=None):
    #     dt = dt or self.datas[0].datetime.datetime(0)

    #     with open(self.file_path, 'a', newline='') as csvfile:
    #         writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
    #         col_values["datetime"] = dt
    #         col_values = {
    #             "datetime": dt,
    #             "close"

    #         }
    #         writer.writerow(col_values)


    def __init__(self, strategy_name):

        self.strategy_name = strategy_name
        self.backtest_id = uuid.uuid4()
        global backtest_id_placeholder
        backtest_id_placeholder = self.backtest_id

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        file_name = f"{self.strategy_name}_backtest_{self.backtest_id}.csv"
        self.file_path = f"{user_dir}/data/backtest/{file_name}"

        # write headers on init
        with open(self.file_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                # self.log(
                #     'Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #     (order.executed.price,
                #      order.executed.value,
                #      order.executed.comm))
                col_values = {
                    "avgPx": order.executed.price,
                    "grossAmt": order.executed.value,
                    "commission": order.executed.comm
                }
                self.log(col_values)

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                # self.log('Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #          (order.executed.price,
                #           order.executed.value,
                #           order.executed.comm))
                col_values = {
                    "avgPx": order.executed.price,
                    "grossAmt": order.executed.value,
                    "commission": order.executed.comm
                }
                self.log(col_values)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(col_values={
                "text": 'Order Canceled/Margin/Rejected'
            })

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        # self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
        #          (trade.pnl, trade.pnlcomm))
        col_values = {
            "profit": trade.pnl,
            "commission": trade.pnlcomm
        }
        self.log(col_values)


    def next(self):
        # Log the closing price of the series from the reference if we want to have every candle close
        # self.log('Close: %.2f' % self.dataclose[0])
        # self.log(f'Drawdown: {self.stats.drawdown.drawdown[-1]}')
        # self.log(f'Max Drawdown: {self.stats.drawdown.maxdrawdown[-1]}')
        # self.log(f'Total Net Value: {self.stats.broker.value[-1]}')

        # base dict that we will log in any case
        # we will add key/values depending on orders
        col_values = {
            "close": self.dataclose[0],
            "drawdown": self.stats.drawdown.drawdown[-1],
            "max_drawdown": self.stats.drawdown.maxdrawdown[-1],
            "totalNetValue": self.stats.broker.value[-1]
        }


        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            self.log(col_values)
            return


        # for some reason "is True" and "if self.data.long" don't work
        if self.data.long == True:

            col_values["side"] = "long"
            col_values["avgPx"] = self.dataclose[0]

            if not self.position:
                self.order = self.buy()
                # self.log('↗ OPENING LONG, %.2f' % self.dataclose[0])
                col_values["text"] = "opening"

            else:
                self.order = self.close()
                self.order = self.buy()
                # self.log('↗ OPENING LONG, %.2f' % self.dataclose[0])
                col_values["text"] = "closing & opening"

        if self.data.short == True:

            col_values["side"] = "long"
            col_values["avgPx"] = self.dataclose[0]

            if not self.position:
                self.order = self.sell()
                # self.log('↘ OPENING SHORT, %.2f' % self.dataclose[0])
                col_values["text"] = "opening"
            else:
                self.order = self.close()
                self.order = self.sell()
                # self.log('↘ OPENING SHORT, %.2f' % self.dataclose[0])
                col_values["text"] = "closing & opening"


        # get back updated dict and log
        self.log(col_values)




# ================================================================================


def printTradeAnalysis(analyzer):
    '''
    Function to print the Technical Analysis results in a nice format.
    '''
    #Get the results we are interested in
    total_open = analyzer.total.open
    total_closed = analyzer.total.closed
    total_won = analyzer.won.total
    total_lost = analyzer.lost.total
    win_streak = analyzer.streak.won.longest
    lose_streak = analyzer.streak.lost.longest
    pnl_net = round(analyzer.pnl.net.total, 2)
    strike_rate = round((total_won / total_closed) * 100, 2)
    total_len = analyzer.len.total
    avg_len = round(analyzer.len.average, 2)
    min_len = analyzer.len.min
    max_len = analyzer.len.max

    #Designate the rows
    h1 = ['Total Open', 'Total Closed', 'Total Won', 'Total Lost']
    h2 = ['Strike Rate','Win Streak', 'Losing Streak', 'PnL Net']
    h3 = ['Total Length', 'Avg Length', 'Min Length', 'Max Length']
    r1 = [total_open, total_closed,total_won,total_lost]
    r2 = [strike_rate, win_streak, lose_streak, pnl_net]
    r3 = [total_len, avg_len, min_len, max_len]
    #Check which set of headers is the longest.
    if len(h1) > len(h2):
        header_length = len(h1)
    else:
        header_length = len(h2)
    #Print the rows
    print_list = [h1,r1,h2,r2, h3, r3]
    row_format ="{:<15}" * (header_length + 1)
    print("Trade Analysis Results:")
    for row in print_list:
        print(row_format.format('',*row))


def printSQN(analyzer):
    sqn = round(analyzer.sqn, 2)
    print('SQN: {}'.format(sqn))

def printVWR(analyzer):
    vwr = round(analyzer["vwr"], 2)
    print('VWR: {}'.format(vwr))

def printSharpe(analyzer):
    sharpe = round(analyzer["sharperatio"], 2)
    print('Sharpe: {}'.format(sharpe))

def printTimeReturn(analyzer):
    timereturn = analyzer
    print("Benchmark: {}".format(timereturn))


def run(df, strategy_name, commission=0):

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Pass gryphon_strategy_class as superclass
    cerebro.addstrategy(Strategy, strategy_name)

    # Get the dataframe with buy and sell signals that we created in the strat file
    # df = df

    # Pass it to the backtrader datafeed and add to cerebro
    data = ExtendedFeed(dataname=df)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Add observers and analyzers
    cerebro.addobserver(bt.observers.DrawDown)
    cerebro.addobserver(bt.observers.TimeReturn)
    cerebro.addobserver(bt.observers.Benchmark)
    cerebro.addanalyzer(bt.analyzers.AnnualReturn)
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.VWR, _name="vwr")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe")
    cerebro.addanalyzer(bt.analyzers.TimeReturn, data=data, _name="benchmark")


    # Set our desired cash start
    cerebro.broker.setcash(100000.0)

    # Add a FixedSize sizer according to the stake
    # TODO change this
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)


    # Set the commission
    cerebro.broker.setcommission(commission=commission)

    s = '| Backtesting Strat : %s  |' % strategy_name
    print('-' * len(s))
    print(s)
    print('-' * len(s) + '\n')
    print('Starting Portfolio Value : {0}'.format(cerebro.broker.getvalue()))
    print('-' * len(s) + '\n')
    start_account_value = cerebro.broker.getvalue()

    # Run over everything
    strategies = cerebro.run()
    first = strategies[0]

    printTradeAnalysis(first.analyzers.ta.get_analysis())
    printSQN(first.analyzers.sqn.get_analysis())
    printVWR(first.analyzers.vwr.get_analysis())
    printSharpe(first.analyzers.sharpe.get_analysis())
    # printTimeReturn(first.analyzers.benchmark.get_analysis())

    index_start_value = float(df.iloc[0]["open"])
    index_end_value = float(df.iloc[-1]["close"])
    index_return = round((index_end_value - index_start_value) / (index_start_value) * 100, 2)
    print(f"Index Return: {index_return} %")

    final_account_value = round(cerebro.broker.getvalue(), 2)
    strat_return = round((final_account_value - start_account_value) / (start_account_value) * 100 , 2)
    print(f"Strategy Return: {strat_return} %")

    print('-' * len(s) + '\n')
    print('Final Portfolio Value : {0}'.format(final_account_value))
    print('-' * len(s) + '\n')

    return {
        "start_account_value": start_account_value,
        "final_account_value": final_account_value
    }

    figure = cerebro.plot(style='candlebars', width=21, height=9)[0][0]
    figure.savefig(f"{user_dir}/data/backtest/{strategy_name}_backtest_{backtest_id_placeholder}.png")