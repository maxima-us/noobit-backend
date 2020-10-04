import asyncio
from datetime import datetime

import ujson
import stackprinter
stackprinter.set_excepthook(style="darkbg2")

from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket, HTMLResponse
from noobit import runtime
from noobit.models.orm.account import Account


router = APIRouter()

@router.websocket("/ws/test_ping")
async def test_ping(websocket: WebSocket):
    await websocket.accept()
    for i in range(50):
        await websocket.send_text(str(i))
        await asyncio.sleep(1)


# @router.websocket("/ws/notifications")
# async def stream_notifications(websocket: WebSocket):
#     await websocket.accept()
#     redis = runtime.Config.redis_pool
#     notifications = f"ws:public:status:subscription:*"

#     try:
#         [consumer] = await redis.psubscribe(notifications)
#     except Exception as e:
#         print(e)

#     while True:
#         if runtime.Config.terminate:
#             break

#         async for _chan, message in consumer.iter():
#             try:
#                 payload = ujson.dumps(message)
#                 await websocket.send_text(payload)
#             except Exception as e:
#                 print(e)


@router.websocket("/ws/trade/snapshot")
async def stream_push_trade(websocket: WebSocket,
                            ):
    await websocket.accept()
    redis = runtime.Config.redis_pool

    snapshot_chan = f"ws:public:data:trade:snapshot:*"

    try:
        [consumer] = await redis.psubscribe(snapshot_chan)
        if consumer:
            print("Successfully subd to trade ws")
    except Exception as e:
        print(e)

    while True:
        if runtime.Config.terminate:
            break

        async for _chan, message in consumer.iter():
            try:
                payload = ujson.dumps(message)
                print(message)
                await websocket.send_text(payload)
            except Exception as e:
                print(e)


@router.websocket("/ws/orderbook/snapshot")
async def stream_full_orderbook(websocket: WebSocket,
                                # exchange: str = Query(..., title="Exchange"),
                                # symbol: str = Query(..., title="Symbol")
                                ):
    await websocket.accept()

    redis = runtime.Config.redis_pool
    # snapshot_chan = f"ws:public:data:spread:snapshot:{runtime.Config.selected_exchange}:{runtime.Config.selected_symbol}"
    # snapshot_chan = f"ws:public:data:orderbook:snapshot:kraken:XBT-USD"
    snapshot_chan = f"ws:public:data:orderbook:snapshot:*"
    # sub returns list of channels
    try:
        [consumer] = await redis.psubscribe(snapshot_chan)
        if consumer:
            print("Sucessfully subd to orderbook ws")
    except Exception as e:
        print(e)

    while True:
        if runtime.Config.terminate:
            break

        async for _chan, message in consumer.iter():
            try:
                # print(message)
                payload = ujson.dumps(message)
                await websocket.send_text(payload)
            except Exception as e:
                print(e)



# @router.websocket("/ws/config")
# async def stream_config(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         if runtime.Config.terminate:
#             break

#         available_strats = [k for k, _v in runtime.Config.available_strategies.items()]
#         index_strats = {i: v for i, v in enumerate(available_strats)}
#         available_exchanges = [k for k, _v in runtime.Config.available_feedreaders.items()]

#         parsed_sub_feeds_public = []
#         for exchange, private_or_public in runtime.Config.subscribed_feeds.items():
#             for feed_name, pairs in private_or_public["public"].items():
#                 for pair in pairs:
#                     data = {
#                         "exchange": exchange,
#                         "type": "public",
#                         "feed": feed_name,
#                         "symbol": pair
#                     }
#                     parsed_sub_feeds_public.append(data)


#         data = {
#             "subscribed_feeds_public": parsed_sub_feeds_public,
#             "available_strategies": available_strats,
#             "running_strategies": runtime.Config.running_strategies,
#             "available_execution_models": runtime.Config.available_execution_models,
#             "indexed_strats": index_strats,
#             "available_exchanges": available_exchanges
#         }
#         try:
#             payload = ujson.dumps(data)
#             await websocket.send_text(payload)
#         except Exception as e:
#             pass
#         await asyncio.sleep(0.1)


@router.websocket("/ws/account_balance")
async def stream_account_balance(websocket: WebSocket):
    await websocket.accept()
    while True:
        if runtime.Config.terminate:
            break

        try:
            # returns a list of dicts, where each dicts contains model fields as keys
            account_table = await Account.all().values()
            # javascript timestamps are in milliseconds
            filter_acc_value = [(datetime.timestamp(i["time_recorded"])*10**3, i["exposure"]["totalNetValue"]) for i in account_table]
            payload = ujson.dumps(filter_acc_value)
            await websocket.send_text(payload)

        except Exception as e:
            print(e)

        await asyncio.sleep(1)

@router.websocket("/ws/update/account_balance")
async def stream_account_balance_update(websocket: WebSocket):
    await websocket.accept()
    previous_db_len = None
    while True:
        if runtime.Config.terminate:
            break

        try:
            # returns a list of dicts, where each dicts contains model fields as keys
            account_table = await Account.all().values()
            db_len = len(account_table)

            # initialize
            if not previous_db_len:
                previous_db_len = db_len
                continue

            if db_len > previous_db_len:
                # we have a new item and need to push it
                last_row = account_table[-1]
                # javascript timestamps are in milliseconds
                filter_update_acc_value = (datetime.timestamp(last_row["time_recorded"])*10**3, last_row["exposure"]["totalNetValue"])
                payload = ujson.dumps(filter_update_acc_value)
                await websocket.send_text(payload)
                # reset
                previous_db_len = db_len

        except Exception as e:
            print(e)

        await asyncio.sleep(1)

