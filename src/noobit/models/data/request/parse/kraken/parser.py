from typing import Optional, Any

from typing_extensions import Literal

from noobit.models.data.base.types import PAIR, TIMEFRAME
from noobit.models.data.request.parse.base import BaseRequestParser
from .orders import open_orders, closed_orders, order
from .user_trades import parse_user_trades
from .ohlc import parse_ohlc
from .orderbook import parse_orderbook
from .instrument import parse_instrument
from .trades import parse_public_trades
from .open_positions import parse_open_positions
from .closed_positions import parse_closed_positions



class KrakenRequestParser(BaseRequestParser):


    def orders(self,
               mode: Literal["all", "open", "closed", "by_id"],
               symbol: Optional[PAIR] = None,
               orderID: Optional[Any] = None,
               clOrdID: Optional[int] = None
               ):

        if mode == "closed":
            return closed_orders(symbol, clOrdID)

        if mode == "open":
            return open_orders(symbol, clOrdID)

        if mode == "by_id":
            return order(orderID, clOrdID)


    def user_trades(self,
                    mode: Optional[Literal["to_list", "by_id"]] = None,
                    trdMatchID: Optional[str] = None,
                    symbol: Optional[PAIR] = None
                    ):

        return parse_user_trades(trdMatchID)


    def open_positions(self,
                       mode: Literal["to_list", "by_id"] = "to_list",
                       symbol: Optional[PAIR] = None
                       ):
        return parse_open_positions()


    def closed_positions(self,
                         mode: Literal["to_list", "by_id"] = "to_list",
                         symbol: Optional[PAIR] = None
                         ):
        return parse_closed_positions()



    # ================================================================================
    # ==== PUBLIC REQUESTS
    # ================================================================================


    def ohlc(self,
             symbol: PAIR,
             timeframe: TIMEFRAME
             ):
        return parse_ohlc(symbol, timeframe)


    def public_trades(self,
               symbol: PAIR
               ):
        return parse_public_trades(symbol)


    def orderbook(self,
                  symbol: PAIR,
                  ):
        return parse_orderbook(symbol)


    # corresponds to kraken ticker request
    def instrument(self,
                   symbol: PAIR,
                   ):
        return parse_instrument(symbol)