import asyncio
import time
import pytest
import pandas as pd
import logging




# ==== PyTest Fixtures
# ======================================== 


@pytest.fixture
def api():
    import httpx
    from server.crypto_api.api import Api

    test_api = Api(exchange="kraken")
    test_api.session = httpx.AsyncClient()

    return test_api




# ==== Test Public Queries
# ========================================


@pytest.mark.asyncio
async def test_get_ticker(api):
    single_pair = await api.get_ticker(["XBT-USD"])
    pairs_list = await api.get_ticker(["XBT-USD", "ETH-USD"])

    
    assert isinstance(single_pair, pd.DataFrame)
    assert isinstance(pairs_list, pd.DataFrame)

    cols = ["ask", "bid", "close", "volume", "vwap", "trades", "low", "high", "open"]
    
    assert sorted(single_pair.columns.values.tolist()) == sorted(cols)
    assert sorted(pairs_list.columns.values.tolist()) == sorted(cols) 



@pytest.mark.asyncio
async def test_get_ohlc(api):
    resp = await api.get_ohlc(["XBT-USD"], timeframe=240)

    assert isinstance(resp, dict) 
    assert sorted(list(resp.keys())) == ["df", "last"]

    assert isinstance(resp["df"], pd.DataFrame)
    assert sorted(resp["df"].columns.values.tolist()) == sorted(["time", "open", "high", "low", "close", "vwap", "volume", "count"])

    assert isinstance(resp["last"], int)


@pytest.mark.asyncio
async def test_get_orderbook(api):
    resp = await api.get_orderbook(["XBT-USD"])

    assert isinstance(resp, dict)
    assert sorted(list(resp.keys())) == ["asks", "bids"]

    assert isinstance(resp["asks"], pd.DataFrame)
    assert isinstance(resp["bids"], pd.DataFrame)

    assert sorted(resp["asks"].columns.values.tolist()) == sorted(["price", "volume", "timestamp"])
    assert sorted(resp["bids"].columns.values.tolist()) == sorted(["price", "volume", "timestamp"])


@pytest.mark.asyncio
async def test_get_trades(api):
    resp = await api.get_trades(["XBT-USD"])

    assert isinstance(resp, dict)
    assert sorted(list(resp.keys())) == ["df", "last"]

    assert isinstance(resp["df"], pd.DataFrame)
    assert isinstance(resp["last"], int)

    cols = ["price", "volume", "time", "side", "type", "misc"]
    assert sorted(resp["df"].columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_spread(api):
    resp = await api.get_spread(["XBT-USD"])

    assert isinstance(resp, dict)
    assert sorted(list(resp.keys())) == ["df", "last"]

    assert isinstance(resp["df"], pd.DataFrame)
    assert isinstance(resp["last"], int)

    cols = ["time", "bid", "ask"]
    assert sorted(resp["df"].columns.values.tolist()) == sorted(cols)




# ==== Test Private Queries
# ========================================


@pytest.mark.asyncio
async def test_get_account_balance(api):
    resp = await api.get_account_balance()

    assert isinstance(resp, dict)


@pytest.mark.asyncio
async def test_get_trade_balance(api):
    balance_in_usd = await api.get_trade_balance(asset="usd")
    balance_in_eur = await api.get_trade_balance(asset="eur")

    assert isinstance(balance_in_usd, dict)
    assert isinstance(balance_in_eur, dict)


@pytest.mark.asyncio
async def test_get_open_orders(api):
    #! problems with handling args

    resp = await api.get_open_orders()

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

    assert isinstance(resp, pd.DataFrame)

    cols = ["refid", "userref", "status", "opentm", "starttm", "expiretm", "descr", 
    "vol", "vol_exec", "cost", "fee", "price", "stopprice", "limitprice", "misc", 
    "oflags", "closetm", "reason"] 
    #if trades=true we need to append trades to cols

    assert sorted(resp.columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_user_trades_history(api):
    resp = await api.get_user_trades_history()

    assert isinstance(resp, pd.DataFrame)

    cols = ["pair", "time", "type", "ordertype", "price",
    "cost", "fee", "vol", "margin", "misc", "ordertxid", 
    "posstatus", "postxid"  
    ]

    assert sorted(resp.columns.values.tolist()) == sorted(cols)


@pytest.mark.asyncio
async def test_get_open_positions(api):
    #! test will fail if we have no open positions as it returns an empty df
    resp = await api.get_open_positions()

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
async def test_place_order(api):
    resp = await api.place_order(pair=["XRP-USD"], 
                                side="buy",
                                ordertype="limit", 
                                price=float(0.1),
                                volume=float(100),
                                validate=True
                                )

    assert resp["descr"]["order"] == 'buy 100.00000000 XRPUSD @ limit 0.10000'


@pytest.mark.asyncio
async def test_cancel_order(api):
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