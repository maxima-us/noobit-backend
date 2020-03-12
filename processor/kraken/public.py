import asyncio
import uvloop
import websockets
import logging
import httpx
import aioredis
import ujson
import stackprinter
from collections import deque

from server.crypto_api.api import Api


public_ws_url = "wss://ws.kraken.com"
private_ws_url = "wss://ws-auth.kraken.com"


# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================



class KrakenPublicFeedReader:


    def __init__(self, feeds: list=["spread", "trade", "ohlc", "book", "ticker"], 
                       book_depth: int=10,
                       ohlc_tf: int=1,
                       ws_uri: str=public_ws_url,
                       ):

        self.ws_uri = ws_uri
        self.feeds = feeds
        self.book_depth = book_depth
        self.ohlc_tf = ohlc_tf
        
        self.redis = None


    async def serve(self, ping_interval: int=60, ping_timeout: int=30):

        self.redis = await aioredis.create_redis_pool('redis://localhost')

        async with websockets.connect(uri=self.ws_uri,
                                      ping_interval=ping_interval,
                                      ping_timeout=ping_timeout
                                      ) as ws:

            for feed in self.feeds:
                
                try:
                    data = {"event": "subscribe", "subscription": {"name": feed}}

                    if feed == "book":
                        data["subscription"]["depth"] = self.book_depth
                    
                    if feed == "ohlc":
                        data["subscription"]["interval"] = self.ohlc_tf

                    payload = ujson.dumps(data) 
                    await ws.send(payload)
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logging.error(stackprinter.format(e, style="darkbg2"))
            # end for             


            async for msg in ws:
                await self.ws_msg_handler(msg)
            # end for 


            self.redis.close()
            await self.redis.wait_closed()



    async def ws_msg_handler(self, msg):

        if "subscription" in msg:
            # msg = ujson.loads(msg)
            self.redis.publish("status", msg)

        elif "event" in msg:
            # msg = ujson.loads(msg)
            self.redis.publish("events", msg)
        
        else : 
            msg = ujson.loads(msg)
            data = msg[0]
            feed = msg[1]
            self.redis.publish(f"data:{feed}", ujson.dumps(data))


    def run(self):
        uvloop.install()
        asyncio.run(self.serve())




# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



