import logging
import asyncio

from fastapi import FastAPI
import httpx
import stackprinter
stackprinter.set_excepthook(style="darkbg2")

from noobit import runtime
from noobit.exchanges.mappings import public_ws_map, private_ws_map
from noobit.server.app_runtime import consume_ws
# from noobit.logger.structlogger import get_logger

logger = logging.getLogger("uvicorn.error")



async def public():
    for exchange_name, feedreader in public_ws_map.items():
        try:
            # dict value is class object, we need to instantiate it
            fr = feedreader()
            # connect method binds WebSocketClientProtocol to ws attribute
            await fr.connect(ping_interval=10, ping_timeout=30)
            if not runtime.Config.open_websockets.get(exchange_name, None):
                runtime.Config.open_websockets[exchange_name] = {}
            # store
            runtime.Config.open_websockets[exchange_name]["public"] = fr.ws

            if not runtime.Config.available_feedreaders.get(exchange_name, None):
                runtime.Config.available_feedreaders[exchange_name] = {}
            # store
            runtime.Config.available_feedreaders[exchange_name]["public"] = fr

        except Exception as e:
            logger.exception(e)


async def private():
    for exchange_name, feedreader in private_ws_map.items():
        try:
            # dict value is abstract object, we need to instantiate it
            fr = feedreader()
            # connect method from feedreader binds WebSocketClientProtocol to ws attribute
            await fr.connect(ping_interval=10, ping_timeout=30)

            if not runtime.Config.open_websockets.get(exchange_name, None):
                runtime.Config.open_websockets[exchange_name] = {}
            runtime.Config.open_websockets[exchange_name]["private"] = fr.ws

            if not runtime.Config.available_feedreaders.get(exchange_name, None):
                runtime.Config.available_feedreaders[exchange_name] = {}
            # store
            runtime.Config.available_feedreaders[exchange_name]["private"] = fr

        except Exception as e:
            logger.exception(e)



async def load_feedhandlers():
    for exchange_name, fr_dict in runtime.Config.available_feedreaders.items():
        try:
            public_fr = fr_dict["public"]
            private_fr = fr_dict["private"]
        except Exception as e:
            logger.exception(e)

        asyncio.ensure_future(consume_ws.public(public_fr))

