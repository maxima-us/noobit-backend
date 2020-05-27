import logging
from decimal import Decimal

import stackprinter

from noobit.server import settings
from noobit.models.data.base.types import PAIR


def parse_public_trades(response):

    try:
        key = list(response.keys())[0]
        last = int(response["last"])
        raw_trades = response[key]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


    try:
        parsed_trades = [
            parse_single_trade(item, key) for item in raw_trades
        ]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return {
        "data": parsed_trades,
        "last": last
    }



def parse_single_trade(list_item: list, symbol: PAIR):
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]
    # map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    try:
        parsed_info = {
            "trdMatchID": None,
            "orderID": None,
            "symbol": map_to_standard[symbol.upper()],
            "transactTime": list_item[2]*10**9,
            "side": "buy" if list_item[3] == "b" else "sell",
            "ordType": "market" if list_item[4] == "m" else "limit",
            "avgPx": list_item[0],
            "cumQty": list_item[1],
            "grossTradeAmt": Decimal(list_item[0]) * Decimal(list_item[1]),
            "text": list_item[5]
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info

# KRAKEN RESPONSE FORMAT
# Result: array of pair name and recent trade data
# <pair_name> = pair name
#     array of array entries(<price>, <volume>, <time>, <buy/sell>, <market/limit>, <miscellaneous>)
# last = id to be used as since when polling for new trade data

# KRAKEN EXAMPLE
# {
#   "XXBTZUSD":[
#     ["8943.10000","0.01000000",1588710118.4965,"b","m",""],
#     ["8943.10000","4.52724239",1588710118.4975,"b","m",""],
#     ["8941.10000","0.04000000",1588710129.8625,"b","m",""],
#   ],
#   "last":"1588712775751709062"
# }