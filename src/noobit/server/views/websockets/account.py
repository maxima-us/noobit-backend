import asyncio
from typing import Tuple, Set
from decimal import Decimal

from noobit.exchanges.mappings import rest_api_map
import ujson

from noobit.server.views import APIRouter, WebSocket
from noobit import runtime
from noobit.logger.structlogger import get_logger, log_exception
# from noobit.models.orm.account import Account

router = APIRouter()
logger = get_logger(__name__)

@router.websocket("/ws/account")
async def stream_account(websocket: WebSocket):
    "stream account data like holdings, positions, exposure etc etc"
    await websocket.accept()

    # FIXME we should read this from db and also stream historic holdings
    # so we can plot holdings of assets over time

    # should parsed into a format directly usable for vue-data-table
    # List of tuples (exchange, symbol, size)
    balances: Set[Tuple[str, str, Decimal]] = set()


    # while True:
    #     if runtime.Config.terminate:
    #         break

    #     try:
    #         account_table = await Account.all()
    #         filter_balances = [(i.balances, i.exchange_id) for i in account_table]
    #         await asyncio.sleep(2)
    #     except Exception as e:
    #         log_exception(logger, e)


    while True:
        if runtime.Config.terminate:
            break

        try:
            for exchange, _ in runtime.Config.available_feedreaders.items():
                api = rest_api_map[exchange]()
                resp = await api.get_balances()
                if resp.is_ok:
                    exch_balance = resp.value

                    # example of value:
                    # value = {
                    #   "USD": 2206,
                    #   "EUR": 1.5,
                    #   "XBT": 0.7,
                    #   "LTC": 0.01,
                    #   "ZEC": 207,
                    #   "XTZ": 389,
                    #   "LINK": 825,
                    # }

                    data = [(exchange, symbol, value) for symbol, value in exch_balance.items()]
                    balances.update(data)

            message = {
                "channel": "holdings",
                # vue data table needs same keys as defined in the table headers
                "data": [{
                    "exchange": item[0],
                    "symbol": item[1],
                    "size": round(float(item[2]), 2)
                } for item in balances]
            }
            payload = ujson.dumps(message)
            await websocket.send_text(payload)
            await asyncio.sleep(2)

        except Exception as e:
            log_exception(logger, e)
