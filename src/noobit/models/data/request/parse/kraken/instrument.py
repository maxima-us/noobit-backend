from noobit.server import settings

def parse_instrument(symbol):

    map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]

    payload = {
        "pair": map_to_exchange[symbol.upper()]
    }

    return payload



# KRAKEN INPUT FORMAT (FROM DOC)
# pair = comma delimited list of asset pairs to get info on