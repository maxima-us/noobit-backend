import logging

import stackprinter

from noobit.server import settings


def parse_instrument(response):

    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]

    try:
        key = list(response.keys())[0]
        response = response[key]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    try:
        parsed_instrument = {
            "symbol": map_to_standard[key],
            "low": response["l"][0],
            "high": response["h"][0],
            "vwap": response["p"][0],
            "last": response["c"][0],
            "volume": response["v"][0],
            "trdCount": response["t"][0],
            "bestAsk": {response["a"][0]: response["a"][2]},
            "bestBid": {response["b"][0]: response["b"][2]},
            "prevLow": response["l"][1],
            "prevHigh": response["h"][1],
            "prevVwap": response["p"][1],
            "prevVolume": response["v"][1],
            "prevTrdCount": response["t"][1]
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_instrument

# EXAMPLE OF KRAKEN RESPONSE
# {"XXBTZUSD": {
#     "a":["9540.40000","1","1.000"],
#     "b":["9535.70000","1","1.000"],
#     "c":["9535.50000","0.64488521"],
#     "v":["7584.70758791","11528.72806088"],
#     "p":["9371.51319","9339.82539"],
#     "t":[19111,30423],
#     "l":["9037.00000","9037.00000"],
#     "h":["9619.90000","9619.90000"],
#     "o":"9163.10000"
#     }
# }

# KRAKEN TICKER RESPONSE (DOC)
# <pair_name> = pair name
#     a = ask array(<price>, <whole lot volume>, <lot volume>),
#     b = bid array(<price>, <whole lot volume>, <lot volume>),
#     c = last trade closed array(<price>, <lot volume>),
#     v = volume array(<today>, <last 24 hours>),
#     p = volume weighted average price array(<today>, <last 24 hours>),
#     t = number of trades array(<today>, <last 24 hours>),
#     l = low array(<today>, <last 24 hours>),
#     h = high array(<today>, <last 24 hours>),
#     o = today's opening price
