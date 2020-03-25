from models.data_models.api import Ohlc, OpenOrders
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

from models.data_models.websockets import HeartBeat, SubscriptionStatus, SystemStatus
from models.data_models.websockets import Ticker, Trade, Spread, Book


# needs to be named exactly as the channel name from the exchange 
# TODO think about how this could work to orchestrate different exchanges
data_models_map = {"ticker": Ticker,
                   "trade": Trade,
                   "spread": Spread,
                   "book": Book
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




class BasePublicFeedReader(ABC):

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
            self.feed_counters = {}
    """


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


    
    async def publish_status(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:public:status:{self.exchange}"

        try:
            print(msg)
            subscription_status = SubscriptionStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(subscription_status.dict()))

        except ValidationError as e:
            logging.error(e)



    async def publish_heartbeat(self, msg: str, redis_pool):
        """message needs to be json loaded str, make sure we have the correct keys
        """

        channel = f"ws:public:heartbeat:{self.exchange}"

        try:
            heartbeat = HeartBeat(**msg)
            await redis_pool.publish(channel, ujson.dumps(heartbeat.dict()))

        except ValidationError as e:
            logging.error(e)



    async def publish_systemstatus(self, msg: str, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"ws:public:system:{self.exchange}"

        try:
            print(msg)
            system_status = SystemStatus(**msg)
            await redis_pool.publish(channel, ujson.dumps(system_status.dict()))

        except ValidationError as e:
            logging.error(e)



    async def publish_data(self, data, feed: str, feed_id: int, pair: str, redis_pool):
        """message needs to be json loadedy str, make sure we have the correct keys
        """

        channel = f"ws:public:data:{self.exchange}:{feed}"

        try:
            ws_data = data_models_map[feed](channel_id=feed_id, data=data, channel_name=feed, pair=pair)
        except ValidationError as e :
            logging.error(stackprinter.format(e, style="darkbg2"))
        
        try:
            self.feed_counters[channel] += 1
            update_chan = f"ws:public:data:update:{self.exchange}:{feed}:{pair}"
            data_to_publish = ws_data.dict()
            data_to_publish = data_to_publish["data"]
            print("data :", data_to_publish)
            await redis_pool.publish(update_chan, ujson.dumps(data_to_publish))
        except KeyError :
            self.feed_counters[channel] = 0
            snapshot_chan = f"ws:public:data:snapshot:{self.exchange}:{feed}:{pair}"
            data_to_publish = ws_data.dict()
            data_to_publish = data_to_publish["data"]
            await redis_pool.publish(snapshot_chan, ujson.dumps(data_to_publish))
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        # try:
        #     #!  how to we know which model we need to load ? should we use a mapping again ?
        #     #!  we could try to look up <feed> key in a model mapping defined in data_models.websockets ?
        #     ws_data = data_models_map[feed](data=data, channel_name=feed)
        #     redis_pool.publish(channel, ujson.dumps(ws_data.dict()))

        # except ValidationError as e:
        #     logging.error(stackprinter.format(e, style="darkbg2"))



    @abstractmethod
    def msg_handler(self, msg, redis_pool):
        """sort messages that we receive from websocket and send them to appropriate redis chan
        """
        raise NotImplementedError

    


# ================================================================================
# ==== Run file

# if __name__ == "__main__":

#     kraken = KrakenPrivateFeedReader()
#     kraken.run()



