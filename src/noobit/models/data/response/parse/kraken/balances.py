import logging

import stackprinter

from noobit.server import settings


def parse_balances(response):

    map_asset_to_noobit = settings.SYMBOL_MAP_TO_STANDARD["KRAKEN"]

    try:
        parsed_balances = {
            map_asset_to_noobit[asset]: value for asset, value in response.items() if float(value) > 0 and not asset == "KFEE"
        }

    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_balances