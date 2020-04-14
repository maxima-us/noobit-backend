import logging
import asyncio
import websockets

import ujson
import stackprinter

from noobit.exchanges.base.websockets.public import BasePublicFeedReader



class KrakenPublicFeedReader(BasePublicFeedReader):


    def __init__(self, pairs: list, timeframe: int=1, depth: int=10, feeds: list=["ticker", "trade", "book", "spread"]):

        self.exchange = "kraken"
        self.ws_uri = "wss://ws.kraken.com"
        self.feeds = feeds
        self.ws = None
        self.terminate = False
        self.feed_counters = {}

        self.pairs = pairs
        self.timeframe = timeframe
        self.depth = depth


    async def subscribe(self, ping_interval: int, ping_timeout: int):
        """Subscribe to websocket
        """

        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )


        for feed in self.feeds:
            try:
                data = {"event": "subscribe", "pair": self.pairs, "subscription": {"name": feed}}
                if feed == "ohlc":
                    data["subscription"]["interval"] = self.timeframe
                if feed == "book":
                    data["subscription"]["depth"] = self.depth
                payload = ujson.dumps(data)
                await self.ws.send(payload)
                await asyncio.sleep(0.1)

            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))


    async def close(self):
        try:
            # await self.ws.wait_closed()
            await self.ws.close()
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    async def msg_handler(self, msg, redis_pool):
        """sort messages that we receive from websocket and send them to appropriate redis chan

        Args:
            msg (str): message received from websocket
            redis_pool (object): instance returned from aioredis.create_redis_pool


        Notes :

            redis channels :
                system:exchange = status of websocket connection
                status:exchange = status of feed subscription
                heartbeat:exchange = heartbeat received every X secs
                data:exchange:feed = public or private data from ws
        """

        if "systemStatus" in msg:
            msg = ujson.loads(msg)
            # We need to replace keys so they correspond to our datamodel
            msg["connection_id"] = msg.pop("connectionID")
            await self.publish_systemstatus(msg, redis_pool)

        elif "subscription" in msg:
            msg = ujson.loads(msg)
            # We need to replace keys so they correspond to our datamodel
            msg["channel_name"] = msg.pop("channelName")
            #redis_pool.publish("status", msg)
            await self.publish_status(msg, redis_pool)
            # call some method from base class instead, that method will then check the type

        elif "heartbeat" in msg:
            msg = ujson.loads(msg)
            # redis_pool.publish("events", msg)
            await self.publish_heartbeat(msg, redis_pool)

        else:
            msg = ujson.loads(msg)
            channel_id = msg[0]
            data = msg[1]
            channel_name = msg[2]
            pair = msg[3].replace("/", "-").lower()
            # redis_pool.publish(f"data:{feed}", ujson.dumps(data))
            await self.publish_data(data, feed=channel_name, feed_id=channel_id, pair=pair, redis_pool=redis_pool)



# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



