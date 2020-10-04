import ujson

from noobit import runtime
from noobit.server.views import APIRouter


router = APIRouter()
redis_pool = runtime.Config.redis_pool


@router.get('/account/balance/holdings/{exchange}')
async def get_balance_holdings(exchange: str):
    '''
    returns: balance holdings
    '''

    user_balances = await redis_pool.get(f"db:balance:holdings:{exchange}")
    user_balances = ujson.loads(user_balances)

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return user_balances


@router.get('/account/balance/{exchange}')
async def get_balance_full(exchange: str):
    '''
    returns: entire balance(holdings + positions)
    '''

    user_balances = await redis_pool.get("balances")
    user_balances = ujson.loads(user_balances)

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return user_balances[exchange]["holdings"]


@router.get('/account/balance/positions/{exchange}')
async def get_balance_positions(exchange: str):
    '''
    returns : balance positions
    '''

    user_balances = await redis_pool.get("balances")
    user_balances = ujson.loads(user_balances)

    # exch_balance = [balance for balance in all_balances if balance["exchange_id"]==settings.EXCHANGE_IDS[exchange]]
    # above code useless since we cleaned up the dict straight in the startup balance file

    return user_balances[exchange]["positions"]