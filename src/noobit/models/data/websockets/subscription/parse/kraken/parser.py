import asyncio

import httpx

from noobit.logger.structlogger import get_logger, log_exception
from noobit.exchanges.mappings import rest_api_map
from noobit.models.data.websockets.subscription.parse.base import BaseSubParser


logger = get_logger(__name__)

class KrakenSubParser(BaseSubParser):


    async def public(self, symbol, timeframe, depth, feed):

        map_to_exchange = {
            "orderbook": "book",
            "instrument": "ticker",
            "trade": "trade",
            "ohlc": "ohlc",
            "spread": "spread"
        }

        try:
            data = {"event": "subscribe", "pair": [symbol.replace("-", "/")], "subscription": {"name": map_to_exchange[feed]}}
            if feed == "ohlc":
                data["subscription"]["interval"] = timeframe
            if feed == "book":
                data["subscription"]["depth"] = depth

            return data

        except Exception as e:
            log_exception(logger, e)
            raise


    async def private(self, feed):

        map_to_exchange = {
            "order": "openOrders",
            "trade": "ownTrades",
        }

        try:
            api = rest_api_map["kraken"]()
            async with httpx.AsyncClient() as api.session:
                ws_token = await api.get_websocket_auth_token()
            data = {"event": "subscribe", "subscription": {"name": map_to_exchange[feed], "token": ws_token.value["token"]}}
            return data

        except Exception as e:
            log_exception(logger, e)
            raise