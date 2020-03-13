import os
import signal,sys,time                          
import asyncio
import websockets
import logging

import httpx
import ujson
import stackprinter
from collections import deque

from exchanges.mappings import rest_api_map
from exchanges.base.websockets.private import BasePrivateFeedReader


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




class KrakenPrivateFeedReader(BasePrivateFeedReader):


    def __init__(self, feeds: list=["openOrders", "ownTrades"], 
                       ws_uri: str="wss://ws-auth.kraken.com",
                       ):

        self.exchange = "kraken"
        self.ws_uri = ws_uri
        self.feeds = feeds
        self.api = rest_api_map["kraken"]()
        self.api.session = httpx.AsyncClient()
        self.ws = None
        self.terminate = False
    
    
    async def subscribe(self, ping_interval: int, ping_timeout: int):
        """Subscribe to websocket
        """

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


        print(self.ws)
    

    def msg_handler(self, msg, redis_pool):

        if "systemStatus" in msg:
            msg = ujson.loads(msg)
            # We need to replace keys so they correspond to our datamodel
            msg["connection_id"] = msg.pop("connectionID")
            self.publish_systemstatus(msg, redis_pool)

        elif "subscription" in msg:
            msg = ujson.loads(msg)
            # We need to replace keys so they correspond to our datamodel
            msg["channel_name"] = msg.pop("channelName")
            #redis_pool.publish("status", msg)
            self.publish_status(msg, redis_pool)
            # call some method from base class instead, that method will then check the type

        elif "heartbeat" in msg:
            msg = ujson.loads(msg)
            # redis_pool.publish("events", msg)
            self.publish_heartbeat(msg, redis_pool)
        
        else : 
            msg = ujson.loads(msg)
            data = msg[0]
            feed = msg[1]
            # redis_pool.publish(f"data:{feed}", ujson.dumps(data))
            self.publish_data(data, feed, redis_pool)

    

# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



