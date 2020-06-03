import asyncio

import aioredis
from uvicorn.config import Config

from noobit.server import settings
from noobit.server.main_server import Server

server = None

async def launch_server():
    # cant just call main_server.run
    # main_server.run("noobit.server.main_app:app", host="localhost", port=8000, reload=False)
    app = "noobit.server.main_app:app"
    config = Config(app, host="localhost", port=8000, reload=False)
    config.backlog = 2048

    global server
    server = Server(config=config)
    server.aioredis_pool = await aioredis.create_redis_pool(('localhost', 6379))

    await server.serve()


async def get_ohlc():
    await asyncio.sleep(3)
    session = settings.SESSION

    global server

    try:
        ohlc = await session.get("http://localhost:8000/json/public/ohlc/kraken?symbol=XBT-USD&timeframe=60")
    except:
        pass
    finally:
        server.should_exit = True
        await server.shutdown_server()
        assert ohlc.status_code == 200

async def main():
    results = await asyncio.gather(
        launch_server(),
        get_ohlc()
    )
    return results

def test_main_server():


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
