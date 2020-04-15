[![Build Status](https://travis-ci.com/maxima-us/noobit-backend.svg?branch=master)](https://travis-ci.com/maxima-us/noobit-backend)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ee5a7cf93c65477db5bd675f8979aa9d)](https://www.codacy.com/manual/maximousse/noobit-backend?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=maxima-us/noobit-backend&amp;utm_campaign=Badge_Grade)

# NooBit Backend

## Installation

```console
git clone https://github.com/maxima-us/noobit-backend
python setup.py develop
```

For Ta-Lib install please see their doc


## Processes

**API Server** :\
Based on Uvicorn and FastAPI\
OpenAPI interface accessible at localhost:8000/docs\
Interfaces with sqlite db via Tortoise ORM\
Listens to redis channels to automatically update db\

**Feed Handler** :\
Receive data from websocket, sort and publish to appropriate redis channels

**Trading Engine** :\
Handle signals and execution logic (not implemented yet)


## Usage

### Credentials and environment variables

For each exchange, you will need to provide an .env file with a list of API keys.
To open the env file (ide will default to vscode):
```console
noobit-add-keys --exchange=<exchange_name> --ide=<ide>
```

Make sure to follow the following format (env key for API KEY needs to at least contain <exchange_name> and "API_KEY",
env key for API SECRET needs to at least contain <exchange_name> and "API_SECRET") :
```python
KRAKEN_BTC_USD_API_KEY=<YOUR KEY>
KRAKEN_BTC_USD_API_SECRET=<YOUR SECRET>

#or

KRAKEN_1_API_KEY=<YOUR KEY>
KRAKEN_1_API_SECRET=<YOUR SECRET>
```

### Write your strategy
Strategies are only used to generate signals, execution of orders is handled by execution models that user needs to define

User Strategies should be placed into noobit_user/strategies folder
You should define a Strategy class that subclasses BaseStrategy and defines all methods in the following template:
```python
from noobit.engine.base import BaseStrategy
from noobit.engine.exec.execution import LimitChaseExecution


class Strategy(BaseStrategy):
    """
    Name needs to be "Strategy"
    Needs to subclass BaseStrategy

    Define execution_models to place and cancel orders
    Add indicators to self.df in user_setup
    Refer to self.df for ohlc values
    """

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
```

### Launch


To start api server:
```console
noobit-server --help
```

To start feed handler:
```console
noobit-feedhandler --help
```

To start strat runner:
```console
noobit-stratrunner --help
```

### Testing

From within main folder :
```python
pytest tests
```

## To Do

  - data validation + testing for placing & closing orders
  - implement cancel all positions
  - command line
  - trading engine


