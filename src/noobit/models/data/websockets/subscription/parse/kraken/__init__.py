import asyncio

import ujson
import stackprinter

from noobit.server import settings


class KrakenSubParser():


    def parse(self, pairs, timeframe, depth, feed):

        map_feed_to_exchange = {
            "orderbook": "book",
            "instrument": "ticker",
            "trade": "trade",
            "ohlc": "ohlc"
        }

        try:
            data = {"event": "subscribe", "pair": [pair.replace("-", "/") for pair in pairs], "subscription": {"name": map_feed_to_exchange[feed]}}
            if feed == "ohlc":
                data["subscription"]["interval"] = timeframe
            if feed == "book":
                data["subscription"]["depth"] = depth

            return data

        except Exception as e:
            raise stackprinter.format(e, style="darkbg2")
