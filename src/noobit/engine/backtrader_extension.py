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

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        # print('%s, %s' % (dt, txt))
        file_name = f"{self.strategy_name}_backtest_{self.backtest_id}.csv"
        full_path = f"{user_dir}/data/backtest/{file_name}"

        # with open(file_name, mode="a") as file:
        #     file.write(f"{dt} -- {txt}")

        with open(full_path, 'a', newline='') as csvfile:
            fieldnames = ['datetime', 'event']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writerow({'datetime': dt, 'event': txt})


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


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('Executed, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None


    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def next(self):
        # Log the closing price of the series from the reference if we want to have every candle close
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return


        # for some reason "is True" and "if self.data.long" don't work
        if self.data.long == True:

            if not self.position:
                self.order = self.buy()
                self.log('↗ OPENING LONG, %.2f' % self.dataclose[0])
            else:
                self.order = self.close()
                self.order = self.buy()
                self.log('↗ OPENING LONG, %.2f' % self.dataclose[0])

        if self.data.short == True:

            if not self.position:
                self.order = self.sell()
                self.log('↘ OPENING SHORT, %.2f' % self.dataclose[0])
            else:
                self.order = self.close()
                self.order = self.sell()
                self.log('↘ OPENING SHORT, %.2f' % self.dataclose[0])




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
    print('Starting Portfolio Value :{0}'.format(cerebro.broker.getvalue()))

    # Run over everything
    cerebro.run()

    print('Final Portfolio Value :{0}'.format(cerebro.broker.getvalue()))

    # img = cerebro.plot()
    # with open('picture_out.jpg', 'wb') as f:
    #     f.write(img)
    figure = cerebro.plot(style='candlebars', width=21, height=9)[0][0]
    figure.savefig(f"{user_dir}/data/backtest/{strategy_name}_backtest_{backtest_id_placeholder}.png")