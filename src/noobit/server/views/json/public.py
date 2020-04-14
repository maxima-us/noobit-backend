from typing import List

import stackprinter

from noobit.server import settings
from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket, HTMLResponse
from noobit.exchanges.mappings import rest_api_map


router = APIRouter()


# ================================================================================
# ==== Public Exchange Data
# ================================================================================


@router.get('/pairs/{exchange}', response_class=UJSONResponse)
async def get_pairs(exchange: str):
    api = rest_api_map[exchange]()
    pairs = await api.get_mapping()
    return pairs


@router.get('/ticker/{exchange}', response_class=UJSONResponse)
async def get_ticker(exchange: str,
                     pair: List[str] = Query(..., title="Dash Separated Pair", maxlength=8)
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_ticker(pair=pair)
    return response["data"]


@router.get('/ohlc/{exchange}', response_class=UJSONResponse)
async def get_ohlc(exchange: str,
                   pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                   timeframe: int = Query(..., title="OHLC Candle Interval in minutes"),
                   since: int = Query(None, title="Return data since given timestamp"),
                   retries: int = Query(None, title="Number of times to retry the request if it fails")
                   ):
    api = rest_api_map[exchange]()
    response = await api.get_ohlc(pair=[pair], timeframe=timeframe, since=since, retries=retries)
    return response["data"]


@router.get('/orderbook/{exchange}')
async def get_orderbook(exchange: str,
                        pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                        count: int = Query(None, title="Maximum number of asks/bids to return"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.get_orderbook(pair=[pair], count=count, retries=retries)
    # asks_table_json = response["asks"].to_json(orient="table")
    # bids_table_json = response["bids"].to_json(orient="table")
    # return {"asks": asks_table_json, "bids": bids_table_json}
    return response


@router.get("/trades/{exchange}")
async def get_trades(exchange: str,
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_trades(pair=[pair], since=since, retries=retries)
    return response["data"]


@router.get("/spread/{exchange}")
async def get_spread(exchange: str,
                     pair: str = Query(..., title="Dash Separated Pair", maxlength=8),
                     since: int = Query(None, title="Return data since given timestamp"),
                     retries: int = Query(None, title="Number of times to retry the request if it fails")
                     ):
    api = rest_api_map[exchange]()
    response = await api.get_spread(pair=[pair], since=since, retries=retries)
    return response["data"]



@router.get("/aggregate_historical_trades/{exchange}")
async def aggregate_historical_trades(exchange: str,
                                pair: str = Query(..., title="Dash Separated Pair", maxlength=9)
                                ):
    api = rest_api_map[exchange]()
    response = await api.write_historical_trades_to_csv(pair=[pair])
    return response



#! COME BACK TO THIS, WEBSOCKET BELOW DOESNT WORK AS INTENDED YET

import ujson

@router.websocket("/ws/trades/{exchange}")
async def get_trades_from_ws(websocket: WebSocket,
                             exchange: str,
                             # pair: str = Query(..., title="Dash Separated Pair", maxlength=8)
                             ):
    await websocket.accept()

    server_instance = settings.SERVER
    subd_channels = server_instance.subscribed_channels
    public_trade_updates = subd_channels["public_trade_updates"]

    try:
        async for _chan, message in public_trade_updates.iter():
            msg = message.decode("utf-8")
            data = ujson.loads(msg)
            print(data)
            await websocket.send_text(f"{data}")
    except Exception as e:
        print(stackprinter.format(e, style="darkbg2"))


@router.get("/trades_from_ws")
async def receive_trades_from_ws():
    html = """
        <head>
            <title>Trades</title>
        </head>
        <body>
            <ul id='messages'>
            </ul>
            <script>
                var ws = new WebSocket("ws://localhost:8000/json/public/ws/trades/kraken");
                ws.onmessage = function(event) {
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
            </script>
        </body>
    """
    return HTMLResponse(html)
