from noobit.server import settings

def parse_public_trades(symbol, since):

    map_to_exchange = settings.SYMBOL_MAP_TO_EXCHANGE["KRAKEN"]
    if since is None:
        since = "null"

    payload = {
        "pair": map_to_exchange[symbol.upper()],
        "since": since
    }

    return payload

# KRAKEN INPUT FORMAT (FROM DOC)
# pair = asset pair to get trade data for
# since = return trade data since given id (optional.  exclusive)