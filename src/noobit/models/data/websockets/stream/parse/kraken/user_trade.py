from decimal import Decimal

from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)


def parse_user_trade(message):

    try:
        parsed_trades = [
            parse_single_trade(key, value) for trade_dict in message[0] for key, value in trade_dict.items()
        ]
        return parsed_trades
    except Exception as e:
        log_exception(logger, e)


def parse_single_trade(key, value):

    info = value

    try:
        parsed_trade = {
            "trdMatchID": key,
            "orderID": info["postxid"],
            "symbol": info["pair"].replace("/", "-"),
            "side": info["type"],
            "ordType": info["ordertype"],
            "avgPx": info["price"],
            "cumQty": info["vol"],
            "grossTradeAmt": Decimal(info["price"]) * Decimal(info["vol"]),
            "commission": info["fee"],
            "transactTime": float(info["time"])*10**9,
        }

        return parsed_trade
    except Exception as e:
        log_exception(logger, e)

# EXAMPLE MESSAGE FROM KRAKEN DOC
# [
#   [
#     {
#       "TDLH43-DVQXD-2KHVYY": {
#         "cost": "1000000.00000",
#         "fee": "1600.00000",
#         "margin": "0.00000",
#         "ordertxid": "TDLH43-DVQXD-2KHVYY",
#         "ordertype": "limit",
#         "pair": "XBT/EUR",
#         "postxid": "OGTT3Y-C6I3P-XRI6HX",
#         "price": "100000.00000",
#         "time": "1560516023.070651",
#         "type": "sell",
#         "vol": "1000000000.00000000"
#       }
#     },
#     {
#       "TDLH43-DVQXD-2KHVYY": {
#         "cost": "1000000.00000",
#         "fee": "600.00000",
#         "margin": "0.00000",
#         "ordertxid": "TDLH43-DVQXD-2KHVYY",
#         "ordertype": "limit",
#         "pair": "XBT/EUR",
#         "postxid": "OGTT3Y-C6I3P-XRI6HX",
#         "price": "100000.00000",
#         "time": "1560516023.070658",
#         "type": "buy",
#         "vol": "1000000000.00000000"
#       }
#     },
#     {
#       "TDLH43-DVQXD-2KHVYY": {
#         "cost": "1000000.00000",
#         "fee": "1600.00000",
#         "margin": "0.00000",
#         "ordertxid": "TDLH43-DVQXD-2KHVYY",
#         "ordertype": "limit",
#         "pair": "XBT/EUR",
#         "postxid": "OGTT3Y-C6I3P-XRI6HX",
#         "price": "100000.00000",
#         "time": "1560520332.914657",
#         "type": "sell",
#         "vol": "1000000000.00000000"
#       }
#     },
#     {
#       "TDLH43-DVQXD-2KHVYY": {
#         "cost": "1000000.00000",
#         "fee": "600.00000",
#         "margin": "0.00000",
#         "ordertxid": "TDLH43-DVQXD-2KHVYY",
#         "ordertype": "limit",
#         "pair": "XBT/EUR",
#         "postxid": "OGTT3Y-C6I3P-XRI6HX",
#         "price": "100000.00000",
#         "time": "1560520332.914664",
#         "type": "buy",
#         "vol": "1000000000.00000000"
#       }
#     }
#   ],
#   "ownTrades"
# ]