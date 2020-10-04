from typing import List
from typing_extensions import Literal
import websockets

import ujson


# base classes
from noobit.exchanges.base.websockets import BasePublicFeedReader

# models
from noobit.models.data.base.types import TIMEFRAME, PAIR, WS

# parser
from noobit.models.data.websockets.stream.parse.kraken import KrakenStreamParser
from noobit.models.data.websockets.subscription.parse.kraken import KrakenSubParser
from noobit.models.data.websockets.unsubscription.parse.kraken import KrakenUnsubParser


class KrakenPublicFeedReader(BasePublicFeedReader):


    def __init__(self, ws: websockets.WebSocketClientProtocol = None):

        self.exchange = "kraken"
        self.ws_uri = "wss://ws.kraken.com"

        self.subscription_parser = KrakenSubParser()
        self.unsubscription_parser = KrakenUnsubParser()
        self.stream_parser = KrakenStreamParser()

        super().__init__(ws)



    async def route_message(self, msg) -> WS:
        """
        forward to appropriate parser ==> redis channel
        """

        if "systemStatus" in msg:
            route = "connection_status"
            return route

        elif "subscription" in msg:
            route = "subscription_status"
            return route

        elif "heartbeat" in msg:
            route = "heartbeat"
            return route

        else:
            msg = ujson.loads(msg)
            feed = msg[-2]

            if feed == "ticker":
                route = "instrument"

            if feed.startswith("ohlc"):
                route = "ohlc"

            if feed == "spread":
                route = "spread"

            if feed.startswith("book"):
                route = "orderbook"

            if feed == "trade":
                route = "trade"

            return route
