from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)


def parse_orderbook(message):

    info = message[1]
    pair = message[3].replace("/", "-")

    #! we could possibly be a lot more efficient if we count the messages we have received from each channel
    #! so we dont need to do an if check every time
    if "as" in info:
        # message is snaptshot
        return parse_snapshot(info, pair)

    else:
        # message is update
        return parse_update(info, pair)


def parse_snapshot(info, pair):

    try:
        parsed_snapshot = {
            "symbol": pair,
            "asks": {
                item[0]: item[1] for item in info["as"]
            },
            "bids": {
                item[0]: item[1] for item in info["bs"]
            },
            "is_snapshot": True,
            "is_update": False
        }

    except Exception as e:
        log_exception(logger, e)

    return parsed_snapshot



def parse_update(info, pair):

    keys = list(info.keys())
    # logging.warning(keys)


    try:
        parsed_update = {
            "symbol": pair,
            "asks": {
                item[0]: item[1] for item in info["a"]
            } if "a" in keys else {},
            "bids": {
                item[0]: item[1] for item in info["b"]
            } if "b" in keys else {},
            "is_snapshot": False,
            "is_update": True
        }

    except Exception as e:
        log_exception(logger, e)

    return parsed_update







# EXAMPLE OF SNAPSHOT MESSAGE
# [
#   0,
#   {
#     "as": [
#       [
#         "5541.30000",
#         "2.50700000",
#         "1534614248.123678"
#       ],
#       [
#         "5541.80000",
#         "0.33000000",
#         "1534614098.345543"
#       ],
#       [
#         "5542.70000",
#         "0.64700000",
#         "1534614244.654432"
#       ]
#     ],
#     "bs": [
#       [
#         "5541.20000",
#         "1.52900000",
#         "1534614248.765567"
#       ],
#       [
#         "5539.90000",
#         "0.30000000",
#         "1534614241.769870"
#       ],
#       [
#         "5539.50000",
#         "5.00000000",
#         "1534613831.243486"
#       ]
#     ]
#   },
#   "book-100",
#   "XBT/USD"
# ]


# EXAMPLE OF UPDATE MESSAGE
# [
#   1234,
#   {
#     "a": [
#       [
#         "5541.30000",
#         "2.50700000",
#         "1534614248.456738"
#       ],
#       [
#         "5542.50000",
#         "0.40100000",
#         "1534614248.456738"
#       ]
#     ]
#   },
#   "book-10",
#   "XBT/USD"
# ]