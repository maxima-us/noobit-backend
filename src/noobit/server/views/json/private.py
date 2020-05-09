from noobit.models.data.base.types import PAIR, TIMEFRAME
from starlette.responses import JSONResponse
from typing import List
from typing_extensions import Literal

from noobit.server.views import APIRouter, Query, UJSONResponse
from noobit.exchanges.mappings import rest_api_map


router = APIRouter()


# ================================================================================
# ==== Private User Data
# ================================================================================


@router.get('/account_balance/{exchange}', response_class=UJSONResponse)
async def get_account_balance(exchange: str):
    api = rest_api_map[exchange]()
    response = await api.get_account_balance()
    return response["data"]


@router.get('/trade_balance/{exchange}', response_class=UJSONResponse)
async def get_trade_balance(exchange: str,
                            asset: str = Query(None, title="Base Asset used to determine balance", maxlength=4),
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    response = await api.get_trade_balance(asset=asset, retries=retries)
    return response["data"]


@router.get('/open_orders/{exchange}', response_class=UJSONResponse)
async def get_open_orders(exchange: str,
                          trades: bool = Query(None, title="Wether to include trades in output"),
                          retries: int = Query(None, title="Number of times to retry the request if it fails")
                          ):
    api = rest_api_map[exchange]()
    response = await api.get_open_orders(trades=trades, retries=retries)
    return response["data"]


@router.get('/closed_orders/{exchange}', response_class=UJSONResponse)
async def get_closed_orders(exchange: str,
                            trades: bool = Query(None, title="Wether to include trades in output"),
                            start: int = Query(None, title="Start Unix Timestamp"),
                            end: int = Query(None, title="End Unix Timestamp"),
                            closetime: str = Query(None, title="Which time to use (candle close, open or both)"),
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    response = await api.get_closed_orders(trades=trades, start=start, end=end, closetime=closetime, retries=retries)
    return response["data"]


@router.get('/trades/{exchange}', response_class=UJSONResponse)
async def get_user_trades(exchange: str,
                          trade_type: str = Query(None, title="Type of trade"),
                          trades: bool = Query(None, title="Wether to include trades in output"),
                          start: int = Query(None, title="Start Unix Timestamp"),
                          end: int = Query(None, title="End Unix Timestamp"),
                          retries: int = Query(None, title="Number of times to retry the request if it fails")
                          ):
    api = rest_api_map[exchange]()
    response = await api.get_user_trades(trade_type=trade_type,
                                         trades=trades,
                                         start=start,
                                         end=end,
                                         retries=retries
                                         )
    return response["data"]


@router.get('/open_positions/{exchange}', response_class=UJSONResponse)
async def get_positions(exchange: str,
                        txid: List[int] = Query(None, title="List of transaction ids to query"),
                        show_pnl: bool = Query(None, title="Show profit and loss of positions"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.get_open_positions(txid=txid, show_pnl=show_pnl, retries=retries)
    return response["data"]


@router.get('/ledger/{exchange}', response_class=UJSONResponse)
async def get_trade_ledger(exchange: str):
    pass





# ================================================================================
# ==== NEW API
# ================================================================================

@router.get('/new_api/open_orders/{exchange}', response_class=UJSONResponse)
async def new_api_get_open_orders(exchange: str,
                                  mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                                  ):

    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_open_orders(mode=mode)
    return UJSONResponse(status_code=response.status_code, content=response.value)
    # return response.value


@router.get('/new_api/closed_orders/{exchange}', response_class=UJSONResponse)
async def new_api_get_closed_orders(exchange: str,
                                    mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                                    ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_closed_orders(mode=mode)
    return response



@router.get('/new_api/order/{exchange}', response_class=UJSONResponse)
async def new_api_get_order_by_id(exchange: str,
                                  mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                                  order_id: str = Query(..., title="orderID to query")
                                  ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_order(mode=mode, orderID=order_id)
    return response


@router.get('/new_api/trades/{exchange}', response_class=UJSONResponse)
async def new_api_get_trades(exchange: str,
                             mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                             ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_user_trades(mode=mode)
    return response

@router.get('/new_api/trade/{exchange}', response_class=UJSONResponse)
async def new_api_get_single_trade(exchange: str,
                                   mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                                   trade_id: str = Query(..., title="trdMatchID to query")
                                   ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_user_trade_by_id(mode=mode, trdMatchID=trade_id)
    return response


@router.get('/new_api/ohlc/{exchange}', response_class=UJSONResponse)
async def new_api_get_ohlc(exchange: str,
                       symbol: str = Query(..., title="symbol"),
                       timeframe: int = Query(..., title="candle timeframe")
                       ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_ohlc(symbol=symbol, timeframe=int(timeframe))
    return response



@router.get('/new_api/public_trades/{exchange}', response_class=UJSONResponse)
async def new_api_get_public_trades(exchange: str,
                                    symbol: str = Query(..., title="symbol"),
                                    ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_public_trades(symbol=symbol)
    return response


@router.get('/new_api/orderbook/{exchange}', response_class=UJSONResponse)
async def new_api_get_orderbook(exchange: str,
                                symbol: str = Query(..., title="symbol"),
                                ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_orderbook(symbol=symbol)
    return response


@router.get('/new_api/instrument/{exchange}', response_class=UJSONResponse)
async def new_api_get_instrument(exchange: str,
                                 symbol: str = Query(..., title="symbol")
                                 ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_instrument(symbol=symbol)
    return response



@router.get('/new_api/positions/open/{exchange}', response_class=UJSONResponse)
async def new_api_get_open_positions(exchange: str,
                                     mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                                     symbol: str = Query(..., title="symbol")
                                     ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_open_positions(symbol=symbol, mode=mode)
    return response


@router.get('/new_api/positions/closed/{exchange}', response_class=UJSONResponse)
async def new_api_get_closed_positions(exchange: str,
                                       mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                                       symbol: str = Query(..., title="symbol")
                                       ):
    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_closed_positions(symbol=symbol, mode=mode)
    return response




# ================================================================================
# ==== UNDECIDED
# ================================================================================



#! do we even need to set this as an api endpoint or do we just need the request for the bot ?
@router.get('/ws_token/{exchange}', response_class=UJSONResponse)
async def get_websocket_auth_token(exchange: str,
                                   validity: int = Query(None, title="Number of minutes the returned token will be valid")
                                   ):
    api = rest_api_map[exchange]()
    response = await api.get_websocket_auth_token(validity=validity)
    return response
