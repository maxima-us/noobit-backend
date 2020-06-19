from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)

def parse_instrument(msg):

    pair = msg[3].replace("/", "-")

    info = msg[1]

    try:
        parsed_instrument = {
            "symbol": pair,
            "low": info["l"][0],
            "high": info["h"][0],
            "vwap": info["p"][0],
            "last": info["c"][0],

            "volume": info["v"][0],
            "trdCount": info["t"][0],

            "bestAsk": {info["a"][0]: info["a"][2]},
            "bestBid": {info["b"][0]: info["b"][2]},

            "prevLow": info["l"][1],
            "prevHigh": info["h"][1],
            "prevVwap": info["p"][1],
            "prevVolume": info["v"][1],
            "prevTrdCount": info["t"][1]
        }

    except Exception as e:
        log_exception(logger, e)

    return parsed_instrument

# DATA FORMAT (FROM DOC):
# a	array	Ask
#    price	float	Best ask price
#    wholeLotVolume	integer	Whole lot volume
#    lotVolume	float	Lot volume
#   b	array	Bid
#    price	float	Best bid price
#    wholeLotVolume	integer	Whole lot volume
#    lotVolume	float	Lot volume
#   c	array	Close
#    price	float	Price
#    lotVolume	float	Lot volume
#   v	array	Volume
#    today	float	Value today
#    last24Hours	float	Value over last 24 hours
#   p	array	Volume weighted average price
#    today	float	Value today
#    last24Hours	float	Value over last 24 hours
#   t	array	Number of trades
#    today	integer	Value today
#    last24Hours	integer	Value over last 24 hours
#   l	array	Low price
#    today	float	Value today
#    last24Hours	float	Value over last 24 hours
#   h	array	High price
#    today	float	Value today
#    last24Hours	float	Value over last 24 hours
#   o	array	Open Price
#    today	float	Value today
#    last24Hours	float	Value over last 24 hours

# EXAMPLE OF MESSAGE:
# [
#   0,
#   {
#     "a": [
#       "5525.40000",
#       1,
#       "1.000"
#     ],
#     "b": [
#       "5525.10000",
#       1,
#       "1.000"
#     ],
#     "c": [
#       "5525.10000",
#       "0.00398963"
#     ],
#     "h": [
#       "5783.00000",
#       "5783.00000"
#     ],
#     "l": [
#       "5505.00000",
#       "5505.00000"
#     ],
#     "o": [
#       "5760.70000",
#       "5763.40000"
#     ],
#     "p": [
#       "5631.44067",
#       "5653.78939"
#     ],
#     "t": [
#       11493,
#       16267
#     ],
#     "v": [
#       "2634.11501494",
#       "3591.17907851"
#     ]
#   },
#   "ticker",
#   "XBT/USD"
# ]