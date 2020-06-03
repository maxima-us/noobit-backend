from typing import List

import stackprinter
from starlette import status

from noobit.server import settings
from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket, HTMLResponse
from noobit.exchanges.mappings import rest_api_map

from noobit.models.data.response import Ohlc, Instrument, OrderBook, TradesList

router = APIRouter()


# ================================================================================
# ==== Public Exchange Data
# ================================================================================



@router.get('/trades/{exchange}', response_class=UJSONResponse, response_model=TradesList)
async def get_public_trades(exchange: str,
                            symbol: str = Query(..., title="symbol"),
                            ):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_public_trades(symbol=symbol)
        if response.is_ok:
            return UJSONResponse(
                status_code=response.status_code,
                content=response.value
            )
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


@router.get('/orderbook/{exchange}', response_class=UJSONResponse, response_model=OrderBook)
async def get_orderbook(exchange: str,
                        symbol: str = Query(..., title="symbol"),
                        ):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_orderbook(symbol=symbol)
        if response.is_ok:
            return UJSONResponse(
                status_code=response.status_code,
                content={
                    "sendingTime": response.value["sendingTime"],
                    "symbol": response.value["symbol"],
                    "asks": response.value["asks"],
                    "bids": response.value["bids"]
                }
            )
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


@router.get('/instrument/{exchange}', response_class=UJSONResponse, response_model=Instrument)
async def get_instrument(exchange: str,
                         symbol: str = Query(..., title="symbol")
                         ):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_instrument(symbol=symbol)
        if response.is_ok:
            return UJSONResponse(
                status_code=response.status_code,
                content={**response.value}
            )
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



@router.get('/ohlc/{exchange}', response_class=UJSONResponse, response_model=Ohlc)
async def get_ohlc(exchange: str,
                   symbol: str = Query(..., title="symbol"),
                   timeframe: int = Query(..., title="candle timeframe")
                   ):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_ohlc(symbol=symbol, timeframe=int(timeframe))
        if response.is_ok:
            return UJSONResponse(
                status_code=response.status_code,
                content={"data": response.value}
            )
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
