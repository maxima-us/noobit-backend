from decimal import Decimal

from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)


def parse_trades_to_list(message):

    pair = message[3]

    try:
        parsed_trades = [
            parse_single_trade(info, pair) for info in message[1]
        ]
    except Exception as e:
        log_exception(logger, e)

    if parsed_trades:
        return parsed_trades



def parse_single_trade(info, pair):
    "parse single item of the list of trade"

    try:
        parsed_trade = {
            "trdMatchID": None,
            "orderID": None,
            "symbol": pair.replace("/", "-"),
            "side": "buy" if (info[3] == "b") else "sell",
            "ordType": "market" if (info[4] == "m") else "limit",
            "avgPx": info[0],
            "cumQty": info[1],
            "grossTradeAmt": Decimal(info[0]) * Decimal(info[1]),
            "transactTime": Decimal(info[2])*10**9,
        }

    except Exception as e:
        log_exception(logger, e)

    return parsed_trade


# KRAKEN STREAM FORMAT (FROM DOC)

# channelID: integer   ChannelID of pair-trade subscription
# Array	array
#   Array	array
#    price	float	Price
#    volume	float	Volume
#    time	float	Time, seconds since epoch
#    side	string	Triggering order side, buy/sell
#    orderType	string	Triggering order type market/limit
#    misc	string	Miscellaneous
# channelName:	string	Channel Name of subscription
# pair:	string	Asset pair


# EXAMPLE
# [
#   0,
#   [
#     [
#       "5541.20000",
#       "0.15850568",
#       "1534614057.321597",
#       "s",
#       "l",
#       ""
#     ],
#     [
#       "6060.00000",
#       "0.02455000",
#       "1534614057.324998",
#       "b",
#       "l",
#       ""
#     ]
#   ],
#   "trade",
#   "XBT/USD"
# ]