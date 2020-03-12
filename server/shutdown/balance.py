from server import settings
import json
import logging
import stackprinter

from models.orm_models.balance import Balance
from server.startup.balance import update_balance_holdings, update_balance_positions

async def shutdown_balances():
    try:
        exch_balances = await Balance.all().values()
       
        for balance in exch_balances:
            await update_balance_holdings(balance)
            await update_balance_positions(balance)
    
    except Exception as e:
        logging.error(stackprinter.format(e, style="darkbg2"))