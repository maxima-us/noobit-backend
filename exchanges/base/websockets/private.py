from models.data_models.api import OpenOrders
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
from pydantic import ValidationError

from models.data_models.websockets import HeartBeat, SubscriptionStatus
from models.data_models.websockets import HeartBeat
from models.data_models.websockets import SystemStatus
from models.data_models.websockets import OpenOrders, OwnTrades


# needs to be named exactly as the channel name from the exchange 
# TODO think about how this could work to orchestrate different exchanges
data_models_map = {"openOrders": OpenOrders,
                   "ownTrades": OwnTrades,
                  }

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
            self.msg_handler(msg, redis_pool)
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

    
    def publish_status(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"status:{self.exchange}"

        try:
            print(msg)
            subscription_status = SubscriptionStatus(**msg)
            redis_pool.publish(channel, ujson.dumps(subscription_status.dict()))

        except ValidationError as e:
            logging.error(e)


    def publish_heartbeat(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"heartbeat:{self.exchange}"

        try:
            print(msg)
            heartbeat = HeartBeat(**msg)
            redis_pool.publish(channel, ujson.dumps(heartbeat.dict()))

        except ValidationError as e:
            logging.error(e)


    def publish_systemstatus(self, msg: str, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"system:{self.exchange}"

        try:
            print(msg)
            system_status = SystemStatus(**msg)
            redis_pool.publish(channel, ujson.dumps(system_status.dict()))

        except ValidationError as e:
            logging.error(e)


    def publish_data(self, data: dict, feed: str, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"data:{self.exchange}:{feed}"

        try:
            #!  how to we know which model we need to load ? should we use a mapping again ?
            #!  we could try to look up <feed> key in a model mapping defined in data_models.websockets ?
            ws_data = data_models_map[feed](data=data, channel_name=feed)
            redis_pool.publish(channel, ujson.dumps(ws_data.dict()))

        except ValidationError as e:
            logging.error(stackprinter.format(e, style="darkbg2"))


    @abstractmethod
    def msg_handler(self, msg, redis_pool):
        raise NotImplementedError

    


# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



