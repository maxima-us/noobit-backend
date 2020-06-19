import logging

from fastapi import FastAPI
import httpx

from noobit.server import settings
# from noobit.logger.structlogger import get_logger

logger = logging.getLogger("uvicorn.error")


def register_session(
        app=FastAPI,
    ):
    '''register an httpx session'''


    @app.on_event('startup')
    async def init_session():
        client = httpx.AsyncClient()
        settings.SESSION = client
        logger.info(f"Started HTTPX Session : {client}")


    @app.on_event('shutdown')
    async def close_session():
        await settings.SESSION.aclose()
        logger.info("Closed HTTPX Session")