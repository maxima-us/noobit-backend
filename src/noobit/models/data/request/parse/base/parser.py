from abc import ABC, abstractmethod
from typing import Optional

from typing_extensions import Literal

from noobit.models.data.base.types import PAIR, TIMEFRAME


class BaseRequestParser(ABC):


    @abstractmethod
    def orders(self,
               mode: Literal["all", "closed", "open", "by_id"],
               symbol: Optional[PAIR] = None,
               orderID: Optional[str] = None,
               clOrdID: Optional[int] = None
               ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def user_trades(self,
                    mode: Literal["by_id", "to_list"],
                    symbol: PAIR,
                    trdMatchID: Optional[str] = None
                    ) -> dict:
        raise NotImplementedError


    # ================================================================================
    # ==== PUBLIC REQUESTS
    # ================================================================================

    @abstractmethod
    def ohlc(self,
             symbol: PAIR,
             timeframe: TIMEFRAME
             ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def public_trades(self,
                      symbol: PAIR,
                      ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def orderbook(self,
                  symbol: PAIR,
                  ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def instrument(self,
                   symbol: PAIR,
                   ) -> dict:
        raise NotImplementedError