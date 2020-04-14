import httpx
from starlette.testclient import TestClient

from noobit.server.main_app import app
from noobit.server import settings

api = TestClient(app)

session = httpx.AsyncClient()
settings.SESSION = session



def test_get_ticker():
    response = api.get("/html/public/ticker/kraken?pair=xbt-usd")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_ohlc():
    response = api.get("/html/public/ohlc/kraken?pair=xbt-usd&timeframe=240")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_orderbook():
    response = api.get("/html/public/orderbook/kraken?pair=xbt-usd")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_trades():
    response = api.get("/html/public/trades/kraken?pair=xbt-usd")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_spread():
    response = api.get("/html/public/spread/kraken?pair=xbt-usd")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]