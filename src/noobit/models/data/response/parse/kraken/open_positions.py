import logging
from decimal import Decimal

from pydantic import ValidationError
import stackprinter

from noobit.server import settings

def parse_open_positions_to_list(response):

    try:
        parsed_positions = [
            parse_single_position(key, info) for key, info in response.items()
        ]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_positions


def parse_single_position(key, value):
    info = value
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]

    try:
        parsed_info = {
            "orderID": info["ordertxid"],
            "clOrdID": None,
            "symbol": map_to_standard[info["pair"]],
            "currency": map_to_standard[info["pair"]].split("-")[1],
            "side": info["type"],
            "ordType": info["ordertype"],
            "transactTime": info["time"],

            "cashMargin": "margin",
            "ordStatus": "new",
            "workingIndicator": True,

            "grossTradeAmt": info["cost"],
            "orderQty": info["vol"],
            "cashOrderQty": info["cost"],
            "cumQty": info["vol_closed"],
            "leavesQty": Decimal(info["vol"]) - Decimal(info["vol_closed"]),

            "marginRatio": Decimal(info["margin"]) / Decimal(info["cost"]),
            "marginAmt": info["margin"],

            "commission": info["fee"],

            # we need to request <docacls> to get this value
            "unrealisedPnL": info.get("net", None),

            "text": {
                "misc": info["misc"],
                "flags": info["oflags"]
            }

        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info


# KRAKEN RESPONSE FORMAT (FROM DOC)
# <position_txid> = open position info
#     ordertxid = order responsible for execution of trade
#     pair = asset pair
#     time = unix timestamp of trade
#     type = type of order used to open position (buy/sell)
#     ordertype = order type used to open position
#     cost = opening cost of position (quote currency unless viqc set in oflags)
#     fee = opening fee of position (quote currency)
#     vol = position volume (base currency unless viqc set in oflags)
#     vol_closed = position volume closed (base currency unless viqc set in oflags)
#     margin = initial margin (quote currency)
#     value = current value of remaining position (if docalcs requested.  quote currency)
#     net = unrealized profit/loss of remaining position (if docalcs requested.  quote currency, quote currency scale)
#     misc = comma delimited list of miscellaneous info
#     oflags = comma delimited list of order flags
        # viqc = volume in quote currency