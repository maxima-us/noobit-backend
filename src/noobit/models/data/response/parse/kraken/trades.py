import logging

import stackprinter

from noobit.server import settings
from noobit.models.data.response.trade import TradesList, TradesByID


def parse_trades_to_list(response, symbol):
    if response is None:
        return TradesList(data=[])

    # response["result"] from kraken will be indexed with "trade" and "count"
    try:
        trades = response["trades"]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    try:
        parsed_trades = [
            parse_single_trade(key, info) for key, info in trades.items()
        ]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_trades



def parse_trades_by_id(response, symbol):
    if response is None:
        return TradesByID(data={})

    # response["result"] from kraken will be indexed with "trade" and "count"
    try:
        trades = response["trades"]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    try:
        parsed_trades = {
            key: parse_single_trade(key, info) for key, info in trades.items()
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_trades


def parse_single_trade(key, value):
    info = value
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]
    map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    try:
        parsed_info = {
            "trdMatchID": key,
            "transactTime": info["time"],
            "orderID": info["ordertxid"],
            "clOrdID": None,
            "symbol": map_to_standard[info["pair"].upper()],
            "side": info["type"],
            "ordType": info["ordertype"],
            "avgPx": info["price"],
            "cumQty": info["vol"],
            "grossTradeAmt": info["cost"],
            "commission": info["fee"],
            "tickDirection": None,
            "text": info["misc"]
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info


# EXAMPLE OF KRAKEN RESPONSE
# {
#   "TZ63HS-YBD4M-3RDG7H": {
#     "ordertxid": "OXXRD7-L67OU-QWHJEZ",
#     "postxid": "TKH1SE-M7IF3-CFI4LT",
#     "pair": "ETH-USD",
#     "time": 1588032030.4648,
#     "type": "buy",
#     "ordertype": "market",
#     "price": "196.94000",
#     "cost": "7395.50936",
#     "fee": "14.79101",
#     "vol": "37.55209384",
#     "margin": "0.00000",
#     "misc": ""
#   },
#   "TESD4J-6G7RU-K5C9TU": {
#     "ordertxid": "ORZGFF-GENRB-Z20HTV",
#     "postxid": "T6HT2W-ER1S7-5MVQGW",
#     "pair": "ETH-USD",
#     "time": 1588032024.6599,
#     "type": "buy",
#     "ordertype": "market",
#     "price": "196.93124",
#     "cost": "6788.34719",
#     "fee": "13.57670",
#     "vol": "34.47064696",
#     "margin": "1697.08680",
#     "misc": "closing"
#   },
#   "TEF2TE-RRBVG-FLFHG6": {
#     "ordertxid": "OL1AHL-OOF5D-V3KKJM",
#     "postxid": "TKH0SE-M1IF3-CFI1LT",
#     "posstatus": "closed",
#     "pair": "ETH-USD",
#     "time": 1585353611.261,
#     "type": "sell",
#     "ordertype": "market",
#     "price": "131.01581",
#     "cost": "7401.30239",
#     "fee": "17.76313",
#     "vol": "56.49167433",
#     "margin": "1850.32560",
#     "misc": ""
#   }
# }