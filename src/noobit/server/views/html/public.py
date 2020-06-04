from starlette import status

from noobit.server.views import APIRouter, Query, HTMLResponse, UJSONResponse
from noobit.exchanges.mappings import rest_api_map


router = APIRouter()


# ================================================================================
# ==== Public Exchange Data
# ================================================================================


# @router.get('/pairs/{exchange}', response_class=UJSONResponse)
# async def get_pairs(exchange: str):
#     api = rest_api_map[exchange]()
#     pairs = await api.get_mapping()
#     return pairs


# @router.get('/ticker/{exchange}', response_class=HTMLResponse)
# async def get_ticker(exchange: str,
#                      pair: List[str] = Query(..., title="Dash Separated Pair", maxlength=8)
#                      ):
#     api = rest_api_map[exchange]()
#     response = await api.get_ticker_as_pandas(pair=pair)
#     html_table = response.to_html()
#     return html_table


@router.get('/ohlc/{exchange}')
async def get_ohlc(exchange: str,
                   symbol: str = Query(..., title="symbol"),
                   timeframe: int = Query(..., title="candle timeframe")
                   ):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_ohlc_as_pandas(symbol=symbol, timeframe=int(timeframe))
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=f"{html_table}")
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )


@router.get('/orderbook/{exchange}')
async def get_orderbook(exchange: str,
                        symbol: str = Query(..., title="symbol"),
                        ):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_orderbook_as_pandas(symbol=symbol)
        if response.is_ok:
            asks_table = response.value["asks"].to_html()
            bids_table = response.value["bids"].to_html()
            joined = f"<table><tr><td><h3>asks</h3>{asks_table}</td><td><h3>bids</h3>{bids_table}</td></tr></table>"
            return HTMLResponse(content=f"{joined}")
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )


# @router.get('/orderbook/{exchange}', response_class=HTMLResponse)
# async def get_orderbook(exchange: str,
#                         pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
#                         count: int = Query(None, title="Maximum number of asks/bids to return"),
#                         retries: int = Query(None, title="Number of times to retry the request if it fails")
#                         ):
#     api = rest_api_map[exchange]()
#     response = await api.get_orderbook_as_pandas(pair=[pair], count=count, retries=retries)
#     html_asks_table = response["asks"].to_html()
#     html_bids_table = response["bids"].to_html()
#     return f"<table><tr><td><h3>asks</h3>{html_asks_table}</td><td><h3>bids</h3>{html_bids_table}</td></tr></table>"


# @router.get("/trades/{exchange}", response_class=HTMLResponse)
# async def get_trades(exchange: str,
#                      pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
#                      since: int = Query(None, title="Return data since given timestamp"),
#                      retries: int = Query(None, title="Number of times to retry the request if it fails")
#                      ):
#     api = rest_api_map[exchange]()
#     response = await api.get_trades_as_pandas(pair=[pair], since=since, retries=retries)
#     html_table = response["data"].to_html()
#     return f"{html_table}<br><p>last : {response['last']}</p>"


@router.get('/trades/{exchange}')
async def get_trades(exchange: str,
                     symbol: str = Query(..., title="symbol"),
                     ):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_public_trades_as_pandas(symbol=symbol)
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=f"{html_table}")
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )

