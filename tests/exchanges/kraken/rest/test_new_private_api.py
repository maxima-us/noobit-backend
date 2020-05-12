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


@pytest.mark.asyncio
async def test_get_open_orders_by_id(api):
    resp = await api.get_open_orders(mode="by_id")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value



@pytest.mark.asyncio
async def test_get_open_orders_to_list(api):
    resp = await api.get_open_orders(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


# ================================================================================


@pytest.mark.asyncio
async def test_get_closed_orders_by_id(api):
    resp = await api.get_closed_orders(mode="by_id")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value


@pytest.mark.asyncio
async def test_get_closed_orders_to_list(api):
    resp = await api.get_closed_orders(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


# ================================================================================


@pytest.mark.asyncio
async def test_get_user_trades_to_list(api):
    resp = await api.get_user_trades(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


@pytest.mark.asyncio
async def test_get_user_trades_by_id(api):
    resp = await api.get_user_trades(mode="by_id")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value



# ================================================================================


@pytest.mark.asyncio
async def test_get_open_positions_to_list(api):
    resp = await api.get_open_positions(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


@pytest.mark.asyncio
async def test_get_open_positions_by_id(api):
    resp = await api.get_open_positions(mode="by_id")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value


@pytest.mark.asyncio
async def test_get_closed_positions_to_list(api):
    resp = await api.get_closed_positions(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, list), resp.value


@pytest.mark.asyncio
async def test_get_closed_positions_by_id(api):
    resp = await api.get_closed_positions(mode="by_id")
    logging.error(resp)

    assert isinstance(resp, NoobitResponse), resp
    assert isinstance(resp.status_code, int), resp.status_code
    assert isinstance(resp.value, dict), resp.value