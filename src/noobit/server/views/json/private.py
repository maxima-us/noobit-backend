from typing import List

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
async def new_api_get_open_orders(exchange: str):

    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_open_orders(mode="to_list")
    return response



@router.get('/new_api/order/{exchange}/{order_id}', response_class=UJSONResponse)
async def new_api_get_order_by_id(exchange: str, order_id: str):

    new_api_key = f"new_{exchange}"
    api = rest_api_map[new_api_key]()

    response = await api.get_order(mode="to_list", orderID=order_id)
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
