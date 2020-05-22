import logging

import httpx
from pydantic import ValidationError
from starlette.testclient import TestClient

from noobit.server.main_app import app
from noobit.server import settings
from noobit.models.data.receive.api import Ohlc, Orderbook, Ticker, Trades, Spread


api = TestClient(app)

session = httpx.AsyncClient()
settings.SESSION = session


def test_get_pairs():
    response = api.get("/json/public/pairs/kraken")

    assert response.status_code == 200


def test_get_ticker():
    response = api.get("/json/public/ticker/kraken?pair=xbt-usd")

    assert response.status_code == 200

    only_data_as_key = len(response.json())==1 and list(response.json().keys())==["data"]
    assert not only_data_as_key, response.json()

    try:
        account_balance = Ticker(data=response.json())
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_ohlc():
    response = api.get("/json/public/ohlc/kraken?pair=xbt-usd&timeframe=240")

    assert response.status_code == 200

    only_data_and_last_as_keys = len(response.json())==2 and list(response.json().keys())==["data", "last"]
    assert not only_data_and_last_as_keys, response.json()

    try:
        account_balance = Ohlc(data=response.json(), last=0)
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_orderbook():
    response = api.get("/json/public/orderbook/kraken?pair=xbt-usd")

    assert response.status_code == 200

    try:
        account_balance = Orderbook(asks=response.json()["asks"], bids=response.json()["bids"])
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_trades():
    response = api.get("/json/public/trades/kraken?pair=xbt-usd")

    assert response.status_code == 200

    only_data_and_last_as_keys = len(response.json())==2 and list(response.json().keys())==["data", "last"]
    assert not only_data_and_last_as_keys, response.json()

    try:
        account_balance = Trades(data=response.json(), last=0)
    except ValidationError as e:
        logging.error(e)
        raise e


def test_get_spread():
    response = api.get("/json/public/spread/kraken?pair=xbt-usd")

    assert response.status_code == 200

    only_data_and_last_as_keys = len(response.json())==2 and list(response.json().keys())==["data", "last"]
    assert not only_data_and_last_as_keys, response.json()

    try:
        account_balance = Spread(data=response.json(), last=0)
    except ValidationError as e:
        logging.error(e)
        raise e