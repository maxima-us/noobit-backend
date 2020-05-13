import logging
import stackprinter

from noobit.models.data.response.ohlc import Ohlc
from noobit.server import settings

def parse_ohlc(response):

    try:
        key = list(response.keys())[0]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    try:
        parsed_ohlc = [
            parse_single_ohlc(item, key) for item in response[key]
        ]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_ohlc



def parse_single_ohlc(list_item, symbol):
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]

    try:
        parsed_info = {
            "symbol": map_to_standard[symbol],
            "utcTime": list_item[0]*10**9,
            "open": list_item[1],
            "high": list_item[2],
            "low": list_item[3],
            "close": list_item[4],
            "volume": list_item[6],
            'trdCount': list_item[7]
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info

# KRAKEN RESPONSE FORMAT
# Result: array of pair name and OHLC data

# <pair_name> = pair name
#     array of array entries(<time>, <open>, <high>, <low>, <close>, <vwap>, <volume>, <count>)
# last = id to be used as since when polling for new, committed OHLC data


