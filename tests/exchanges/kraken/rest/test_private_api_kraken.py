import asyncio
from decimal import Decimal
from typing import Optional, Union
from models.data_models.api import (AccountBalance, Ohlc, OpenOrders, ClosedOrders, Orderbook, Spread, Ticker,
                                    TradeBalance, Trades, UserTrades, OpenPositions)
from pydantic import ValidationError
import time
import pytest
import pandas as pd
import logging





# ==== PyTest Fixtures
# ======================================== 


@pytest.fixture
def api():
    import httpx
    from exchanges.mappings import rest_api_map

    test_api = rest_api_map["kraken"]()
    test_api.session = httpx.AsyncClient()

    return test_api





# ==== Test Private Queries
# ========================================


@pytest.mark.asyncio
async def test_get_account_balance(api):
    resp = await api.get_account_balance()

    assert isinstance(resp, dict)
    assert isinstance(resp["data"], dict)

    try:
        account_balance = AccountBalance(data=resp["data"])
    except ValidationError as e:
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_trade_balance(api):
    balance_in_usd = await api.get_trade_balance(asset="usd")
    balance_in_eur = await api.get_trade_balance(asset="eur")

    assert isinstance(balance_in_usd, dict)
    assert isinstance(balance_in_eur, dict)

    keys = ["equivalent_balance", "trade_balance", "positions_margin", "positions_cost", "positions_unrealized",
            "positions_valuation", "equity", "free_margin", "margin_level"]

    try:
        assert sorted(list(balance_in_usd["data"].keys())) == sorted(keys) 
        assert sorted(list(balance_in_eur["data"].keys())) == sorted(keys)
    except Exception as e:
        logging.error(balance_in_usd)
        raise e

    try:
        trade_balance = TradeBalance(data=balance_in_usd["data"])
    except ValidationError as e:
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_open_orders(api):
    #! problems with handling args
    resp = await api.get_open_orders()

    assert isinstance(resp["data"], dict)

    try:
        open_orders = OpenOrders(data=resp["data"])
    except Exception as e:
        logging.error(e)
        raise e



@pytest.mark.asyncio
async def test_get_open_orders_as_pandas(api):
    resp = await api.get_open_orders_as_pandas()

    #we might not have any open orders
    if resp.empty:
        return
    
    assert isinstance(resp, pd.DataFrame)

    cols = ["refid", "userref", "status", "opentm", "starttm", "expiretm", "descr", 
    "vol", "vol_exec", "cost", "fee", "price", "stopprice", "limitprice", "misc", 
    "oflags"] 
    #if trades=true we need to append trades to cols

    assert sorted(resp.columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_closed_orders(api):
    #! problems with handling args
    resp = await api.get_closed_orders(offset=0)

    assert isinstance(resp["data"], dict)
    try:
        closed_orders = ClosedOrders(data=resp["data"])
    except Exception as e: 
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_closed_orders_as_pandas(api):
    resp = await api.get_closed_orders_as_pandas(offset=0)

    if resp.empty:
        return

    assert isinstance(resp, pd.DataFrame)

    cols = ["refid", "userref", "status", "opentm", "starttm", "expiretm", "descr", 
    "vol", "vol_exec", "cost", "fee", "price", "stopprice", "limitprice", "misc", 
    "oflags", "closetm", "reason"] 
    #if trades=true we need to append trades to cols

    assert sorted(resp.columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_user_trades(api):
    resp = await api.get_user_trades()
    assert isinstance(resp["data"], dict)
    try:
        user_trades = UserTrades(data=resp["data"])
    except Exception as e:
        logging.error(e)
        raise e    


@pytest.mark.asyncio
async def test_get_user_trades_as_pandas(api):
    resp = await api.get_user_trades_as_pandas()
    assert isinstance(resp, pd.DataFrame)

    cols = ["pair", "time", "type", "ordertype", "price",
    "cost", "fee", "vol", "margin", "misc", "ordertxid", 
    "posstatus", "postxid"  
    ]

    assert sorted(resp.columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_open_positions(api):

    resp = await api.get_open_positions()

    assert isinstance(resp, dict)
    try:
        open_positions = OpenPositions(data=resp)
    except Exception as e:
        logging.error(e)
        logging.error(resp)
        raise e


@pytest.mark.asyncio
async def test_get_open_positions_as_pandas(api):
    resp = await api.get_open_positions_as_pandas()
    assert isinstance(resp, pd.DataFrame)

    if resp.empty:
        return

    cols = ["pair", "time", "type", "ordertype", "cost", 
    "fee", "vol", "vol_closed", "margin", "value", "net", 
    "misc", "oflags", "ordertxid", "posstatus", "rollovertm",
    "terms"
    ]

    assert sorted(resp.columns.values.tolist()) == sorted(cols)




# ==== Test User Trading Queries
# ========================================


@pytest.mark.asyncio
async def st_place_order(api):
    resp = await api.place_order(pair=["XRP-USD"], 
                                side="buy",
                                ordertype="limit", 
                                price=float(0.1),
                                volume=float(100),
                                validate=True
                                )

    assert resp["descr"]["order"] == 'buy 100.00000000 XRPUSD @ limit 0.10000'


@pytest.mark.asyncio
async def tst_cancel_order(api):
    place = await api.place_order(pair=["XRP-USD"], 
                                side="buy",
                                ordertype="limit", 
                                price=float(0.1),
                                volume=float(100),
                                )

    txid = place["txid"]

    await asyncio.sleep(1)
    cancel = await api.cancel_order(txid=txid)

    assert cancel["count"] == 1




# ==== Test WebSocket Auth
# ========================================


@pytest.mark.asyncio
async def test_get_websocket_auth_token(api):
    response = await api.get_websocket_auth_token()

    assert isinstance(response, dict)
    assert sorted(list(response.keys())) == sorted(["token", "expires"])
    assert isinstance(response["token"], str)
    assert isinstance(response["expires"], int)