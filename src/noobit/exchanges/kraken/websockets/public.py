from typing import List
from typing_extensions import Literal

import ujson


# base classes
from noobit.exchanges.base.websockets import BasePublicFeedReader

# models
from noobit.models.data.base.types import TIMEFRAME, PAIR, WS_ROUTE

# parser
from noobit.models.data.websockets.stream.parse.kraken import KrakenStreamParser
from noobit.models.data.websockets.subscription.parse.kraken import KrakenSubParser


class KrakenPublicFeedReader(BasePublicFeedReader):


    def __init__(self,
                 pairs: List[PAIR],
                 timeframe: TIMEFRAME = 1,
                 depth: int = 10,
                 feeds: List[str] = ["instrument", "trade", "orderbook"]
                 ):

        self.exchange = "kraken"
        self.ws_uri = "wss://ws.kraken.com"

        self.subscription_parser = KrakenSubParser()
        self.stream_parser = KrakenStreamParser()

        super().__init__(pairs=pairs, timeframe=timeframe, depth=depth, feeds=feeds)



    async def route_message(self, msg) -> Literal[WS_ROUTE]:
        """
        forward to appropriate parser ==> redis channel
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
            feed = msg[2]

            if feed == "ticker":
                route = "instrument"

            if feed == "ohlc":
                route = "ohlc"

            if feed == "spread":
                route = "spread"

            if "book" in feed:
                route = "orderbook"

            if feed == "trade":
                route = "trade"

            return route
