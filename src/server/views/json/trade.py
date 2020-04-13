from server.views import APIRouter, Query, UJSONResponse
from exchanges.mappings import rest_api_map


router = APIRouter()


# ================================================================================
# ==== Private User Trading
# ================================================================================


@router.post('/place_order/{exchange}', response_class=UJSONResponse)
async def place_order(exchange: str,
                      pair: str = Query(..., title="Dash Separated Pair"),
                      side: str = Query(..., title="Direction of the trade (buy or sell)"),
                      ordertype: str = Query(..., title="Market/Limit/Stop Loss/Take Profit"),
                      price: float = Query(None, title="Price - Leave empty if order type is market"),
                      volume: float = Query(..., title="Volume of Order in lots"),
                      price2: float = Query(None, title="2nd Price - Depends on ordertype - Usually used for stops/take profits"),
                      leverage: float = Query(None, title="Leverage Used"),
                      validate: bool = Query(None, title="Only validate Order Input, without actually placing the order"),
                      retries: int = Query(None, title="Number of times to retry the request if it fails"),
                      start_time: int = Query(None, title="Start Time"),
                      expire_time: int = Query(None, title="Expire Time")
                      ):

    api = rest_api_map[exchange]()

    # no price = market order => we set order price to last close to calculate slippage later
    if not price:
        price = await api.get_ticker_as_pandas([pair])
        price = float(price[pair.upper(), "close"][0])

    response = await api.place_order(pair=[pair],
                                     side=side,
                                     ordertype=ordertype,
                                     price=price,
                                     volume=volume,
                                     price2=price2,
                                     leverage=leverage,
                                     validate=validate,
                                     start_time=start_time,
                                     expire_time=expire_time,
                                     retries=retries
                                     )

    return response


@router.post('/cancel_order/{exchange}', response_class=UJSONResponse)
async def cancel_order(exchange: str,
                       txid: str = Query(..., title="ID of Order to cancel"),
                       retries: int = Query(None, title="Number of times to retry the request if it fails")
                       ):
    api = rest_api_map[exchange]()
    response = await api.cancel_order(txid=txid, retries=retries)
    return response



@router.post('/cancel_all_orders/{exchange}', response_class=UJSONResponse)
async def cancel_all_orders(exchange: str,
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    response = await api.cancel_all_orders(retries=retries)
    return response
