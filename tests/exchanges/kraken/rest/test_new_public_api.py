import asyncio
import logging
from decimal import Decimal
from typing import Optional

from pydantic import ValidationError
import pytest
import pandas as pd

import stackprinter

from noobit.models.data.base.response import NoobitResponse

# ==== PyTest Fixtures
# ========================================


@pytest.fixture
def api():
    import httpx
    from noobit.exchanges.kraken.rest.new_api import KrakenRestAPI

    test_api = KrakenRestAPI()
    test_api.session = httpx.AsyncClient()

    return test_api


# ================================================================================


@pytest.mark.asyncio
async def test_get_ohlc(api):
    resp = await api.get_ohlc(symbol="xbt-usd", timeframe=15)
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


@pytest.mark.asyncio
async def test_get_public_trades(api):
    resp = await api.get_public_trades(symbol="eth-usd")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


@pytest.mark.asyncio
async def test_get_orderbook(api):
    resp = await api.get_orderbook(symbol="zec-usd")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value
    assert isinstance(resp.value["asks"], dict), resp.value
    assert isinstance(resp.value["bids"], dict), resp.value


@pytest.mark.asyncio
async def test_get_instrument(api):
    resp = await api.get_instrument(symbol="eth-usd")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value