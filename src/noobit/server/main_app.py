import os

import uvicorn
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from noobit.server import settings
from noobit.server.app_startup.register_client import register_session
from noobit.server.app_startup.register_orm import register_tortoise
from noobit.server.views import cache, html, json
import noobit_user


# TODO      copy paste code from minigryph: at startup should initialize all exchange classes
# TODO      from abstract factory and store them in settings file
# TODO      then we can load them into the views.account file
# TODO      ==> rather just send all the minigryph data to a kafka topic instead of printing it,
# TODO      ==> and have fastapi connect to that topic + the same database

#TODO       load httpx client at startup : https://www.python-httpx.org/advanced/


app = FastAPI()


origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_dir = noobit_user.get_abs_path()

register_tortoise(
    app=app,
    db_url=f"sqlite://{user_dir}/data/fastapi.db",
    modules={"models": ["noobit.models.orm"]},
    generate_schemas=True,
    )

register_session(
    app=app
    )

# register_kafka(
#     app=app,
#     config={"bootstrap.servers": "localhost:9092", "group.id": "cryptofeed"},
#     loop = asyncio.get_event_loop()
#     )

router = APIRouter()



# Routers we want to actually use in production
app.include_router(cache.account.router, prefix="/cache", tags=["cached_data"])
app.include_router(json.public.router, prefix="/json/public", tags=["public_data", "json"])
app.include_router(json.private.router, prefix="/json/private", tags=["private_data", "json"])
# app.include_router(html.public.router, prefix="/html/public", tags=["public_data", "html"])
# app.include_router(html.private.router, prefix="/html/private", tags=["private_data", "html"])


# app.mount("/static", StaticFiles(directory="server/static"), name="static")
# we don't need static files anymore



# Tring to add a background task based on the following example :
# https://github.com/miguelgrinberg/python-socketio/issues/282

# We need to find a way to shutdown th bg task/infinite loop when uvicorn is shutdown

@app.on_event('startup')
async def signal_startup():
    settings.UVICORN_RUNNING = True


@app.on_event('shutdown')
async def signal_shutdown():
    settings.UVICORN_RUNNING = False


async def run_uvicorn():
    uvicorn.run(app, host='localhost', port=8000)


# def run_server():
#     from server import main_server

#     logging.info("Initiating application startup.")
#     main_server.run("main_app:app", host='localhost', port=8000, reload=False)
