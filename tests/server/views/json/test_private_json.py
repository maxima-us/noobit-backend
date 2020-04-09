import logging

import httpx
from pydantic import ValidationError
from starlette.testclient import TestClient

from server.main_app import app
from server import settings
from models.data.receive.api import AccountBalance, TradeBalance, OpenOrders, ClosedOrders, UserTrades, OpenPositions


api = TestClient(app)

session = httpx.AsyncClient()
settings.SESSION = session


def test_get_account_balance():
    response = api.get("/json/private/account_balance/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        account_balance = AccountBalance(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_trade_balance():
    response = api.get("/json/private/trade_balance/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        trade_balance = TradeBalance(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_open_orders():
    response = api.get("/json/private/open_orders/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        open_orders = OpenOrders(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_closed_orders():
    response = api.get("/json/private/closed_orders/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        open_orders = ClosedOrders(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_user_trades():
    response = api.get("/json/private/trades/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        user_trades = UserTrades(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_open_positions():
    response = api.get("/json/private/open_positions/kraken")
    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        open_positions = OpenPositions(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e