from server import settings
import json
import logging
from decimal import Decimal 
from typing import List

from server.views import APIRouter, Query, HTMLResponse, UJSONResponse
from exchanges.mappings import rest_api_map


router = APIRouter()

#! Shoud we pass pair list as path parameter of query parameter
#! ==> queried like "domain/endpoint/pair" or "domain/endpoint?pair=..."

# ================================================================================
# ==== Public Exchange Data


@router.get('/pairs/{exchange}', response_class=UJSONResponse)
async def get_pairs(exchange: str):
    api = rest_api_map[exchange]()
    pairs = await api.get_mapping()
    return pairs


@router.get('/ticker/{exchange}', response_class=HTMLResponse)
async def get_ticker(exchange: str, 
                     pair: List[str] = Query(..., title="Dash Separated Pair", maxlength=8)
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_ticker_as_pandas(pair=pair)
    html_table = response.to_html()
    return html_table
    

@router.get('/ohlc/{exchange}', response_class=HTMLResponse)
async def get_ohlc(exchange: str, 
                   pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                   timeframe: int = Query(..., title="OHLC Candle Interval in minutes"),
                   since: int = Query(None, title="Return data since given timestamp"),
                   retries: int = Query(None, title="Number of times to retry the request if it fails")
                   ):
    api = rest_api_map[exchange]()
    response = await api.get_ohlc_as_pandas(pair=[pair], timeframe=timeframe, since=since, retries=retries)
    html_table = response["data"].to_html()
    return f"{html_table}<br><p>last : {response['last']}</p>"

@router.get('/orderbook/{exchange}', response_class=HTMLResponse)
async def get_orderbook(exchange: str, 
                        pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                        count: int = Query(None, title="Maximum number of asks/bids to return"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.get_orderbook_as_pandas(pair=[pair], count=count, retries=retries)
    html_asks_table = response["asks"].to_html()
    html_bids_table = response["bids"].to_html()
    return f"<table><tr><td><h3>asks</h3>{html_asks_table}</td><td><h3>bids</h3>{html_bids_table}</td></tr></table>"


@router.get("/trades/{exchange}", response_class=HTMLResponse)
async def get_trades(exchange: str, 
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_trades_as_pandas(pair=[pair], since=since, retries=retries)
    html_table = response["data"].to_html()
    return f"{html_table}<br><p>last : {response['last']}</p>"


@router.get("/spread/{exchange}", response_class=HTMLResponse)
async def get_spread(exchange: str, 
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_spread_as_pandas(pair=[pair], since=since, retries=retries)
    html_table = response["data"].to_html()
    return f"{html_table}<br><p>last : {response['last']}</p>"


