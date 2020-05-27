import logging
from decimal import Decimal

import stackprinter

from noobit.server import settings
from noobit.models.data.response.order import OrdersList, OrdersByID


MAP_ORDER_STATUS = {

    "pending": "pending-new",
    "open": "new",
    "closed": "filled",
    "canceled": "canceled"
}


# ================================================================================


def parse_orders_to_list(response, symbol):
    """Parse open or closed orders into unified format and validate data against model.

    Args:
        response (typing.Any): raw response from kraken to open_orders or closed_orders query
        smymbol (noobit.PAIR): filter out only orders for a given symbol

    Returns:
        parsed_orders (list): list containing unvalidated noobit.Order items

    Note:
        parsed data is to be validated by corresponding api method in noobit.exchanges.base.rest.api
    """

    #! this is not correct anymore since we parse it after,
    #! so shoud return empty dict maybe
    if response is None:
        return OrdersList(data=[])

    # response["result"] from kraken will be indexed with "open" or "closed" key according to request
    # check if we received a response for closed/open/single order
    try:
        key = list(response.keys())[0]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    if key == "open":
        response = response["open"]
    elif key == "closed":
        response = response["closed"]
    else:
        # # the request is for a single order filtered by ID
        # response = response[key]
        pass


    try:
        parsed_orders = [
            parse_single_order(key, info) for key, info in response.items()
        ]

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    #! validation has to take place in the base API file : we dont want to leave this reponsability to user implementation
    # try:
    #     validated_data = OrdersList(data=parsed_orders)
    # except ValidationError as e:
    #     raise e


    # return validated_data
    return parsed_orders


# ================================================================================


def parse_orders_by_id(response, symbol):

    #! this is not correct anymore since we parse it after,
    #! so shoud return empty dict maybe
    if response is None:
        return OrdersByID(data={})


    # check if we received a response for closed/open/single order
    try:
        key = list(response.keys())[0]
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
    if key == "open":
        response = response["open"]
    elif key == "closed":
        response = response["closed"]
    else:
        # # the request is for a single order filtered by ID
        # response = response[key]
        pass

    try:
        parsed_orders = {

            key: parse_single_order(key, info) for key, info in response.items()
        }

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


    # try:
    #     validated_data = OrdersByID(data=parsed_orders)
    # except ValidationError as e:
    #     raise e

    return parsed_orders



