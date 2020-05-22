import asyncio

import stackprinter
import httpx

from noobit.exchanges.mappings import rest_api_map
from noobit.models.data.websockets.subscription.parse.base import BaseSubParser

class KrakenSubParser(BaseSubParser):


    async def public(self, pairs, timeframe, depth, feed):

        map_to_exchange = {
            "orderbook": "book",
            "instrument": "ticker",
            "trade": "trade",
            "ohlc": "ohlc"
        }

        try:
            data = {"event": "subscribe", "pair": [pair.replace("-", "/") for pair in pairs], "subscription": {"name": map_to_exchange[feed]}}
            if feed == "ohlc":
                data["subscription"]["interval"] = timeframe
            if feed == "book":
                data["subscription"]["depth"] = depth

            return data

        except Exception as e:
            raise stackprinter.format(e, style="darkbg2")



    async def private(self, pairs, feed):

        map_to_exchange = {
            "order": "openOrders",
            "trade": "ownTrades",
        }
        exchange_name = map_to_exchange[feed]
        print(exchange_name, feed)

        try:
            api = rest_api_map["kraken"]()
            async with httpx.AsyncClient() as api.session:
                ws_token = await api.get_websocket_auth_token()
            data = {"event": "subscribe", "subscription": {"name": map_to_exchange[feed], "token": ws_token.value["token"]}}
            return data

        except Exception as e:
            raise stackprinter.format(e, style="darkbg2")
