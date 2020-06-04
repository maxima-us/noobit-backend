from typing_extensions import Literal

from noobit.server.views import APIRouter, Query, UJSONResponse
from noobit.exchanges.mappings import rest_api_map


router = APIRouter()


# ================================================================================
# ==== Private User Data
# ================================================================================


@router.get('/open_orders/{exchange}', response_class=UJSONResponse)
async def get_open_orders(exchange: str,
                          mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                          ):


    #! handle cases where exchange is unknown to return correct error message
    api = rest_api_map[exchange]()

    response = await api.get_open_orders(mode=mode)
    return UJSONResponse(status_code=response.status_code, content=response.value)
    # return response.value


@router.get('/closed_orders/{exchange}', response_class=UJSONResponse)
async def get_closed_orders(exchange: str,
                            mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                            ):
    api = rest_api_map[exchange]()

    response = await api.get_closed_orders(mode=mode)
    return response



@router.get('/order/{exchange}', response_class=UJSONResponse)
async def get_single_order(exchange: str,
                           mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                           order_id: str = Query(..., title="orderID to query")
                           ):
    api = rest_api_map[exchange]()

    response = await api.get_order(mode=mode, orderID=order_id)
    return response


@router.get('/trades/{exchange}', response_class=UJSONResponse)
async def get_trades(exchange: str,
                     mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode")
                     ):
    api = rest_api_map[exchange]()

    response = await api.get_user_trades(mode=mode)
    return response


@router.get('/trade/{exchange}', response_class=UJSONResponse)
async def get_single_trade(exchange: str,
                           mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                           trade_id: str = Query(..., title="trdMatchID to query")
                           ):
    api = rest_api_map[exchange]()

    response = await api.get_user_trade_by_id(mode=mode, trdMatchID=trade_id)
    return response


@router.get('/positions/open/{exchange}', response_class=UJSONResponse)
async def get_open_positions(exchange: str,
                             mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                             symbol: str = Query(..., title="symbol")
                             ):
    api = rest_api_map[exchange]()

    response = await api.get_open_positions(symbol=symbol, mode=mode)
    return response


@router.get('/positions/closed/{exchange}', response_class=UJSONResponse)
async def get_closed_positions(exchange: str,
                               mode: Literal["by_id", "to_list"] = Query(..., title="Sorting mode"),
                               symbol: str = Query(..., title="symbol")
                               ):
    api = rest_api_map[exchange]()

    response = await api.get_closed_positions(symbol=symbol, mode=mode)
    return response


@router.get('/balances/{exchange}', response_class=UJSONResponse)
async def get_balances(exchange: str):
    api = rest_api_map[exchange]()

    response = await api.get_balances()
    return response


@router.get('/exposure/{exchange}', response_class=UJSONResponse)
async def get_exposure(exchange: str):
    api = rest_api_map[exchange]()

    response = await api.get_exposure()
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