def parse_single_order(key, value):
    info = value
    map_to_standard = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]
    # map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    try:
        parsed_info = {

            "orderID": key,
            "symbol": map_to_standard[info["descr"]["pair"].upper()],
            "currency": map_to_standard[info["descr"]["pair"].upper()].split("-")[1],
            "side": info["descr"]["type"],
            "ordType": info["descr"]["ordertype"],
            "execInst": None,

            "clOrdID": info["userref"],
            "account": None,
            "cashMargin": "cash" if (info["descr"]["leverage"] == "none") else "margin",
            "marginRatio": 0 if info["descr"]["leverage"] == "none" else 1/int(info["descr"]["leverage"][0]),
            "marginAmt": 0 if info["descr"]["leverage"] == "none" else Decimal(info["cost"])/int(info["descr"]["leverage"][0]),
            "ordStatus": MAP_ORDER_STATUS[info["status"]],
            "workingIndicator": True if (info["status"] in ["pending", "open"]) else False,
            "ordRejReason": info.get("reason", None),

            "timeInForce": None,
            "transactTime": info["closetm"]*10**9 if "closetm" in info else None,
            "sendingTime": None,
            "effectiveTime": info["opentm"]*10**9,
            "validUntilTime": None,
            "expireTime": None if info["expiretm"] == 0 else info["expiretm"]*10**9,

            "displayQty": None,
            "grossTradeAmt": info["cost"],
            "orderQty": info["vol"],
            "cashOrderQty": info["cost"],
            "orderPercent": None,
            "cumQty": info["vol_exec"],
            "leavesQty": Decimal(info["vol"]) - Decimal(info["vol_exec"]),

            "price": info["descr"]["price"],
            "stopPx": info["stopprice"],
            "avgPx": info["price"],

            "fills": None,
            "commission": info["fee"],

            "targetStrategy": None,
            "targetStrategyParameters": None,

            "text": {
                "misc": info["misc"],
                "flags": info["oflags"]
            }

        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_info



# ================================================================================


# EXAMPLE OF OPEN ORDERS RESPONSE:

# {
#     "OTCJRA-SZYUP-LBLOTQ": {
#         "refid": null,
#         "userref": 0,
#         "status": "open",
#         "opentm": 1587243440.5982,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "ETHUSD",
#         "type": "buy",
#         "ordertype": "limit",
#         "price": "98.58",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 2.34154630 ETHUSD @ limit 98.58",
#         "close": ""
#         },
#         "vol": "2.34154630",
#         "vol_exec": "0.00000000",
#         "cost": "0.00000",
#         "fee": "0.00000",
#         "price": "0.00000",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     },

#     "OS5GER-FI6DI-VWXUD4": {
#         "refid": null,
#         "userref": 0,
#         "status": "open",
#         "opentm": 1587242256.38,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "ETHUSD",
#         "type": "buy",
#         "ordertype": "limit",
#         "price": "130.34",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 5.00000000 ETHUSD @ limit 130.34",
#         "close": ""
#         },
#         "vol": "5.00000000",
#         "vol_exec": "0.00000000",
#         "cost": "0.00000",
#         "fee": "0.00000",
#         "price": "0.00000",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     },

#     "O5TYA6-EC2HN-KJ65ZG": {
#         "refid": null,
#         "userref": 0,
#         "status": "open",
#         "opentm": 1587240556.5647,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "ETHUSD",
#         "type": "buy",
#         "ordertype": "limit",
#         "price": "130.00",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 5.00000000 ETHUSD @ limit 130.00",
#         "close": ""
#         },
#         "vol": "5.00000000",
#         "vol_exec": "0.00000000",
#         "cost": "0.00000",
#         "fee": "0.00000",
#         "price": "0.00000",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     }
# }

# ================================================================================


# EXAMPLE OF CLOSED ORDERS RESPONSE:

# {
#     "O6Z37Y-IJ8KM-3WTRHX": {
#         "refid": null,
#         "userref": 0,
#         "status": "closed",
#         "reason": null,
#         "opentm": 1587571229.0971,
#         "closetm": 1587571229.1034,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "XBTUSD",
#         "type": "buy",
#         "ordertype": "market",
#         "price": "0",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 0.97694688 XBTUSD @ market",
#         "close": ""
#         },
#         "vol": "0.97694688",
#         "vol_exec": "0.97694688",
#         "cost": "6974.7",
#         "fee": "13.9",
#         "price": "7139.3",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     },

#     "O2A4D7-BYTBN-72R6CB": {
#         "refid": null,
#         "userref": 0,
#         "status": "closed",
#         "reason": null,
#         "opentm": 1587571224.7359,
#         "closetm": 1587571224.7396,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "ETHUSD",
#         "type": "buy",
#         "ordertype": "market",
#         "price": "0",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 47.51731923 ETHUSD @ market",
#         "close": ""
#         },
#         "vol": "47.51731923",
#         "vol_exec": "47.51731923",
#         "cost": "8742.71",
#         "fee": "17.48",
#         "price": "183.99",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     },

#     "OOSVOF-IMYUY-VZ45FL": {
#         "refid": null,
#         "userref": null,
#         "status": "canceled",
#         "reason": "User requested",
#         "opentm": 1586962804.0969,
#         "closetm": 1586964015.8981,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "XBTUSD",
#         "type": "buy",
#         "ordertype": "limit",
#         "price": "1000.0",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 0.02100000 XBTUSD @ limit 1000.0",
#         "close": ""
#         },
#         "vol": "0.02100000",
#         "vol_exec": "0.00000000",
#         "cost": "0.00000",
#         "fee": "0.00000",
#         "price": "0.00000",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     },
#     "OFEROZ-DQ6S4-KF78MV": {
#         "refid": null,
#         "userref": null,
#         "status": "canceled",
#         "reason": "User requested",
#         "opentm": 1586962846.4656,
#         "closetm": 1586964015.5331,
#         "starttm": 0,
#         "expiretm": 0,
#         "descr": {
#         "pair": "XBTUSD",
#         "type": "buy",
#         "ordertype": "limit",
#         "price": "1000.0",
#         "price2": "0",
#         "leverage": "none",
#         "order": "buy 0.02100000 XBTUSD @ limit 1000.0",
#         "close": ""
#         },
#         "vol": "0.02100000",
#         "vol_exec": "0.00000000",
#         "cost": "0.00000",
#         "fee": "0.00000",
#         "price": "0.00000",
#         "stopprice": "0.00000",
#         "limitprice": "0.00000",
#         "misc": "",
#         "oflags": "fciq"
#     }
# }
