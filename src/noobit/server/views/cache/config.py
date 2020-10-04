from noobit.exchanges.mappings import rest_api_map
import ujson

from noobit import runtime
from noobit.server.views import APIRouter, UJSONResponse


router = APIRouter()


@router.get('/config/available_exchanges')
async def get_available_exhanges():
    '''
    '''

    # redis_pool = runtime.Config.redis_pool
    # available_exchanges = await redis_pool.get("config:available_exchanges")
    available_exchanges = [k for k, _v in runtime.Config.available_feedreaders.items()]
    available_exchanges = ujson.dumps(available_exchanges)

    return available_exchanges

@router.get('/config/available_pairs')
async def get_exchange_pairs():

    available_exchanges = [k for k, _v in runtime.Config.available_feedreaders.items()]

    exch_pairs = {}
    for exch in available_exchanges:
        api = rest_api_map[exch]()
        pairs = [k for k, _v in api.exchange_pair_specs.items()]
        exch_pairs[exch] = pairs

    payload = ujson.dumps(exch_pairs)
    return payload


@router.get('/config/pair_specs')
async def get_exchange_pair_specs():
    pass


@router.get('/config/available_timeframes')
async def get_available_timeframes():
    available_timeframes = [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]
    payload = ujson.dumps(available_timeframes)
    return payload


@router.get('/config/available_execution_models')
async def get_available_exec_models():

    available_execution_models = [k for k, _v in runtime.Config.available_execution_models.items()]
    payload = ujson.dumps(available_execution_models)

    return payload


@router.get('/config/available_feeds')
async def get_available_feeds():
    pass