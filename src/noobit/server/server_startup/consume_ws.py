from typing import Union
import asyncio
from asyncio import CancelledError, IncompleteReadError
from noobit.exchanges.base.websockets import BasePublicFeedReader
from socket import error as socket_error
from websockets import ConnectionClosed

from noobit import runtime
from noobit.logger.structlogger import get_logger, log_exception, log_exc_to_db
from noobit.exchanges.base.websockets import BasePublicFeedReader


logger = get_logger(__name__)


async def public(feed_reader):
    await consume(feed_reader, "public")

async def private(feed_reader):
    await consume(feed_reader, "private")


async def consume(feed_reader: BasePublicFeedReader, public_or_private: Union["public", "private"], max_retries: int = 10):
    """consume all messages that we receive from websocket
    pass them onto msg handler function from feedreader (should just be routing)
    reminder that we will still need to sub to feed using our API
    """

    retried = 0
    delay = 1

    while retried <= max_retries or max_retries == -1:

        if runtime.Config.terminate:
            break

        try:
            async for msg in feed_reader.ws:
                await feed_reader.msg_handler(msg, runtime.Config.redis_pool)
                # print("inside async for", msg)

        except CancelledError:
            return

        #! handle reconnection here or in some watcher function ?
        except (ConnectionClosed, ConnectionAbortedError, ConnectionResetError, socket_error) as e:
            # log_exception(logger, e)

            # notify runtime
            if not runtime.Config.dropped_websockets.get(feed_reader.exchange, None):
                runtime.Config.dropped_websockets[feed_reader.exchange] = {}
            runtime.Config.dropped_websockets[feed_reader.exchange][public_or_private] = feed_reader
            print("CAPTURED ERROR - JUST TESTING TO SEE FROM WHERE WE RECV THE ERROR MSG")

            print("Trying to reconnect")
            for _exchange_name, fr_dict in runtime.Config.dropped_websockets.items():
                # we encountered runtimerror: dict changed size during iteration
                # watch out and fix
                for _level, fr in fr_dict.items():
                    await fr.connect(ping_interval=10, ping_timeout=30)
            # await asyncio.sleep(delay)
            # await self.connect_public(exchange)
            # retried += 1
            # delay *= 2

        except Exception as e:
            log_exception(logger, e)
            await log_exc_to_db(logger, e)
            await asyncio.sleep(delay)
            retried += 1
            delay *= 2
