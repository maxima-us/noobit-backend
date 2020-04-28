import asyncio
import logging
from decimal import Decimal
from typing import Optional

from pydantic import ValidationError
import pytest
import pandas as pd

import stackprinter

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

    assert isinstance(resp, dict), resp



@pytest.mark.asyncio
async def test_get_open_orders_to_list(api):
    resp = await api.get_open_orders(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, list), resp


@pytest.mark.asyncio
async def test_get_closed_orders_to_list(api):
    resp = await api.get_closed_orders(mode="to_list")
    logging.error(resp)

    assert isinstance(resp, list), resp
