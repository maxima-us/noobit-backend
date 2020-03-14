from server import settings
import json
import logging
import pandas as pd

from starlette.responses import HTMLResponse, JSONResponse

from server.views import APIRouter, Request, WebSocket, Response, templates
from exchanges.mappings import rest_api_map


router = APIRouter()

@router.get('/{exchange}/{crypto}/{currency}/{timeframe}')
async def ohlc_chart(request : Request, exchange: str, crypto: str, currency: str, timeframe: int):
    api = rest_api_map[exchange]()
    req_pair = "XXBTZUSD"
    req = await api.query_public(method="ohlc", data={"pair": req_pair, "interval": timeframe})

    df = pd.DataFrame.from_records(req["result"][req_pair], columns=["unix", "open", "high", "low", "close", "vwap", "volume", "count"])
    df["unix"] = df["unix"]*1000
    ohlc_df = df.drop(["vwap", "volume", "count"], axis=1, inplace=False)
    volume_df = df[["unix", "volume"]]

    ohlc_data = json.loads(ohlc_df.to_json(orient="split"))["data"]
    volume_data = json.loads(volume_df.to_json(orient="split"))["data"]
    # kraken_data = json.dumps(kraken_data)

    # return templates.TemplateResponse("pages/dashboard_chart.html", {"request": request, "ohlc_data": ohlc_data, "volume_data": volume_data})
    # return req["result"][req_pair]
    # return HTMLResponse(df.to_html())
    return JSONResponse({"ohlc": ohlc_data, "volume": volume_data })
