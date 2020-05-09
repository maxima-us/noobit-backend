import logging
from decimal import Decimal

from pydantic import ValidationError
import stackprinter

from noobit.server import settings



def parse_closed_positions_to_list(response):

    trades = response["trades"]

    try:
        parsed_positions = [
            parse_single_position(key, info) for key, info in trades.items()
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
            # eventually there should be some way to get this info from the db
            "clOrdID": None,
            "symbol": map_to_standard[info["pair"]],
            "currency": map_to_standard[info["pair"]].split("-")[1],
            "side": info["type"],
            "ordType": info["ordertype"],
            "transactTime": info["time"],

            "cashMargin": "margin",
            "ordStatus": info["posstatus"],
            "workingIndicator": False if info["posstatus"] in ["closed", "canceled"] else True,

            "grossTradeAmt": info["cost"],
            "orderQty": info["vol"],
            "cashOrderQty": info["cost"],
            "cumQty": info["cvol"],
            "leavesQty": Decimal(info["vol"]) - Decimal(info["cvol"]),

            "marginRatio": Decimal(info["margin"]) / Decimal(info["cost"]),
            "marginAmt": info["margin"],

            "commission": info["fee"],

            "price": info["price"],
            "avgPx": info["cprice"],

            "fills": [
                {
                    "fillExecID": trade_id,
                    "noFills": len(info["trades"])
                }
                for trade_id in info["trades"]
                ],

            # we need to request <docacls> to get this value
            "realisedPnL": info.get("net", None),

            "text": {
                "misc": info["misc"],
                "notes": "fillExecID correponds to Kraken Trade ID"
            }

        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info



# Kraken does not have a direct endpoint for closed_positions
# We need to fetch trades and then filter

# EXAMPLE RESPONSE TO REQUEST FOR trade == closed_position
    # {'ordertxid': 'OYSYI7-YMGY6-74QRDY',
    #  'postxid': 'TKH2SE-M7IF5-CFI7LT',
    #  'posstatus': 'closed',
    #  'pair': 'XETHZUSD',
    #  'time': 1588809613.7804,
    #  'type': 'sell',
    #  'ordertype': 'market',
    #  'price': '198.58815',
    #  'cost': '6852.98722',
    #  'fee': '15.07658',
    #  'vol': '34.50854049',
    #  'margin': '1713.24681',
    #  'cprice': '213.54',
    #  'ccost': '7369.11',
    #  'cfee': '14.73',
    #  'cvol': '34.50854049',
    #  'cmargin': '1842.27',
    #  'misc': '',
    #  'net': '-545.9409',
    #  'trades': ['TPL6FJ-LZWCE-3YKZHW', ]}



# KRAKEN TRADE_HISTORY RESPONSE FORMAT (FROM DOC)
# trades = array of trade info with txid as the key
#     ordertxid = order responsible for execution of trade
#     pair = asset pair
#     time = unix timestamp of trade
#     type = type of order (buy/sell)
#     ordertype = order type
#     price = average price order was executed at (quote currency)
#     cost = total cost of order (quote currency)
#     fee = total fee (quote currency)
#     vol = volume (base currency)
#     margin = initial margin (quote currency)
#     misc = comma delimited list of miscellaneous info
#         closing = trade closes all or part of a position
# count = amount of available trades info matching criteria

# If the trade opened a position, the follow fields are also present in the trade info:

#     posstatus = position status (open/closed)
#     cprice = average price of closed portion of position (quote currency)
#     ccost = total cost of closed portion of position (quote currency)
#     cfee = total fee of closed portion of position (quote currency)
#     cvol = total fee of closed portion of position (quote currency)
#     cmargin = total margin freed in closed portion of position (quote currency)
#     net = net profit/loss of closed portion of position (quote currency, quote currency scale)
#     trades = list of closing trades for position (if available)