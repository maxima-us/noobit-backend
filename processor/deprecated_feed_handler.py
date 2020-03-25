import os
import signal
import asyncio
from typing import List
from contextlib import suppress
import logging

import stackprinter
import uvloop
import aioredis

from exchanges.mappings.websockets import private_ws_map, public_ws_map


HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)



class FeedHandler(object):
    """Central Logic to handle all different websocket data
    
    Args:
        exchanges (list): list of exchanges to subscribe to
        feeds (list): list of feeds to subscribe to (shared)

    Returns:
        cls
    """


    def __init__(self, exchanges: List[str], private_feeds: List[str], public_feeds: List[str], pairs: List[str]):
        """For now, feeds will be common to all exchanges, meaning all
        exchanges will subscribe to the same feeds we passed
        """

        self.exchanges = [exchange.lower() for exchange in exchanges]
        self.private_feeds = private_feeds
        self.public_feeds = public_feeds
        self.terminate = False
        self.private_feed_readers = {}
        self.public_feed_readers = {}
        self.pairs = pairs
    
    async def serve(self, ping_interval: int=60, ping_timeout: int=30):
        process_id = os.getpid()
        print(f"FeedHandler --- Started process {process_id}")
        self.install_signal_handlers()
        
        self.redis = await aioredis.create_redis_pool('redis://localhost')

        for exchange in self.exchanges:
            exchange_private_ws = private_ws_map[exchange](self.private_feeds)
            await exchange_private_ws.subscribe(ping_interval, ping_timeout)
            self.private_feed_readers[exchange] = exchange_private_ws
            
            exchange_public_ws = public_ws_map[exchange](pairs=self.pairs, feeds=self.public_feeds)
            await exchange_public_ws.subscribe(ping_interval, ping_timeout)
            self.public_feed_readers[exchange] = exchange_public_ws

        
        if self.terminate:
            return
        await self.main_loop()
        
        print("FeedHandler --- Shutting down")
        print("FeedHandler --- Closing redis")
        
        # how to get rid of aioredis.ConnectionForceClosedError
        self.redis.close()                                
        await self.redis.wait_closed()
        print("FeedHandler --- Shutdown complete")
        return


    async def on_tick(self, counter: int):

        try:
            for exchange in self.exchanges:
                await self.private_feed_readers[exchange].process_feed(self.redis)
                await self.public_feed_readers[exchange].process_feed(self.redis)
        except Exception as e:
            logging.error(stackprinter.format(e, style="darkbg2"))

        if self.terminate:
            return True
        return False


    async def main_loop(self):

        counter = 0
        should_exit = await self.on_tick(counter)
        while not should_exit:
            counter += 1

            # do we need to change 864000 to some other number ?
            counter = counter % 864000
            # if we don't sleep this blocks for some reason
            await asyncio.sleep(0.001)
            should_exit = await self.on_tick(counter)


    def run(self):
        uvloop.install()
        asyncio.run(self.serve())


    def install_signal_handlers(self):
        loop = asyncio.get_event_loop()

        try:
            for sig in HANDLED_SIGNALS:
                loop.add_signal_handler(sig, self.handle_exit, sig, None)
                # loop.add_signal_handler(sig, lambda sig=sig: asyncio.create_task(self.shutdown(sig, loop)))
                # loop.add_signal_handler(sig, lambda sig=sig: asyncio.create_task(self.another_shutdown(sig, loop)))
        except NotImplementedError as exc:
            # Windows
            for sig in HANDLED_SIGNALS:
                signal.signal(sig, self.handle_exit)


    def handle_exit(self, sig, frame):
        self.terminate = True