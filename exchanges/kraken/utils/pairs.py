import httpx
import logging
import stackprinter

PAIR_SEP = '-'

async def kraken_pairs(client: httpx.AsyncClient):
    ret = {}
    r = await client.get('https://api.kraken.com/0/public/AssetPairs')
    data = r.json()
    for pair in data['result']:
        alt = data['result'][pair]['altname']

        if ".d" in alt:
            # https://blog.kraken.com/post/259/introducing-the-kraken-dark-pool/
            # .d is for dark pool pairs
            continue

        normalized = alt[:-3] + PAIR_SEP + alt[-3:]
        exch = normalized.replace(PAIR_SEP, "/")
        normalized = normalized.replace('XBT', 'BTC')
        normalized = normalized.replace('XDG', 'DOG')
        ret[normalized] = exch

    return ret


def normalize_currency(currency: str):

    # assert len(currency)==4

    if currency[0] in ["X", "Z"]:
        return currency[1:4]

    else:
        return currency


def normalize_pair(pair: str):

    try:
        base = pair[1:4]
        quote = pair[5:9]

        return f'{base}-{quote}'

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))


def kraken_format_pair(normalized_pair: str):

    try:
        n_base, n_quote = normalized_pair.split("-")
        return f"X{n_base.upper()}Z{n_quote.upper()}"
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))
