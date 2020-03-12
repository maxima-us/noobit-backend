import os
import signal,sys,time                          
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

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)

# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# terminate = False                            

# def signal_handling(signum,frame):           
#     global terminate                         
#     terminate = True                         

# signal.signal(signal.SIGINT,signal_handling) 



class KrakenPrivateFeedProducer:


    def __init__(self, feeds: list=["openOrders", "ownTrades"], 
                       ws_uri: str="wss://ws-auth.kraken.com",
                       ):

        self.ws_uri = ws_uri
        self.feeds = feeds
        self.api = Api(exchange="kraken")
        self.api.session = httpx.AsyncClient() 
        self.open_ws = None
        self.redis = None
        self.terminate = False


    async def serve(self, ping_interval: int=10, ping_timeout: int=40):

        process_id = os.getpid()
        print(f"Producer --- Started process {process_id}")
        self.install_signal_handlers()

        self.redis = await aioredis.create_redis_pool('redis://localhost')
        await self.subscribe_to_ws(ping_interval, ping_timeout) 

        while not self.terminate:
            await self.process_ws_feed()

        print("Producer --- Shutting down")
        print("Producer --- Closing redis")
        self.redis.close()
        await self.redis.wait_closed()
        print("Producer --- Closing websocket connection")
        await self.ws.close()
        print("Producer --- Shutdown complete")


    async def subscribe_to_ws(self, ping_interval: int, ping_timeout: int):

        self.ws = await websockets.connect(uri=self.ws_uri,
                                           ping_interval=ping_interval,
                                           ping_timeout=ping_timeout
                                           )

        ws_token = await self.api.get_websocket_auth_token()


        for feed in self.feeds:
            try:
                data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
                payload = ujson.dumps(data) 
                await self.ws.send(payload)
                await asyncio.sleep(0.1)
            
            except Exception as e:
                logging.error(stackprinter.format(e, style="darkbg2"))



    async def process_ws_feed(self):

        # while not self.terminate:
        msg = await self.ws.recv()
        await self.msg_handler(msg)
        await self.redis.publish("events", ujson.dumps("random test event"))


    async def msg_handler(self, msg):

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
    
    
    def install_signal_handlers(self):
        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
        except NotImplementedError as exc:
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)


    def handle_exit(self, sig, frame):
        self.terminate = True


# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



