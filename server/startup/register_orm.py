import logging
from typing import Dict, List, Optional

from fastapi import FastAPI
from tortoise import Tortoise


# from https://github.com/tortoise/tortoise-orm/blob/develop/tortoise/contrib/starlette/__init__.py


def register_tortoise(app=FastAPI,
                      config: Optional[dict] = None,
                      config_file: Optional[str] = None,
                      db_url: Optional[str] = None,
                      modules: Optional[Dict[str, List[str]]] = None,
                      generate_schemas: bool = False,
                      ) -> None:

    @app.on_event('startup')
    async def init_orm():
        await Tortoise.init(config=config, config_file=config_file, db_url=db_url, modules=modules)
        # logging.info("Tortoise-ORM started, %s, %s", Tortoise._connections, Tortoise.apps)
        if generate_schemas:
            try:
                logging.info("Tortoise-ORM generating schema")
                await Tortoise.generate_schemas()
            except Exception as e:
                logging.warning(e)
                pass

    @app.on_event('shutdown')
    async def close_orm():
        await Tortoise.close_connections()