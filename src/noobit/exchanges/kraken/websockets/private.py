"""
Dispatch messages coming in from private websocket connections
to appropriate redis channel
"""
from typing import List
from typing_extensions import Literal

import ujson


# base classes
from noobit.exchanges.base.websockets import BasePrivateFeedReader

# models
from noobit.models.data.base.types import PAIR, WS_ROUTE

# parser
from noobit.models.data.websockets.stream.parse.kraken import KrakenStreamParser
from noobit.models.data.websockets.subscription.parse.kraken import KrakenSubParser


class KrakenPrivateFeedReader(BasePrivateFeedReader):


    def __init__(self,
                 pairs: List[PAIR],
                 feeds: List[str] = ["trade", "order"]
                 ):

        self.exchange = "kraken"
        self.ws_uri = "wss://ws-auth.kraken.com"

        self.subscription_parser = KrakenSubParser()
        self.stream_parser = KrakenStreamParser()

        super().__init__(pairs=pairs, feeds=feeds)



    async def route_message(self, msg) -> Literal[WS_ROUTE]:
        """
        forward to appropriate parser and eventually publish
        to redis channel
        """

        if "systemStatus" in msg:
            route = "system_status"
            return route

        elif "subscription" in msg:
            route = "subscription_status"
            return route

        elif "heartbeat" in msg:
            route = "heartbeat"
            return route

        else:
            msg = ujson.loads(msg)
            feed = msg[1]

            if feed == "ownTrades":
                route = "trade"

            if feed == "openOrders":
                route = "order"

            return route
