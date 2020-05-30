from decimal import Decimal

from noobit.logging.structlogger import get_logger, log_exception


logger = get_logger(__name__)



def parse_spread(message):

    try:
        parsed = {
            "symbol": message[3].replace("/", "-"),
            "bestBid": message[1][0],
            "bestAsk": message[1][1],
            "utcTime": Decimal(message[1][2]) * 10**9
        }

    except Exception as e:
        log_exception(logger, e)


    return parsed


# KRAKEN PAYLOAD EXAMPLE
# [
#   0,
#   [
#     "5698.40000",
#     "5700.00000",
#     "1542057299.545897",
#     "1.01234567",
#     "0.98765432"
#   ],
#   "spread",
#   "XBT/USD"
# ]


# KRAKEN DOC PAYLOAD FORMAT
# channelID	integer	ChannelID of pair-spreads subscription
# Array	array
#   bid	float	Bid price
#   ask	float	Ask price
#   timestamp	float	Time, seconds since epoch
#   bidVolume	float	Bid Volume
#   askVolume	float	Ask Volume
# channelName	string	Channel Name of subscription
# pair	string	Asset pair
