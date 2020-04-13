import asyncio

import click
import httpx
from structlogger import get_logger, log_exception

from exchanges.mappings import rest_api_map
from processor.feed_handler import FeedHandler
from server import main_server


logger = get_logger(__name__)


@click.command()
@click.option("--exchange", default="kraken", help="Lowercase exchange")
@click.option("--pair", help="Dash-separated lowercase pair")
def aggregate_historical_trades(exchange, pair):
    api = rest_api_map[exchange]()
    api.session = httpx.AsyncClient()
    try:
        asyncio.run(api.write_historical_trades_to_csv(pair=[pair]))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(logger, e)


@click.command()
@click.option("--exchanges", default=["kraken"], help="List of lowercase exchanges")
@click.option("--pairs", default=["XBT/USD", "ETH/USD"], help="List of slash-separated uppercase pairs")
@click.option("--private_feeds", default=["ownTrades", "openOrders"], help="List of private feeds to subscribe to")
@click.option("--public_feeds", default=["trade", "spread"], help="List of public feeds to subscribe to")
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
@click.option("--host", default="localhost", help="Host adress")
@click.option("--port", default=8000, help="Host port")
@click.option("--auto_reload", default=False, help="Auto-reload (bool)")
def run_server(host, port, auto_reload):
    try:
        main_server.run("server.main_app:app", host=host, port=port, reload=auto_reload)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(logger, e)



@click.command()
@click.option("--exchange", default="kraken", help="Lowercase exchange")
@click.option("-pair", help="List of dash-separated lowercase pairs")
@click.option("--timeframe", help="TimeFrame in minutes")
@click.option("--volume", default=0, help="Volume in lots")
def run_stratrunner(exchange, pair, timeframe, volume):
    pass




if __name__ == "__main__":

    try:
        aggregate_historical_trades()
    except Exception as e:
        log_exception(logger, e)


# if __name__ == "__main__":
#     try:
#         asyncio.run(aggregate_historical_trades())
#     except Exception as e:
#         log_exception(logger, e)
