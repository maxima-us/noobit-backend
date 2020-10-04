"""class containing all runtime variables"""
from collections import deque
from typing import Dict, Any, List, Union, Optional

import httpx
import websockets

from noobit.models.data.base.types import PAIR, TIMEFRAME
# from noobit.engine.base import BaseStrategy
# from noobit.exchanges.base.websockets import BasePrivateFeedReader, BasePublicFeedReader


class GlobalConfig():

    @property
    def terminate(self):
        return self.__class__.terminate

    @terminate.setter
    def set_terminate(self, value):
        self.__class__.terminate = value
        Config.terminate = value
        Internal.terminate = value


#! should this be a pydantic model ?
class Config():

    terminate: bool = False

    # http session
    session: httpx.AsyncClient = None

    # aioredis pool
    redis_pool: None

    # scheduled coroutines to be picked up by watcher
    scheduled: deque = deque()

    # map exchange pairs to their specs
    # example: {"kraken": {"XBT-USD": {"price_precision": 6}}}
    available_pairs: Dict[str, Dict[PAIR, Dict[str, Any]]] = {}

    # example: {"kraken"; {"private": private_fr, "public": public_fr}}
    # available_feedreaders: Dict[str, Dict[str, Union[BasePublicFeedReader, BasePrivateFeedReader]]] = {}
    available_feedreaders: Dict[str, Dict[str, Union[Any, Any]]] = {}

    # example: {"kraken": {"private": set(), "public": dict()}}
    # private is a set since the subds are independant of pairs (e.g user trades)
    # for public feeds we need to sub to a pair (e.g ohlc for btc/usd)
    subscribed_feeds: Dict[str, Dict[str, List[str]]] = {}

    # map strategy name to class
    # available_strategies: Dict[str, BaseStrategy] = {}
    # running_strategies: Dict[str, BaseStrategy] = {}
    available_strategies: Dict[str, Any] = {}
    running_strategies: Dict[str, Any] = {}  #! should also map parameters to strat

    # map exec model to class
    available_execution_models: Dict[str, Any] = {}    #! BaseExecModel not defined yet
                                                       #! ExecModels should also be defined in noobit_user
    running_execution_models: Dict[str, Any] = {}      #! BaseExecModel not defined yet

    # example: {"kraken": {"private": ws, "public": ws}}
    open_websockets: Dict[str, Dict[str, websockets.client.WebSocketClientProtocol]] = {}

    # ws where connection dropped (feedreader has connect method for easy reconnection)
    # dropped_websockets: Dict[str, Dict[str, Union[BasePublicFeedReader, BasePrivateFeedReader]]] = {}
    dropped_websockets: Dict[str, Dict[str, Union[Any, Any]]] = {}


    # ================================================================================
    # ==== FRONTEND SELECTED ATTRS

    # Page: TRADE

    requested_exchange_market_data: Optional[str] = 'kraken'
    requested_symbol_market_data: Optional[PAIR] = 'XBT-USD'


    @classmethod
    async def watch_strats(self):
        """
        check if we receive a heartbeat every interval
        """
        pass

    @classmethod
    async def watch_execs(self):
        """
        check if we receive a heartbeat every interval
        """
        pass






# class GlobalConfig():

#     async def register(self, exchange):
#         setattr(self, exchange, ExchangeConfig())



# how we want to set or retrieve runtime data

# runtime.config.kraken.pairs --> get tradable pairs
#     >>> ["BTC-USD", "ETH-USD"] --> in noobit format
# runtime.config.pair_specs["kraken"] --> get specs for each pair (e.g price precisions)
#     >>> {"BTC-USD": {"price_decimals": 4, "volume_decimals": 5}}
# runtime.config.running_strategies
#     >>> {"kraken": {"mock_strat": {**params}}}
# runtime.config.open_websockets:
#     >>> {"kraken": {"private": ws, "public": ws}}
# runtime.config.available_strategies:
#     >>> ["mock_strat", "trend", "hft"]
#     or
#     >>> {"mock_strat": Strat, "trend": Strat}
# runtime.config.available_execution_models:
#     >>> ["limit_chase", "scaler"]
#     or
#     >>> {"limit_chase": ExecModel, "scaler": ExecModel}
# runtime.config.session
#     >>> httpx.ClientSession object
