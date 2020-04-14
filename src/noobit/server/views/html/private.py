from typing import List

import pandas as pd

from noobit.server.views import APIRouter, Query, HTMLResponse
from noobit.exchanges.mappings import rest_api_map

router = APIRouter()


# ================================================================================
# ==== Private User Data
# ================================================================================


@router.get('/account_balance/{exchange}', response_class=HTMLResponse)
async def get_account_balance(exchange: str):
    api = rest_api_map[exchange]()
    response = await api.get_account_balance()
    data = response["data"]
    df = pd.DataFrame.from_dict(data, orient="index")
    return df.to_html()


@router.get('/trade_balance/{exchange}', response_class=HTMLResponse)
async def get_trade_balance(exchange: str,
                            asset: str = Query(None, title="Base Asset used to determine balance", maxlength=4),
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    response = await api.get_trade_balance_as_pandas(asset=asset, retries=retries)

    df = pd.DataFrame.from_dict(response)
    return df.to_html()


@router.get('/open_orders/{exchange}', response_class=HTMLResponse)
async def get_open_orders(exchange: str,
                          trades: bool = Query(None, title="Wether to include trades in output"),
                          retries: int = Query(None, title="Number of times to retry the request if it fails")
                          ):
    api = rest_api_map[exchange]()
    response = await api.get_open_orders_as_pandas(trades=trades, retries=retries)
    html_table = response.to_html()
    return html_table


@router.get('/closed_orders/{exchange}', response_class=HTMLResponse)
async def get_closed_orders(exchange: str,
                            trades: bool = Query(None, title="Wether to include trades in output"),
                            start: int = Query(None, title="Start Unix Timestamp"),
                            end: int = Query(None, title="End Unix Timestamp"),
                            closetime: str = Query(None, title="Which time to use (candle close, open or both)"),
                            retries: int = Query(None, title="Number of times to retry the request if it fails")
                            ):
    api = rest_api_map[exchange]()
    response = await api.get_closed_orders_as_pandas(trades=trades, start=start, end=end, closetime=closetime, retries=retries)
    html_table = response.to_html()
    return html_table


@router.get('/trades/{exchange}', response_class=HTMLResponse)
async def get_user_trade(exchange: str,
                         trade_type: str = Query(None, title="Type of trade"),
                         trades: bool = Query(None, title="Wether to include trades in output"),
                         start: int = Query(None, title="Start Unix Timestamp"),
                         end: int = Query(None, title="End Unix Timestamp"),
                         retries: int = Query(None, title="Number of times to retry the request if it fails")
                         ):
    api = rest_api_map[exchange]()
    response = await api.get_user_trades_as_pandas(trade_type=trade_type,
                                                   trades=trades,
                                                   start=start,
                                                   end=end,
                                                   retries=retries
                                                   )
    html_table = response.to_html()
    return html_table


@router.get('/open_positions/{exchange}', response_class=HTMLResponse)
async def get_positions(exchange: str,
                        txid: List[int] = Query(None, title="List of transaction ids to query"),
                        show_pnl: bool = Query(None, title="Show profit and loss of positions"),
                        retries: int = Query(None, title="Number of times to retry the request if it fails")
                        ):
    api = rest_api_map[exchange]()
    response = await api.get_open_positions_as_pandas(txid=txid, show_pnl=show_pnl, retries=retries)
    html_table = response.to_html()
    return html_table


@router.get('/ledger/{exchange}')
async def get_trade_ledger(exchange: str):
    pass
