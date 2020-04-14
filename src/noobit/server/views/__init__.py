# shared global config
from noobit.server import settings

# common package imports
from fastapi import APIRouter, Query
from starlette.requests import Request
from starlette.websockets import WebSocket
from starlette.responses import Response, HTMLResponse, UJSONResponse

from starlette.templating import Jinja2Templates
templates = Jinja2Templates(directory="templates")

# just for better readability when we will import into main.py