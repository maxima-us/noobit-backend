import asyncio
import ujson
from datetime import datetime

from tortoise import Tortoise

from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket, HTMLResponse
from noobit.models.orm.account import Account

router = APIRouter()



@router.get('/historic/account_value')
async def get_historic_account_value():

    try:
        # returns a list of dicts, where each dicts contains model fields as keys
        account_table = await Account.all().values()
        filter_acc_value = [(datetime.timestamp(i["time_recorded"])*10**3, i["exposure"]["totalNetValue"]) for i in account_table]
        print(filter_acc_value[-1])
        payload = ujson.dumps(filter_acc_value)
        return payload
    except Exception as e:
        print(e)



@router.get('/update/account_value')
async def get_update_account_value():
    try:
        account_table = await Account.all().values()
        last_row = account_table[-1]
        filter_update_acc_value = (last_row["time_recorded"], last_row["exposure"]["totalNetValue"])
    except Exception as e:
        print(e)
    payload = ujson.dumps(filter_update_acc_value)
    return payload

