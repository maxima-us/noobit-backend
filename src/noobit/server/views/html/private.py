from starlette import status

from noobit.server.views import APIRouter, HTMLResponse, UJSONResponse
from noobit.exchanges.mappings import rest_api_map

router = APIRouter()


# ================================================================================
# ==== Private User Data
# ================================================================================


@router.get('/open_orders/{exchange}')
async def get_open_orders(exchange: str):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_open_orders_as_pandas()
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=html_table)
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )


@router.get('/closed_orders/{exchange}')
async def get_closed_orders(exchange: str):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_closed_orders_as_pandas()
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=html_table)
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )


@router.get('/trades/{exchange}')
async def get_user_trades(exchange: str):

    try:
        api = rest_api_map[exchange]()
        response = await api.get_user_trades_as_pandas()
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=html_table)
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )


@router.get('/open_positions/{exchange}')
async def get_open_positions(exchange: str):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_open_positions_as_pandas()
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=html_table)
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )

@router.get('/closed_positions/{exchange}')
async def get_closed_positions(exchange: str):
    try:
        api = rest_api_map[exchange]()
        response = await api.get_closed_positions_as_pandas()
        if response.is_ok:
            html_table = response.value.to_html()
            return HTMLResponse(content=html_table)
        else:
            return UJSONResponse(
                status_code=response.status_code,
                content={"error": response.value}
            )
    except Exception as e:
        return UJSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": repr(e)}
        )
# @router.get('/ledger/{exchange}')
# async def get_trade_ledger(exchange: str):
#     pass
