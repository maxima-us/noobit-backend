import asyncio
import uvloop
import websockets
import logging
import httpx
import ujson
import stackprinter
from collections import deque

from exchanges import rest_api_map

public_ws_url = "wss://ws.kraken.com"
private_ws_url = "wss://ws-auth.kraken.com"


# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================
# ================================================================================



class KrakenPrivateFeedReader(object):


    def __init__(self, 
                       feeds: list=["openOrders", "ownTrades"], 
                       ws_uri: str="wss://ws-auth.kraken.com",
                       loop=None
                       ):

        self.ws_uri = ws_uri
        self.feeds = feeds
        self.api = rest_api_map["kraken"]()
        self.api.session = httpx.AsyncClient() 
        self.filtered_msgs = {}
       
        self.filtered_msgs["events"] = deque()
        self.filtered_msgs["status"] = deque()
        
        for feed in feeds :
            self.filtered_msgs[feed] = deque()



    async def serve(self, ping_interval: int=60, ping_timeout: int=30):

        async with websockets.connect(uri=self.ws_uri,
                                      ping_interval=ping_interval,
                                      ping_timeout=ping_timeout
                                      ) as ws:

            ws_token = await self.api.get_websocket_auth_token()

            for feed in self.feeds:

                try:
                    data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
                    payload = ujson.dumps(data) 
                    await ws.send(payload)
                    await asyncio.sleep(0.1)
                
                except Exception as e:
                    logging.error(stackprinter.format(e, style="darkbg2"))
            
            # async for msg in ws:
            #     # await self.ws_msg_handler(msg)
            #     print(msg)
            while 1:
                msg = await ws.recv()
                print(msg)



            
    async def ws_msg_handler(self, msg):
        if "subscription" in msg:
            msg = ujson.loads(msg)
            self.filtered_msgs["status"].append(msg) 
            print("sub: ", msg)

        elif "event" in msg:
            msg = ujson.loads(msg)
            self.filtered_msgs["events"].append(msg)
            print("event: ",msg) 

        else : 
            msg = ujson.loads(msg)
            data = msg[0]
            feed = msg[1]
            self.filtered_msgs[feed].append(data)
            print("data :", msg) 


    def run(self):
        uvloop.install()
        asyncio.run(self.serve())


if __name__ == "__main__":

    kraken = KrakenPrivateFeedReader()
    kraken.run()