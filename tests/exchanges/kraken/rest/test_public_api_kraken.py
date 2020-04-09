from decimal import Decimal
from models.data.receive.api import (AccountBalance, Ohlc, OpenOrders, ClosedOrders, Orderbook, Spread, Ticker,
                                     TradeBalance, Trades, UserTrades, OpenPositions)
from pydantic import ValidationError
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




# ==== Test Public Queries
# ========================================

@pytest.mark.asyncio
async def test_get_ticker(api):
    single_pair = await api.get_ticker(["XBT-USD"])
    pairs_list = await api.get_ticker(["XBT-USD", "ETH-USD"])

    assert isinstance(single_pair["data"], dict)
    assert isinstance(pairs_list["data"], dict)

    try:
        ticker_model_single_pair = Ticker(data=single_pair["data"])
        ticker_model_pairs_list = Ticker(data=pairs_list["data"])
    except ValidationError as e:
        logging.error(single_pair)
        raise e




@pytest.mark.asyncio
async def test_get_ticker_as_pandas(api):
    single_pair = await api.get_ticker_as_pandas(["XBT-USD"])
    pairs_list = await api.get_ticker_as_pandas(["XBT-USD", "ETH-USD"])

    assert isinstance(single_pair, pd.DataFrame)
    assert isinstance(pairs_list, pd.DataFrame)

    cols = ["ask", "bid", "close", "volume", "vwap", "trades", "low", "high", "open"]

    assert sorted(single_pair.columns.values.tolist()) == sorted(cols)
    assert sorted(pairs_list.columns.values.tolist()) == sorted(cols)



@pytest.mark.asyncio
async def test_get_ohlc(api):
    resp = await api.get_ohlc(["XBT-USD"], timeframe=240)

    assert isinstance(resp["data"], list)
    assert isinstance(resp["last"], Decimal)
    assert sorted(list(resp.keys())) == ["data", "last"]

    try:
        ohlc_model = Ohlc(data=resp["data"], last=resp["last"])
    except ValidationError as e:
        logging.error(resp)
        raise e


@pytest.mark.asyncio
async def test_get_ohlc_as_pandas(api):
    resp = await api.get_ohlc_as_pandas(["XBT-USD"], timeframe=240)

    assert isinstance(resp["data"], pd.DataFrame)
    cols = ["time", "open", "high", "low", "close", "vwap", "volume", "count"]
    assert sorted(resp["data"].columns.values.tolist()) == sorted(cols)

    assert isinstance(resp["last"], Decimal)


@pytest.mark.asyncio
async def test_get_orderbook(api):
    resp = await api.get_orderbook(["XBT-USD"])

    assert isinstance(resp, dict)
    assert sorted(list(resp.keys())) == ["asks", "bids"]
    assert isinstance(resp["asks"], list)
    assert isinstance(resp["bids"], list)

    try:
        ob_model = Orderbook(asks=resp["asks"], bids=resp["bids"])
    except ValidationError as e:
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_orderbook_as_pandas(api):

    resp = await api.get_orderbook_as_pandas(["XBT-USD"])

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
    assert sorted(list(resp.keys())) == ["data", "last"]

    assert isinstance(resp["data"], list)
    assert isinstance(resp["last"], Decimal)

    try:
        trades = Trades(data=resp["data"], last=resp["last"])
    except ValidationError as e:
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_trades_as_pandas(api):
    resp = await api.get_trades_as_pandas(["XBT-USD"])
    cols = ["price", "volume", "time", "side", "type", "misc"]
    assert isinstance(resp["data"], pd.DataFrame)
    assert isinstance(resp["last"], Decimal)
    assert sorted(resp["data"].columns.values.tolist()) == sorted(cols)



@pytest.mark.asyncio
async def test_get_spread(api):
    resp = await api.get_spread(["XBT-USD"])

    assert isinstance(resp, dict)
    assert sorted(list(resp.keys())) == ["data", "last"]
    assert isinstance(resp["data"], list)
    assert isinstance(resp["last"], Decimal)

    try:
        spread = Spread(data=resp["data"], last=resp["last"])
    except ValidationError as e:
        logging.error(e)
        raise e


@pytest.mark.asyncio
async def test_get_spread_as_pandas(api):
    resp = await api.get_spread_as_pandas(["XBT-USD"])

    assert isinstance(resp["data"], pd.DataFrame)
    assert isinstance(resp["last"], Decimal)

    cols = ["time", "bid", "ask"]
    assert sorted(resp["data"].columns.values.tolist()) == sorted(cols)


