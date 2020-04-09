from server import settings

import logging

from fastapi import FastAPI
import httpx

def register_session(
    app=FastAPI,
    ):
    '''register an httpx session'''


    @app.on_event('startup')
    async def init_session():
        client = httpx.AsyncClient()
        settings.SESSION = client
        logging.info(f"Started HTTPX Session : {client}")


    @app.on_event('shutdown')
    async def close_session():
        await settings.SESSION.aclose()
        logging.info("Closed HTTPX Session")