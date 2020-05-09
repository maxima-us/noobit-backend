import logging
from datetime import datetime

import stackprinter

from noobit.server import settings


def parse_orderbook(response):

    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]

    try:
        key = list(response.keys())[0]
        response = response[key]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    try:
        parsed_orderbook = {

            "sendingTime": datetime.utcnow(),
            "symbol": map_to_standard[key],
            "asks": {item[0]: item[1] for item in response["asks"]},
            "bids": {item[0]: item[1] for item in response["bids"]}
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_orderbook


# KRAKEN RESPONSE FORMAT (DOC)
# Result: array of pair name and market depth

# <pair_name> = pair name
#     asks = ask side array of array entries(<price>, <volume>, <timestamp>)
#     bids = bid side array of array entries(<price>, <volume>, <timestamp>)

# KRAKEN EXAMPLE RESULT
# {"XXBTZUSD":{
#     "asks":[
#         ["9294.60000","1.615",1588792807],
#         ["9295.00000","0.306",1588792808]
#     ],
#     "bids":[
#         ["9289.50000","1.179",1588792808],
#         ["9289.40000","0.250",1588792808],
#         ["9226.30000","2.879",1588792742]]
#     }
# }