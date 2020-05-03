from typing import Optional, Any

from typing_extensions import Literal

from noobit.models.data.base.types import PAIR
from noobit.models.data.request.parse.base import BaseRequestParser
from .orders import open_orders, closed_orders, order
from .trades import user_trades

class KrakenRequestParser(BaseRequestParser):


    def order(self,
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


    def trade(self,
              mode = None,
              symbol = None
              ):

        return user_trades()