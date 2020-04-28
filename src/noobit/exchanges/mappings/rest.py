from noobit.exchanges.kraken.rest.api import KrakenRestAPI
from noobit.exchanges.bitmex.rest.api import BitmexRestAPI
from noobit.exchanges.kraken.rest.new_api import KrakenRestAPI as NewKrakenAPI


rest_api_map = {"kraken": KrakenRestAPI,
                "bitmex": BitmexRestAPI,
                "new_kraken": NewKrakenAPI
                }