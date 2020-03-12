from server import settings
import json
import logging

from decimal import Decimal 

import pandas as pd

from server.views import APIRouter, Request, WebSocket, Response, templates



router = APIRouter()

@router.get('/account/balance/{exchange}')
async def get_balance_full(exchange: str):
    '''
    returns: entire balance(holdings + positions)
    '''

    r = settings.REDIS
    all_balances = json.loads(r.get("balances"))

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return all_balances[exchange]


@router.get('/account/balance/holdings/{exchange}')
async def get_balance_holdings(exchange: str):
    '''
    returns: balance holdings
    '''

    r = settings.REDIS
    all_balances = json.loads(r.get("balances"))

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return all_balances[exchange]["holdings"]


@router.get('/account/balance/positions/{exchange}')
async def get_balance_positions(exchange: str):
    '''
    returns : balance positions
    '''

    r = settings.REDIS
    all_balances = json.loads(r.get("balances"))

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return all_balances[exchange]["positions"]