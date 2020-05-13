import logging
from decimal import Decimal

import stackprinter


def parse_exposure(response):
    try:
        parsed_exposure = {
            "totalNetValue": response["eb"],
            "marginExcess": response["mf"],

            "marginAmt": response["m"],
            "marginRatio": 1/Decimal(response["ml"]),
            "unrealisedPnL": response["n"],
        }
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))

    return parsed_exposure




# eb = equivalent balance (combined balance of all currencies)
# tb = trade balance (combined balance of all equity currencies)
# m = margin amount of open positions
# n = unrealized net profit/loss of open positions
# c = cost basis of open positions
# v = current floating valuation of open positions
# e = equity = trade balance + unrealized net profit/loss
# mf = free margin = equity - initial margin (maximum margin available to open new positions)
# ml = margin level = (equity / initial margin) * 100