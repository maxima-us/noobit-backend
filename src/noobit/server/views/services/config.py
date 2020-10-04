from pydantic import BaseModel

from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket
from noobit.logger.structlogger import get_logger, log_exception
from noobit import runtime
from noobit.models.data.base.types import PAIR, TIMEFRAME

router = APIRouter()
logger = get_logger(__name__)

@router.get('/inspect')
async def inspect_runtime_config():
    try:
        return {key:str(val) for (key, val) in vars(runtime.Config).items() if not key.startswith("__")}
    except Exception as e:
        log_exception(logger, e)


#================================================================================


class TradeChartParams(BaseModel):
    exchange: str
    symbol: PAIR

@router.post('/update/requested/markets')
async def update_request_tradechart_params(data: TradeChartParams):
    msg = f"Requested params for trade chart: {data}"
    logger.info(msg)

    try:
        runtime.Config.requested_exchange_market_data = data.exchange
        runtime.Config.requested_symbol_market_data = data.symbol
    except Exception as e:
        log_exception(logger, e)