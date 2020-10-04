"""
Dispatch messages coming in from private websocket connections
to appropriate redis channel
"""
from typing import List
from typing_extensions import Literal
import websockets

import ujson


# base classes
from noobit.exchanges.base.websockets import BasePrivateFeedReader

# models
from noobit.models.data.base.types import PAIR, WS_ROUTE

# parser
from noobit.models.data.websockets.stream.parse.kraken import KrakenStreamParser
from noobit.models.data.websockets.subscription.parse.kraken import KrakenSubParser
from noobit.models.data.websockets.unsubscription.parse.kraken import KrakenUnsubParser


class KrakenPrivateFeedReader(BasePrivateFeedReader):


    def __init__(self, ws: websockets.WebSocketClientProtocol = None):

        self.exchange = "kraken"
        self.ws_uri = "wss://ws-auth.kraken.com"

        self.subscription_parser = KrakenSubParser()
        self.unsubscription_parser = KrakenUnsubParser()
        self.stream_parser = KrakenStreamParser()

        super().__init__(ws)



    async def route_message(self, msg) -> Literal[WS_ROUTE]:
        """
        forward to appropriate parser and eventually publish
        to redis channel
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
            feed = msg[1]

            if feed == "ownTrades":
                route = "trade"

            if feed == "openOrders":
                route = "order"

            return route
