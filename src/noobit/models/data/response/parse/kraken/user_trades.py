import logging

import stackprinter

from noobit.server import settings
from noobit.models.data.response.trade import TradesList, TradesByID

# parse ordertypes to noobit format
MAP_ORDERTYPES = {
    "market": "market",
    "limit": "limit",
    "stop market": "stop-loss",
    "take-profit": "take-profit",
    "settle-position": "settle-position",

    "stop-loss-limit": "stop-loss-limit",
    "take-profit-limit": "take-profit-limit",
}

#  market
#     limit (price = limit price)
#     stop-loss (price = stop loss price)
#     take-profit (price = take profit price)
#     stop-loss-profit (price = stop loss price, price2 = take profit price)
#     stop-loss-profit-limit (price = stop loss price, price2 = take profit price)
#     stop-loss-limit (price = stop loss trigger price, price2 = triggered limit price)
#     take-profit-limit (price = take profit trigger price, price2 = triggered limit price)
#     trailing-stop (price = trailing stop offset)
#     trailing-stop-limit (price = trailing stop offset, price2 = triggered limit offset)
#     stop-loss-and-limit (price = stop loss price, price2 = limit price)
#     settle-position

def parse_user_trades_to_list(response, symbol):
    if response is None:
        return TradesList(data=[])

    # response["result"] from kraken will be indexed with "trade" and "count"
    # check if we received a response for single/all trades
    try:
        key = list(response.keys())[0]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
    if key == "trades":
        response = response["trades"]
        # else : the request for a single trade is indexed by ID
        # we want the full response in that case

    try:
        parsed_trades = [
            parse_single_trade(key, info) for key, info in response.items()
        ]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return {"data": parsed_trades, "last": None}



def parse_user_trades_by_id(response, symbol):
    if response is None:
        return TradesByID(data={})

    # response["result"] from kraken will be indexed with "trade" and "count"
    # check if we received a response for single/all trades
    try:
        key = list(response.keys())[0]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
    if key == "trades":
        response = response["trades"]
        # else : the request for a single trade is indexed by ID
        # we want the full response in that case

    try:
        parsed_trades = {
            key: parse_single_trade(key, info) for key, info in response.items()
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return {"data": parsed_trades, "last": None}


def parse_single_trade(key, value):
    info = value
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]
    # map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    try:
        parsed_info = {
            "trdMatchID": key,
            "transactTime": info["time"]*10**9,
            "orderID": info["ordertxid"],
            "clOrdID": None,
            "symbol": map_to_standard[info["pair"].upper()],
            "side": info["type"],
            "ordType": MAP_ORDERTYPES[info["ordertype"]],
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