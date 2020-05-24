import asyncio
from importlib import import_module

import click
import httpx

from noobit.engine.strat_runner import StratRunner
from noobit.logging.structlogger import get_logger, log_exception
from noobit.exchanges.mappings import rest_api_map
from noobit.processor.feed_handler import FeedHandler
from noobit.server import main_server


logger = get_logger(__name__)


@click.command()
@click.option("--exchange", "-e", default="kraken", help="Lowercase exchange")
@click.option("--pair", "-p", required=True, help="Dash-separated lowercase pair")
def aggregate_historical_trades(exchange, pair):
    api = rest_api_map[exchange]()
    api.session = httpx.AsyncClient()
    asyncio.run(api.aggregate_historical_trades(symbol=pair))
    # try:
    #     asyncio.run(api.aggregate_historical_trades(symbol=pair))
    # except KeyboardInterrupt:
    #     pass
    # except Exception as e:
    #     log_exception(logger, e)


@click.command()
@click.option("--exchanges", "-e", multiple=True, default=["kraken"], help="List of lowercase exchanges")
@click.option("--pairs", "-p", multiple=True, default=["XBT-USD", "ETH-USD"], help="dash-separated uppercase pairs")
@click.option("--private_feeds", "-prf", multiple=True, default=["trade", "order"], help="Private feeds to subscribe to")
@click.option("--public_feeds", "-pbf", multiple=True, default=["instrument", "trade", "orderbook"], help="Public feeds to subscribe to")
def run_feedhandler(exchanges, pairs, private_feeds, public_feeds):
    try:
        fh = FeedHandler(exchanges=exchanges,
                         private_feeds=private_feeds,
                         public_feeds=public_feeds,
                         pairs=pairs)
        fh.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(logger, e)


@click.command()
@click.option("--host", "-h", default="localhost", help="Host adress")
@click.option("--port", "-p", default=8000, help="Host port")
@click.option("--auto_reload", "-ar", default=False, help="Auto-reload (bool)")
def run_server(host, port, auto_reload):
    try:
        main_server.run("noobit.server.main_app:app", host=host, port=port, reload=auto_reload)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(logger, e)



@click.command()
# strategy name == file name (e.g trend_following.py => name = trend_following)
@click.option("--strategy", "-s", help="Name of Strategy", required=True)
@click.option("--exchange", "-e", default="kraken", help="Lowercase exchange")
@click.option("--pair", "-p", default="xbt-usd", help="Dash-separated lowercase pairs")
@click.option("--timeframe", "-tf", help="TimeFrame in minutes", required=True)
@click.option("--volume", "-v", default=0, help="Volume in lots")
def run_stratrunner(strategy, exchange, pair, timeframe, volume):
    strat_dir_path = "noobit_user.strategies"
    strat_file_path = f"{strat_dir_path}.{strategy}"
    strategy = import_module(strat_file_path)

    # every strat file needs to define the strategy class
    strat = strategy.Strategy(name="testName",
                              strat_id=10001,
                              description="this is a test description",
                              exchange=exchange,
                              pair=pair,
                              timeframe=timeframe,
                              volume=volume
                              )

    runner = StratRunner(strats=[strat])
    runner.run()
