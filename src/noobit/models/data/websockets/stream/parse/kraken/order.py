import logging
from decimal import Decimal

import stackprinter


MAP_ORDER_STATUS = {

    "pending": "pending-new",
    "open": "new",
    "closed": "filled",
    "canceled": "canceled"
}


# problem: we have : snapshot / new order update / order status change update
# snapshot == first message received from sub
# status change == only one key `status`
# new order == rest of messages
# ==> should we add an "action" message like bitmex ws api has, that identifies if message is a full update or partial ?
# but we sill need to be able to read the current state of orders here ?


#! this is already identified as a snapshot
def parse_order_snapshot_by_id(message):

    try:
        parsed_orders = {
            key: parse_single_order(key, value) for order_dict in message[0] for key, value in order_dict.items()
        }
        return parsed_orders
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


#! this is trickier, we need to specify for EACH message if its a status change or a new order
def parse_order_update_by_id(message):
    try:
        # parsed_orders = {
        # key: MAP_ORDER_STATUS[value["status"]] for key, value in orderdict.items() for orderdict in message[0]
        # }
        # return parsed_orders

        # ==>first test to split status changes / new order
        new_orders = {
            key: parse_single_order(key, value) for order_dict in message[0] for key, value in order_dict.items() if list(value.keys()) > 1
        }
        status_changes = {
            key: {"ordStatus": MAP_ORDER_STATUS[value["status"]]} for key, value in orderdict.items() for orderdict in message[0] if list(value.keys()) == "status"
        }


        return {
            "insert": new_orders,
            "update": status_changes
        }

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))



def parse_single_order(key, value):
    info = value

    try:
        parsed_info = {

            "orderID": key,
            "symbol": info["descr"]["pair"].replace("/", "-"),
            "currency": info["descr"]["pair"].split("/")[1],
            "side": info["descr"]["type"],
            "ordType": info["descr"]["ordertype"],
            "execInst": None,

            "clOrdID": info["userref"],
            "account": None,
            "cashMargin": "cash" if (info["descr"]["leverage"] is None) else "margin",
            "marginRatio": 0 if info["descr"]["leverage"] is None else 1/int(info["descr"]["leverage"][0]),
            "marginAmt": 0 if info["descr"]["leverage"] is None else Decimal(info["cost"])/int(info["descr"]["leverage"][0]),
            "ordStatus": MAP_ORDER_STATUS[info["status"]],
            "workingIndicator": True if (info["status"] in ["pending", "open"]) else False,
            "ordRejReason": info.get("reason", None),

            "timeInForce": None,
            "transactTime": float(info["closetm"])*10**9 if "closetm" in info else None,
            "sendingTime": None,
            "effectiveTime": float(info["opentm"])*10**9,
            "validUntilTime": None,
            "expireTime": None if info["expiretm"] is None else float(info["expiretm"])*10**9,

            "displayQty": None,
            "grossTradeAmt": info["cost"],
            "orderQty": info["vol"],
            "cashOrderQty": info["cost"],
            "orderPercent": None,
            "cumQty": info["vol_exec"],
            "leavesQty": Decimal(info["vol"]) - Decimal(info["vol_exec"]),

            "price": info["descr"]["price"],
            "stopPx": info["stopprice"],
            "avgPx": info["avg_price"],

            "fills": None,
            "commission": info["fee"],

            "targetStrategy": 0,
            "targetStrategyParameters": None,

            "text": {
                "misc": info["misc"],
                "flags": info["oflags"]
            }

        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info

# KRAKEN EXAMPLE OF FULL MESSAGE FROM DOC
# [
#   [
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "cost": "0.00000",
#         "descr": {
#           "close": "",
#           "leverage": "0:1",
#           "order": "sell 10.00345345 XBT/EUR @ limit 34.50000 with 0:1 leverage",
#           "ordertype": "limit",
#           "pair": "XBT/EUR",
#           "price": "34.50000",
#           "price2": "0.00000",
#           "type": "sell"
#         },
#         "expiretm": "0.000000",
#         "fee": "0.00000",
#         "limitprice": "34.50000",
#         "misc": "",
#         "oflags": "fcib",
#         "opentm": "0.000000",
#         "price": "34.50000",
#         "refid": "OKIVMP-5GVZN-Z2D2UA",
#         "starttm": "0.000000",
#         "status": "open",
#         "stopprice": "0.000000",
#         "userref": 0,
#         "vol": "10.00345345",
#         "vol_exec": "0.00000000"
#       }
#     },
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "cost": "0.00000",
#         "descr": {
#           "close": "",
#           "leverage": "0:1",
#           "order": "sell 0.00000010 XBT/EUR @ limit 5334.60000 with 0:1 leverage",
#           "ordertype": "limit",
#           "pair": "XBT/EUR",
#           "price": "5334.60000",
#           "price2": "0.00000",
#           "type": "sell"
#         },
#         "expiretm": "0.000000",
#         "fee": "0.00000",
#         "limitprice": "5334.60000",
#         "misc": "",
#         "oflags": "fcib",
#         "opentm": "0.000000",
#         "price": "5334.60000",
#         "refid": "OKIVMP-5GVZN-Z2D2UA",
#         "starttm": "0.000000",
#         "status": "open",
#         "stopprice": "0.000000",
#         "userref": 0,
#         "vol": "0.00000010",
#         "vol_exec": "0.00000000"
#       }
#     },
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "cost": "0.00000",
#         "descr": {
#           "close": "",
#           "leverage": "0:1",
#           "order": "sell 0.00001000 XBT/EUR @ limit 90.40000 with 0:1 leverage",
#           "ordertype": "limit",
#           "pair": "XBT/EUR",
#           "price": "90.40000",
#           "price2": "0.00000",
#           "type": "sell"
#         },
#         "expiretm": "0.000000",
#         "fee": "0.00000",
#         "limitprice": "90.40000",
#         "misc": "",
#         "oflags": "fcib",
#         "opentm": "0.000000",
#         "price": "90.40000",
#         "refid": "OKIVMP-5GVZN-Z2D2UA",
#         "starttm": "0.000000",
#         "status": "open",
#         "stopprice": "0.000000",
#         "userref": 0,
#         "vol": "0.00001000",
#         "vol_exec": "0.00000000"
#       }
#     },
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "cost": "0.00000",
#         "descr": {
#           "close": "",
#           "leverage": "0:1",
#           "order": "sell 0.00001000 XBT/EUR @ limit 9.00000 with 0:1 leverage",
#           "ordertype": "limit",
#           "pair": "XBT/EUR",
#           "price": "9.00000",
#           "price2": "0.00000",
#           "type": "sell"
#         },
#         "expiretm": "0.000000",
#         "fee": "0.00000",
#         "limitprice": "9.00000",
#         "misc": "",
#         "oflags": "fcib",
#         "opentm": "0.000000",
#         "price": "9.00000",
#         "refid": "OKIVMP-5GVZN-Z2D2UA",
#         "starttm": "0.000000",
#         "status": "open",
#         "stopprice": "0.000000",
#         "userref": 0,
#         "vol": "0.00001000",
#         "vol_exec": "0.00000000"
#       }
#     }
#   ],
#   "openOrders"
# ]


# KRAKEN EXAMPLE OF UPDATE FOR STATUS CHANGE
# [
#   [
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "status": "closed"
#       }
#     },
#     {
#       "OGTT3Y-C6I3P-XRI6HX": {
#         "status": "closed"
#       }
#     }
#   ],
#   "openOrders"
# ]