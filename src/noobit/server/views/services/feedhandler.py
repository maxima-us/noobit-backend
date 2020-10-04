import asyncio
from typing import List, Dict, Optional
from typing_extensions import Literal

from starlette.background import BackgroundTask
from pydantic import BaseModel

from noobit.server.views import APIRouter, Query, UJSONResponse, WebSocket
from noobit.exchanges.mappings.websockets import public_ws_map
from noobit.logger.structlogger import get_logger, log_exception
from noobit import runtime
from noobit.models.data.base.types import PAIR, TIMEFRAME


logger = get_logger(__name__)
router = APIRouter()



@router.get('/inspect_runtime_config')
async def inspect_runtime_config():
    try:
        return {key:str(val) for (key, val) in vars(runtime.Config).items() if not key.startswith("__")}
    except Exception as e:
        log_exception(logger, e)


class SubPrivate(BaseModel):
    exchange: str

@router.post('/subscribe/private')
async def subscribe_private(data: SubPrivate):
    private_fr = runtime.Config.available_feedreaders[data.exchange]["private"]
    for feed in ["trade", "order"]:
        await private_fr.subscribe(feed)


class SubPublic(BaseModel):
    exchange: str
    symbols: List[PAIR]

@router.post('/subscribe/public')
async def subscribe_public(data: SubPublic):
    public_fr = runtime.Config.available_feedreaders[data.exchange]["public"]
    logger.info(data.exchange)
    logger.info(data.symbols)
    for symbol in data.symbols:
        for feed in ["orderbook", "trade", "instrument", "spread", "ohlc"]:
            # default values for depth and interval set in base feedreader are 50 and 60 respectively
            await public_fr.subscribe(symbol=symbol, feed=feed)
        #! private feeds should be subscribed anyway and dont depend on symbol => sub with ws at init



#================================================================================
#================================================================================
#================================================================================


class SelectedState(BaseModel):
    exchange: str
    symbol: PAIR
    timeframe: TIMEFRAME


@router.post('/trading')
async def recv_trade_state(data: SelectedState):
    runtime.Config.selected_exchange = data.exchange
    runtime.Config.selected_symbol = data.symbol
    runtime.Config.selected_timeframe = data.timeframe


class FeedState(BaseModel):
    exchanges: List[str]
    symbols: List[PAIR]
    public_feeds: Optional[List[str]]
    private_feeds: Optional[List[str]]

@router.post('/state')
async def recv_feed_state(data: FeedState):
    """
    receive dict of feeds that our frontend wants to be subscribed to
    compare with dict of feeds we have currently in runtime.Config and subscribe to missing ones
    or unsubscribe from excess ones
    """
    # it actually does not make much sense to sub to only a select feed, so we will sub to all feeds automatically
    # will also make everything much easier

    #! we should probably have an "allowed pairs" attr in our runtime config (to filter out allowed pairs from available pairs)


    try:
        # for each feed received from frontend, check if it is already subscribed
        # if they are not, subscribe and add them to runtime.config
        # for each feed in runtime.config, check if it is among the ones received from frontend
        # if it isn't, we unsubscribe from it
        for exchange in data.exchanges:

            public_fr = runtime.Config.available_feedreaders[exchange]["public"]
            private_fr = runtime.Config.available_feedreaders[exchange]["private"]

            for symbol in data.symbols:
                print("Iterating over symbol: ", symbol)

                for public_feed in data.public_feeds:
                    logger.info(f"verifying if subbed {symbol} {public_feed}")

                    if not symbol in runtime.Config.subscribed_feeds.get(exchange, {}).get("public", {}).get(public_feed, {}):
                        # subscribe to this feed if the key does not exist
                        logger.info(f"subbing to {symbol} {public_feed}")
                        await public_fr.subscribe(symbol, public_feed)

                    current_feeds = runtime.Config.subscribed_feeds.get(exchange, {}).get("public", {}).get(public_feed, set())
                    diff = current_feeds - set(data.symbols)
                    if diff:
                        for f in diff:
                            logger.info(f"unsubbing from {f} {public_feed}")
                            await public_fr.unsubscribe(symbol=f, feed=public_feed)

            #! we also need to make sure we unsub if private_feeds list we receive is empty
            #! ==> in that case there would be no iteration
            for private_feed in data.private_feeds:
                if not private_feed in runtime.Config.subscribed_feeds.get(exchange, {}).get("private", set()):
                    # subscribre to this feed if the key does not exist
                    await private_fr.subscribe(private_feed)

                current_feeds = runtime.Config.subscribed_feeds.get(exchange, {}).get("private", set())
                diff = current_feeds - set(data.private_feeds)
                logger.info(f"diff: {diff}")
                if diff:
                    for f in diff:
                        await private_fr.unsubscribe(feed=f)


    except Exception as e:
        log_exception(logger, e)


#================================================================================
#================================================================================
#================================================================================


@router.get('/feed/remove/public', response_class=UJSONResponse)
async def remove_public_feed_from_fh(exchange: str = Query(..., title="Exchanges"),
                        #  private_feeds: List[str] = Query(..., title="List of private feeds to subscribe"),
                         public_feeds: List[str] = Query(..., title="List of public feeds to subscribe"),
                         pairs: List[str] = Query(..., title="List of pairs to subscribe")
                        ):
    public_fr = runtime.Config.available_feedreaders[exchange]["public"]
    await public_fr.unsubscribe(pairs=pairs, feeds=public_feeds)



@router.post('/add_strat')
async def start_strat(exchange: str = Query(..., title="exchange"),
                      strategy: str = Query(..., title="strategy"),
                      timeframe: str = Query(..., title="timeframe"),
                      symbol: str = Query(..., title="Symbol"),
                      ):

    strat_class = runtime.Config.available_strategies.get(strategy, None)
    if not strat_class:
        return {"error": f"strategy {strategy} not available"}

    strat = strat_class(exchange, symbol, timeframe)
    if not strat.execution_models:
        return {"error": f"no execution model defined for strategy {strategy}"}
    else:
        tasks = []
        for _key, model in strat.execution_models.items():
            try:
                await model.setup()
                tasks.extend(model.redis_tasks)

                logger.debug(model.ws)
                logger.debug(model.ws_token)

            except Exception as e:
                log_exception(logger, e)

        tasks.append(strat.main_loop())

        for task in tasks:
            runtime.Config.scheduled.append(task)

        runtime.Config.running_strategies[strat.name] = strat
    try:
        return {f"{strat.name} - started coros": {task.__name__:str(task) for task in tasks}}
    except Exception as e:
        log_exception(logger, e)


@router.get('/print_from_ws')
async def print_from_ws(exchange: str = Query(..., title="Exchange")):
    while True:
        if runtime.Config.terminate:
            break
        ws = runtime.Config.open_websockets[exchange]["public"]
        async for msg in ws:
            print(msg)
