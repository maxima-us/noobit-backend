import asyncio

from fastapi import FastAPI

from noobit import runtime
from noobit.server.app_runtime import consume_ws



def load_feedreaders(app=FastAPI) -> None:

    @app.on_event('startup')
    async def init_fr():
        try:
            for exchange_name, fr_dict in runtime.Config.available_feedreaders.items():
                public_ws = runtime.Config.open_websockets[exchange_name]["public"]
                public_fr = fr_dict["public"](public_ws)

                private_ws = runtime.Config.open_websockets[exchange_name]["public"]
                private_fr = fr_dict["private"](private_ws)

                # task = asyncio.create_task(consume_ws.public(public_fr))
                # await task
                runtime.Config.scheduled.append((consume_ws.public, {"feed_reader":public_fr}))


        except Exception as e:
            raise e

