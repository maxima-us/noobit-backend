import ujson

from noobit.server.views import APIRouter, WebSocket
from noobit import runtime
from noobit.logger.structlogger import get_logger, log_exception

router = APIRouter()
logger = get_logger(__name__)


@router.websocket("/ws/notifications")
async def stream_notifications(websocket: WebSocket):

    # TODO same as market data streamer: segment with different channels

    await websocket.accept()
    redis = runtime.Config.redis_pool
    notifications = f"ws:public:status:subscription:*"

    try:
        [consumer] = await redis.psubscribe(notifications)
    except Exception as e:
        log_exception(logger, e)

    while True:
        if runtime.Config.terminate:
            break

        async for _chan, message in consumer.iter():
            try:
                payload = ujson.dumps(message)
                await websocket.send_text(payload)
            except Exception as e:
                log_exception(logger, e)