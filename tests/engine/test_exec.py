import logging

import pytest
import httpx
import websockets
import ujson
from pydantic import ValidationError
import stackprinter

from noobit.exchanges.mappings import rest_api_map
from noobit.engine.exec.execution import LimitChaseExecution
from noobit.models.data.send.websockets import AddOrder, CancelOrder

# ================================================================================
# ==== FIXTURES
# ================================================================================

@pytest.fixture
async def exec_model():
    api = rest_api_map["kraken"]()
    api.session = httpx.AsyncClient()

    ws_token = await api.get_websocket_auth_token()
    ws_uri = "wss://ws-auth.kraken.com"
    ws = await websockets.connect(uri=ws_uri,
                                  ping_interval=10,
                                  ping_timeout=30
                                  )

    # feeds = ["addOrder", "cancelOrder"]
    # for feed in feeds:
    #     try:
    #         data = {"event": "subscribe", "subscription": {"name": feed, "token": ws_token['token']}}
    #         payload = ujson.dumps(data)
    #         await ws.send(payload)

    #     except Exception as e:
    #         logging.warning(e)

    execution = LimitChaseExecution(exchange="kraken",
                                    pair=["xbt-usd"],
                                    ws=ws,
                                    ws_token=ws_token,
                                    strat_id=0,
                                    pair_decimals=0.1)
    return execution


# ================================================================================
# ==== TESTS
# ================================================================================



@pytest.mark.asyncio
async def test_place_and_cancel_orders(exec_model):
    """
    Since validate parameter is not yet functional for kraken WS, we need to
    place and order and cancel it immediately after
    """
    # exec_model.add_long_order(total_vol=0.0234567)

    # add_resp = await exec_model.place_order(testing=True)
    system_status = await exec_model.ws.recv()
    system_status = ujson.loads(system_status)
    assert list(system_status.keys()) == ["connectionID", "event", "status", "version"]
    assert system_status["status"] == "online"

    data = {
        "event": "addOrder",
        "token": exec_model.ws_token["token"],     # we need to get this from strat instance that Exec is binded to
        "userref": "0",    # we need to get this from strat instance that Exec is binded to
        "ordertype": "limit",
        "type": "buy",
        "pair": "XBT/USD",
        "volume": "0.021",
        "price": 1000
    }
    try:
        validated = AddOrder(**data)
        validated_data = validated.dict()
    except ValidationError as e:
        logging.error(e)

    payload = ujson.dumps(validated_data)
    await exec_model.ws.send(payload)

    add_resp = await exec_model.ws.recv()
    add_resp = ujson.loads(add_resp)


    error_msg = f"\n{payload}\n{add_resp.get('errorMessage')}"

    assert add_resp["status"] == "ok", error_msg
    assert add_resp["event"] == "addOrderStatus", error_msg

    try:
        txid = add_resp["txid"]
    except Exception as e:
        logging.warning(add_resp["errorMessage"])

    data = {
        "event": "cancelOrder",
        "token": exec_model.ws_token["token"],
        "txid": [txid]
    }

    try:
        validated = CancelOrder(**data)
        validated_data = validated.dict()
    except ValidationError as e:
        logging.error(e)

    payload = ujson.dumps(data)
    await exec_model.ws.send(payload)

    cancel_resp = await exec_model.ws.recv()
    cancel_resp = ujson.loads(cancel_resp)

    try:
        status = cancel_resp["status"]
    except Exception as e:
        logging.error(f'payload: {payload}')
        logging.error(stackprinter.format(e, style="darkbg2"))

    error_msg = f"\n{payload}\n{cancel_resp.get('errorMessage')}"
    assert cancel_resp["status"] == "ok", error_msg
    assert cancel_resp["event"] == "cancelOrderStatus", error_msg
