from noobit.server import settings

def parse_orderbook(symbol):

    map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    payload = {
        "pair": map_to_exchange[symbol.upper()]
    }

    return payload



# KRAKEN INPUT FORMAT (FROM DOC)
# pair = asset pair to get market depth for
# count = maximum number of asks/bids (optional)