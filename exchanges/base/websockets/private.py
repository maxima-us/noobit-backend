import os
import signal,sys,time                          
import asyncio
import logging
from typing import List
from abc import ABC, abstractmethod

import uvloop
import websockets
import httpx
import aioredis
import ujson
import stackprinter
from collections import deque


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




class BasePrivateFeedReader(ABC):

    """Base Class for Websocket Feed Readers
    Makes sure all the data the websockets send to redis is normalized

    Notes :

        Example of Init :
            self.exchange = exchange.lower()
            self.feeds = feeds
            self.ws_uri = ws_uri
            self.api = rest_api_map[self.exchange]()
            self.api.session = httpx.AsyncClient() 
            self.open_ws = None
            self.redis = None
            self.terminate = False
    """


    # ==> MAIN PROCESSOR HAS TO SERVE, EVENTUALLY HAS TO BE ABLE TO SERVE MULTIPLE FEEDREADERS

    # async def serve(self, ping_interval: int=60, ping_timeout: int=30):

    #     process_id = os.getpid()
    #     print(f"Started process {process_id}")
    #     self.install_signal_handlers()


    #     self.redis = await aioredis.create_redis_pool('redis://localhost')
    #     await self.subscribe(ping_interval, ping_timeout) 

    #     while not self.terminate:
    #         await self.process_feed()

    #     print("Shutting down")
    #     print("Closing redis")
    #     self.redis.close()
    #     await self.redis.wait_closed()
    #     print("Closing websocket connection")
    #     await self.ws.close()
    #     print("Shutdown complete")


    # ==> THIS IS PROBABLY TOO SPECIFIC TO EACH EXCHANGE

    # async def subscribe(self, ping_interval: int, ping_timeout: int):

    #     self.ws = await websockets.connect(uri=self.ws_uri,
    #                                        ping_interval=ping_interval,
    #                                        ping_timeout=ping_timeout
    #                                        )

    #     ws_token = await self.api.get_websocket_auth_token()


    #     for feed in self.feeds:
    #         try:
    #             data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
    #             payload = ujson.dumps(data) 
    #             await self.ws.send(payload)
    #             await asyncio.sleep(0.1)
            
    #         except Exception as e:
    #             logging.error(stackprinter.format(e, style="darkbg2"))

    @abstractmethod
    async def subscribe(self, ping_interval: int, ping_timeout: int):
        raise NotImplementedError


    async def process_feed(self, redis_pool):
        """Receive message from feed and process them

        Args:
            redis_pool: instance returned from aioredis.create_redis_pool
        """
        try:
            msg = await self.ws.recv()
            await self.msg_handler(msg, redis_pool)
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    @abstractmethod
    async def msg_handler(self, msg, redis_pool):
        raise NotImplementedError
    


# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



