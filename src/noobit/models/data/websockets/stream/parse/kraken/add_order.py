
import logging

import stackprinter


def parse_add_order(validated_data, token):

    try:
        parsed_add_order = {
            "event": "addOrder",
            "token": token,
            "reqid": "null",         # check again, reqid is of type int while clOrdID is str
            "ordertype": validated_data.ordType,
            "type": validated_data.side,
            "pair": validated_data.symbol.replace("-", "/"),
            "price": validated_data.price,
            "price2": validated_data.stopPx if validated_data.stopPx else "null",
            "volume": validated_data.orderQty,
            "leverage": "null" if validated_data.marginRatio == 1 else int(1/validated_data.marginRatio),
            "oflags": "null",
            "starttm": validated_data.effectiveTime if validated_data.effectiveTime else "null",
            "expiretm": validated_data.expireTime if validated_data.expireTime else 'null',
            "userref": validated_data.clOrdID if validated_data.clOrdID else 'null',
            "validate": "false",
        }

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_add_order




# KRAKEN DOC
# event	string	addOrder
# token	string	Session token string
# reqid	integer	Optional - client originated requestID sent as acknowledgment in the message response
# ordertype	string	Order type
# type	string	Side, buy or sell
# pair	string	Currency pair
# price	float	Optional dependent on order type - order price
# price2	float	Optional dependent on order type - order secondary price
# volume	float	Order volume in lots
# leverage	float	amount of leverage desired (optional; default = none)
# oflags	string	Optional - comma delimited list of order flags. viqc = volume in quote currency (not currently available), fcib = prefer fee in base currency, fciq = prefer fee in quote currency, nompp = no market price protection, post = post only order (available when ordertype = limit)
# starttm	string	Optional - scheduled start time. 0 = now (default) +<n> = schedule start time <n> seconds from now <n> = unix timestamp of start time
# expiretm	string	Optional - expiration time. 0 = no expiration (default) +<n> = expire <n> seconds from now <n> = unix timestamp of expiration time
# userref	string	Optional - user reference ID (should be an integer in quotes)
# validate	string	Optional - validate inputs only; do not submit order (not currently available)
# close[ordertype]	string	Optional - close order type.
# close[price]	float	Optional - close order price.
# close[price2]	float	Optional - close order secondary price.
# trading_agreement	string	Optional - should be set to "agree" by German residents in order to signify acceptance of the terms of the Kraken Trading Agreement .


# WE PASS VALIDATED DATA OF FORMAT:
# data = {
#     "symbol": self.symbol,
#     "side": side,
#     "ordType": "limit",
#     "execInst": None,
#     "clOrdID": None,
#     "timeInForce": None,
#     "effectiveTime": None,
#     "expireTime": None,
#     "orderQty": 0,
#     "orderPercent": None,
#     "price": 0,
#     "stopPx": 0,
#     "targetStrategy": "mock_strat",
#     "targetStrategyParameters": None
# }

# KRAKEN PAYLOAD EXAMPLES :
# Example of payload
# {
#   "event": "addOrder",
#   "ordertype": "limit",
#   "pair": "XBT/USD",
#   "price": "9000",
#   "token": "0000000000000000000000000000000000000000",
#   "type": "buy",
#   "volume": "10"
# }
# Example of payload when conditional close order is sent

# {
#   "close[ordertype]": "limit",
#   "close[price]": "9100",
#   "event": "addOrder",
#   "ordertype": "limit",
#   "pair": "XBT/USD",
#   "price": "9000",
#   "token": "0000000000000000000000000000000000000000",
#   "type": "buy",
#   "volume": "10"
# }

