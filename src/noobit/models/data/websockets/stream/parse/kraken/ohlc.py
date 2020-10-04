from decimal import Decimal

from noobit.logger.structlogger import get_logger, log_exception

logger = get_logger(__name__)


def parse_ohlc(message):
    symbol = message[-1].replace("/", "-")
    ohlc = message[1]
    try:
        parsed_ohlc = {
            "symbol": symbol,
            "utcTime": float(ohlc[0])*10**9,
            "open": Decimal(ohlc[2]),
            "high": Decimal(ohlc[3]),
            "low": Decimal(ohlc[4]),
            "close": Decimal(ohlc[5]),
            "volume": Decimal(ohlc[7]),
            "trdCount": Decimal(ohlc[8])
        }
        return parsed_ohlc
    except Exception as e:
        log_exception(logger, e)


# EXAMPLE PAYLOAD
# [
#   42,
#   [
#     "1542057314.748456",
#     "1542057360.435743",
#     "3586.70000",
#     "3586.70000",
#     "3586.60000",
#     "3586.60000",
#     "3586.68894",
#     "0.03373000",
#     2
#   ],
#   "ohlc-5",
#   "XBT/USD"
# ]