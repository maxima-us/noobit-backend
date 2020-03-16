import os
import signal,sys,time                          
import asyncio
import uvloop
import aioredis
import logging
import stackprinter
import functools
from contextlib import suppress


class FeedConsumer:

    def __init__(self, sub_map: dict=None):
        """
        Sub Map keys are how we want to name the channel, value is the channel/pattern to subscribe to 
        """
        self.redis = None
        if sub_map is None:
            self.sub_map = {"events": "heartbeat:*", "status": "status:*", "kraken_orders": "data:update:kraken:*", "system": "system:*"}
        else:
            self.sub_map = sub_map
        self.subd_channels = {}
        self.terminate = False


    async def subscribe(self):
        
        self.redis = await aioredis.create_redis_pool('redis://localhost')
        
        try:
            for key, channel_name in self.sub_map.items():
                res = await self.redis.psubscribe(channel_name)
                # subscribe/psub always return a list
                self.subd_channels[key] = res[0]
                assert isinstance(self.subd_channels[key], aioredis.Channel)

        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

    
    async def handle_msg(self, msg):
        print(f"Consumer --- Got message : {msg}")
    

    async def consume_from_channel(self, channel: aioredis.Channel):
        
        try:
            # print(f"consume from channel : {channel.name}")
            # print(f"        is active : {channel.is_active}")
            try:
                msg = await asyncio.wait_for(channel.get(), timeout=0.1)
                return msg
            except :
                pass
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2")) 
            
    
    async def on_tick(self, counter: int):


        await self.consume_from_channel(self.subd_channels["status"])
        await self.consume_from_channel(self.subd_channels["events"])
        await self.consume_from_channel(self.subd_channels["data"])
        await self.consume_from_channel(self.subd_channels["system"])

        if self.terminate:
            return True
        return False

