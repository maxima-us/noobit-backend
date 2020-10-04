import os
import asyncio
from asyncio import CancelledError
from typing import List
from socket import error as socket_error

import uvloop
import aioredis
from websockets import ConnectionClosed
from tortoise import Tortoise

from noobit.logger.structlogger import get_logger, log_exception, log_exc_to_db
from noobit.exchanges.mappings.websockets import private_ws_map, public_ws_map

from noobit.server import settings
from noobit_user import get_abs_path


logger = get_logger(__name__)

user_dir = get_abs_path()
config = None
config_file = None
db_url=f"sqlite://{user_dir}/data/fastapi.db"
modules={"models": ["noobit.models.orm"]}
generate_schemas=True


class FeedHandler(object):
    """Central Logic to handle all different websocket data

    Args:
        exchanges (list): list of exchanges to subscribe to
        feeds (list): list of feeds to subscribe to (shared)

    Returns:
        cls
    """


    def __init__(self, exchanges: List[str], private_feeds: List[str], public_feeds: List[str], pairs: List[str], retries: int = 10):
        """For now, feeds will be common to all exchanges, meaning all
        exchanges will subscribe to the same feeds we passed

        maybe instead we should pass a dict like this:
        {
            "kraken":{
                "private_feeds":["trade", "order"],
                "public_feeds": ["trade", "instrument", "orderbook"]
            }
        }
        and define the arg passed as a model of Dict[str, FeedsModel]
        where FeedsModel is a pydantic.BaseModel with fields private_feeds: List[str] and public_feeds: List[str]
        """

        self.exchanges = [exchange.lower() for exchange in exchanges]
        self.private_feeds = private_feeds
        self.public_feeds = public_feeds
        self.terminate = False
        self.private_feed_readers = {}
        self.public_feed_readers = {}
        self.pairs = pairs

        self.redis_pool = None
        self.db_connection = None

        self.tasks = []
        self.retries = retries

        # if settings.TORTOISE_CONNECTION:
        #     logger.info(settings.TORTOISE_CONNECTION)
        # else:
        #     logger.info(f"connection is : {settings.TORTOISE_CONNECTION}")
        #     logger.info(f"server is : {settings.SERVER}")

        # if runtime_config.TORTOISE_CONNECTION is not None:
        #     logger.info(settings.TORTOISE_CONNECTION)
        # else:
        #     logger.info("no connection in config")
        print("inited")


    async def connect_private(self, exchange, ping_interval: int = 60, ping_timeout: int = 30):

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
                log_exception(logger, e)
                await asyncio.sleep(delay)
                await self.connect_private(exchange)
                retries += 1
                delay *= 2

            except Exception as e:
                log_exception(logger, e)
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2


    async def close_private(self, exchange):
        await self.private_feed_readers[exchange].close()





    async def connect_public(self, exchange, ping_interval: int = 60, ping_timeout: int = 30):
        exchange_public_ws = public_ws_map[exchange]()
        await exchange_public_ws.connect(ping_interval, ping_timeout)
        await exchange_public_ws.subscribe(pairs=self.pairs, feeds=self.public_feeds)
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
                log_exception(logger, e)
                await asyncio.sleep(delay)
                await self.connect_public(exchange)
                retries += 1
                delay *= 2

            except Exception as e:
                log_exception(logger, e)
                await log_exc_to_db(logger, e)
                await asyncio.sleep(delay)
                retries += 1
                delay *= 2


    async def close_public(self, exchange):
        await self.public_feed_readers[exchange].close()




    async def setup(self):

        self.redis_pool = await aioredis.create_redis_pool(('localhost', 6379))
        await Tortoise.init(config=config, config_file=config_file, db_url=db_url, modules=modules)
        if generate_schemas:
            try:
                logger.info("Tortoise-ORM generating schema")
                await Tortoise.generate_schemas()
            except Exception as e:
                logger.warning(e)
                raise e
        self.db_connection = Tortoise._connections
        settings.DB_CONNECTION = self.db_connection

        for exchange in self.exchanges:
            await self.connect_private(exchange)
            await asyncio.sleep(1)
            await self.connect_public(exchange)
            await asyncio.sleep(1)
            self.tasks.append(self.consume_private(exchange))
            self.tasks.append(self.consume_public(exchange))


    async def main(self):
        results = await asyncio.gather(*self.tasks)
        logger.info(self.public_feeds)
        logger.info(self.private_feeds)
        return results


    def run(self):

        process_id = os.getpid()
        logger.info(f"Starting process {process_id}")

        loop = uvloop.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.setup())
        logger.info(self.db_connection)

        try:
            loop.run_until_complete(self.main())
        except KeyboardInterrupt as e:
            self.terminate = True
            logger.info("Keyboard Interrupt")
        finally:
            loop = asyncio.get_event_loop()
            tasks = asyncio.all_tasks(loop)
            logger.info(f"Closing tasks : {asyncio.current_task(loop)}")
            for task in tasks:
                task.cancel()
            logger.info("Initiating shutdown")
            loop.run_until_complete(self.shutdown())
            logger.info("Stopping Event Loop")
            loop.stop()
            logger.info("Closing Event Loop")
            loop.close()


    async def shutdown(self):


        await Tortoise.close_connections()

        for exchange in self.exchanges:
            await self.close_private(exchange)
            await self.close_public(exchange)
        logger.info("FeedHandler --- Closing redis")
        self.redis_pool.close()
        await self.redis_pool.wait_closed()
        logger.info("FeedHandler --- Shutdown complete")




if __name__ == "__main__":

    aiotest = FeedHandler(exchanges=["kraken"], private_feeds=["ownTrades", "openOrders"], public_feeds=["trade"], pairs=["XBT/USD"])
    aiotest.run()