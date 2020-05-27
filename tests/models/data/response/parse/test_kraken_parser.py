import logging
from decimal import Decimal

import ujson
import stackprinter
from pydantic import ValidationError

from noobit.models.data.response.order import OrdersList, OrdersByID
from noobit.models.data.response.parse.kraken import KrakenResponseParser


response = '''{"open": {

    "O3R75Y-IYUB4-Y65GXU": {
        "refid": null,
        "userref": 0,
        "status": "closed",
        "reason": null,
        "opentm": 1587571229.0971,
        "closetm": 1587571229.1034,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
        "pair": "XBTUSD",
        "type": "buy",
        "ordertype": "market",
        "price": "0",
        "price2": "0",
        "leverage": "none",
        "order": "buy 0.97694688 XBTUSD @ market",
        "close": ""
        },
        "vol": "0.97694688",
        "vol_exec": "0.97694688",
        "cost": "6974.7",
        "fee": "13.9",
        "price": "7139.3",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq"
    },

    "O2T65U-YYTRC-435TXD": {
        "refid": null,
        "userref": 0,
        "status": "closed",
        "reason": null,
        "opentm": 1587571224.7359,
        "closetm": 1587571224.7396,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
        "pair": "ETHUSD",
        "type": "buy",
        "ordertype": "market",
        "price": "0",
        "price2": "0",
        "leverage": "none",
        "order": "buy 47.51731923 ETHUSD @ market",
        "close": ""
        },
        "vol": "47.51731923",
        "vol_exec": "47.51731923",
        "cost": "8742.71",
        "fee": "17.48",
        "price": "183.99",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq"
    },

    "OFDSJF-I9FY5-VFWC4L": {
        "refid": null,
        "userref": null,
        "status": "canceled",
        "reason": "User requested",
        "opentm": 1586962804.0969,
        "closetm": 1586964015.8981,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
        "pair": "XBTUSD",
        "type": "buy",
        "ordertype": "limit",
        "price": "1000.0",
        "price2": "0",
        "leverage": "none",
        "order": "buy 0.02100000 XBTUSD @ limit 1000.0",
        "close": ""
        },
        "vol": "0.02100000",
        "vol_exec": "0.00000000",
        "cost": "0.00000",
        "fee": "0.00000",
        "price": "0.00000",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq"
    },
    "OFR45U-WCT05-TF6IJO": {
        "refid": null,
        "userref": null,
        "status": "canceled",
        "reason": "User requested",
        "opentm": 1586962846.4656,
        "closetm": 1586964015.5331,
        "starttm": 0,
        "expiretm": 0,
        "descr": {
        "pair": "XBTUSD",
        "type": "buy",
        "ordertype": "limit",
        "price": "1000.0",
        "price2": "0",
        "leverage": "none",
        "order": "buy 0.02100000 XBTUSD @ limit 1000.0",
        "close": ""
        },
        "vol": "0.02100000",
        "vol_exec": "0.00000000",
        "cost": "0.00000",
        "fee": "0.00000",
        "price": "0.00000",
        "stopprice": "0.00000",
        "limitprice": "0.00000",
        "misc": "",
        "oflags": "fciq"
    }
}
}'''


def test_parse_order_response_to_list(response=response, symbol=None, mode="to_list"):

    resp_parser = KrakenResponseParser()

    try:
        response = ujson.loads(response)
        parsed_list = resp_parser.orders(response, mode, symbol)
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    assert isinstance(parsed_list, list)

    try:
        validated = OrdersList(data=parsed_list)
    except ValidationError as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    assert isinstance(validated.data, list), validated.data
    assert isinstance(validated.data[0].orderQty, Decimal), validated.data



def test_parse_order_response_by_id(response=response, symbol=None, mode="by_id"):

    resp_parser = KrakenResponseParser()

    try:
        response = ujson.loads(response)
        parsed_dict = resp_parser.orders(response, mode, symbol)
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    assert isinstance(parsed_dict, dict)

    try:
        validated = OrdersByID(data=parsed_dict)
        print(validated.data)
    except ValidationError as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    assert isinstance(validated.data, dict), validated.data
