from noobit.server import settings

def parse_ohlc(symbol, timeframe):

    map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    payload = {
        "pair": map_to_exchange[symbol.upper()],
        "interval": int(timeframe)
    }

    return payload



# KRAKEN INPUT FORMAT (FROM DOC)

# pair = asset pair to get OHLC data for
# interval = time frame interval in minutes (optional):
# 	1 (default), 5, 15, 30, 60, 240, 1440, 10080, 21600
# since = return committed OHLC data since given id (optional.  exclusive)