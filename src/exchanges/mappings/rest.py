from exchanges.kraken.rest.api import KrakenRestAPI
from exchanges.bitmex.rest.api import BitmexRestAPI


rest_api_map = {"kraken": KrakenRestAPI,
                "bitmex": BitmexRestAPI,
                }