from server import settings
import json
import logging
from decimal import Decimal 
from typing import List

from server.views import APIRouter, Query, HTMLResponse, UJSONResponse
from exchanges.kraken.utils.pairs import kraken_pairs
from exchanges.mappings import rest_api_map


router = APIRouter()

#! Shoud we pass pair list as path parameter of query parameter
#! ==> queried like "domain/endpoint/pair" or "domain/endpoint?pair=..."

# ================================================================================
# ==== Public Exchange Data


@router.get('/pairs/{exchange}', response_class=UJSONResponse)
async def get_pairs(exchange: str):
    pairs = await kraken_pairs(client=settings.SESSION)
    return pairs


@router.get('/ticker/{exchange}', response_class=HTMLResponse)
async def get_ticker(exchange: str, 
                     pair: List[str] = Query(..., title="Dash Separated Pair", maxlength=8)
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_ticker(pair=pair)
    html_table = response.to_html()
    return f"{html_table}"
    

@router.get('/ohlc/{exchange}', response_class=HTMLResponse)
async def get_ohlc(exchange: str, 
                   pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                   timeframe: int = Query(..., title="OHLC Candle Interval in minutes"),
                   since: int = Query(None, title="Return data since given timestamp"),
                   retries: int = Query(None, title="Number of times to retry the request if it fails")
                   ):
    api = rest_api_map[exchange]()
    response = await api.get_ohlc(pair=[pair], timeframe=timeframe, since=since, retries=retries)
    html_table = response["df"].to_html()
    return f"{html_table}<p><br></p>{response['last']}"


@router.get('/orderbook/{exchange}', response_class=HTMLResponse)
async def get_orderbook(exchange: str, 
                        pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                        count: int = Query(None, title="Maximum number of asks/bids to return"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.get_orderbook(pair=[pair], count=count, retries=retries)
    html_asks_table = response["asks"].to_html()
    html_bids_table = response["bids"].to_html()
    return f"{html_asks_table}<p><br></p>{html_bids_table}"


@router.get("/trades/{exchange}", response_class=HTMLResponse)
async def get_trades(exchange: str, 
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_trades(pair=[pair], since=since, retries=retries)
    html_table = response["df"].to_html()
    return f"{html_table}<p><br></p>{response['last']}"


@router.get("/spread/{exchange}", response_class=HTMLResponse)
async def get_spread(exchange: str, 
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_spread(pair=[pair], since=since, retries=retries)
    html_table = response["df"].to_html()
    return f"{html_table}<p><br></p>{response['last']}"


