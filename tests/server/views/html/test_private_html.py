import httpx
from starlette.testclient import TestClient

from noobit.server.main_app import app
from noobit.server import settings

api = TestClient(app)

session = httpx.AsyncClient()
settings.SESSION = session



def test_get_account_balance():
    response = api.get("/html/private/account_balance/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_trade_balance():
    response = api.get("/html/private/trade_balance/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_open_orders():
    response = api.get("/html/private/open_orders/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_closed_orders():
    response = api.get("/html/private/closed_orders/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_user_trades():
    response = api.get("/html/private/trades/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_open_positions():
    response = api.get("/html/private/open_positions/kraken")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]