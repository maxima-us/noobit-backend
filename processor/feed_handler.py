import os
import signal
import asyncio
from asyncio import CancelledError
from typing import List
from contextlib import suppress
import logging
from socket import error as socket_error


import stackprinter
from typing_extensions import Literal
import uvloop
import aioredis
import websockets
from websockets import ConnectionClosed


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


    def __init__(self, exchanges: List[str], private_feeds: List[str], public_feeds: List[str], pairs: List[str], retries: int=10):
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

        self.tasks = []
        self.retries = retries




    async def connect_private(self, exchange, ping_interval: int=60, ping_timeout: int=30):

        exchange_private_ws = private_ws_map[exchange](self.private_feeds)
        await exchange_private_ws.subscribe(ping_interval, ping_timeout)
        if exchange_private_ws is not None:
            self.private_feed_readers[exchange] = exchange_private_ws


    async def consume_private(self, exchange):

        retries = 0
        delay = 1

        while retries <= self.retries or self.retries == -1:

            try:

                async for msg in self.private_feed_readers[exchange].ws:
                    if self.terminate:
                        break
                    private_fr = self.private_feed_readers[exchange]
                    await private_fr.msg_handler(msg, self.redis_pool)
                    # print(msg)

            except CancelledError:
                return

            except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError, socket_error) as e:
                print("encountered connection issue - reconnecting...")
                await asyncio.sleep(delay)
                await self.connect_private(exchange)
                retries += 1
                delay *= 2

            except Exception:
                print("encountered an exception, reconnecting")
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2


    async def close_private(self, exchange):
        await self.private_feed_readers[exchange].close()





    async def connect_public(self, exchange, ping_interval: int=60, ping_timeout: int=30):
        exchange_public_ws = public_ws_map[exchange](pairs=self.pairs, feeds=self.public_feeds)
        await exchange_public_ws.subscribe(ping_interval, ping_timeout)
        if exchange_public_ws is not None:
            self.public_feed_readers[exchange] = exchange_public_ws


    async def consume_public(self, exchange):
        retries = 0
        delay = 1

        while retries <= self.retries or self.retries == -1:

            try:
                async for msg in self.public_feed_readers[exchange].ws:
                    if self.terminate:
                        break
                    public_fr = self.public_feed_readers[exchange]
                    await public_fr.msg_handler(msg, self.redis_pool)
                    # print(msg)

            except CancelledError:
                return

            except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError, socket_error) as e:
                print("reconnecting public ws")
                await asyncio.sleep(delay)
                await self.connect_public(exchange)
                retries += 1
                delay *= 2

            except Exception as e:
                print(stackprinter.format(e, style="darkbg2"))
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2


    async def close_public(self, exchange):
        await self.public_feed_readers[exchange].close()




    async def setup(self):

        self.redis_pool = await aioredis.create_redis_pool('redis://localhost')

        for exchange in self.exchanges:
            await self.connect_private(exchange)
            await asyncio.sleep(1)
            await self.connect_public(exchange)
            await asyncio.sleep(1)
            self.tasks.append(self.consume_private(exchange))
            self.tasks.append(self.consume_public(exchange))


    async def main(self):
        results = await asyncio.gather(*self.tasks)
        return results


    def run(self):

        process_id = os.getpid()
        print(f"Starting process {process_id}")

        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.setup())
        try:
            loop.run_until_complete(self.main())
        except KeyboardInterrupt:
            self.terminate=True
            print("Keyboard Interrupt")
        finally:
            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop)
            print(f"Closing tasks : {asyncio.current_task(loop)}")
            for task in tasks:
                task.cancel()
            print("Initiating shutdown")
            loop.run_until_complete(self.shutdown())
            print("Stopping Event Loop")
            loop.stop()
            print("Closing Event Loop")
            loop.close()


    async def shutdown(self):
        for exchange in self.exchanges:
            await self.close_private(exchange)
            await self.close_public(exchange)
        print("FeedHandler --- Closing redis")
        self.redis_pool.close()
        await self.redis_pool.wait_closed()
        print("FeedHandler --- Shutdown complete")




if __name__ == "__main__":

    aiotest = FeedHandler(exchanges=["kraken"], private_feeds=["ownTrades", "openOrders"], public_feeds=["trade"], pairs=["XBT/USD"])
    aiotest.run()