import asyncio
import ujson

from noobit.server.views import APIRouter, WebSocket
from noobit import runtime
from noobit.logger.structlogger import get_logger, log_exception

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/runtime/config")
async def stream_runtime_config(websocket: WebSocket):
    await websocket.accept()
    while True:
        if runtime.Config.terminate:
            break

        available_strats = [k for k, _v in runtime.Config.available_strategies.items()]
        index_strats = {i: v for i, v in enumerate(available_strats)}
        available_exchanges = [k for k, _v in runtime.Config.available_feedreaders.items()]

        # TODO replace with dict to avoid potential duplicated
        parsed_websockets_status = []
        for exchange, private_or_public in runtime.Config.open_websockets.items():
            for key, _ in private_or_public.items():
                data = {
                    "exchange": exchange,
                    "type": key,
                    "status": "active",
                }
                parsed_websockets_status.append(data)

        for exchange, private_or_public in runtime.Config.dropped_websockets.items():
            for key, _ in private_or_public.items():
                data = {
                    "exchange": exchange,
                    "type": key,
                    "status": "dropped"
                }
                parsed_websockets_status.append(data)

        # TODO replace with dict to avoid potential duplicated
        parsed_sub_feeds_public = []
        for exchange, private_or_public in runtime.Config.subscribed_feeds.items():
            for feed_name, pairs in private_or_public["public"].items():
                for pair in pairs:
                    data = {
                        "exchange": exchange,
                        "type": "public",
                        "feed": feed_name,
                        "symbol": pair
                    }
                    parsed_sub_feeds_public.append(data)


        data = {
            "subscribed_feeds_public": parsed_sub_feeds_public,
            "available_strategies": available_strats,
            "running_strategies": runtime.Config.running_strategies,
            "available_execution_models": runtime.Config.available_execution_models,
            "indexed_strats": index_strats,
            "available_exchanges": available_exchanges,
            "websocket_status": parsed_websockets_status
        }

        try:
            payload = ujson.dumps(data)
            await websocket.send_text(payload)
        except Exception as e:
            log_exception(logger, e)

        await asyncio.sleep(0.5)