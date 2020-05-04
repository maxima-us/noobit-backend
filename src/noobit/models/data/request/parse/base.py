from abc import ABC, abstractmethod
from typing import Optional

from typing_extensions import Literal

from noobit.models.data.base.types import PAIR


class BaseRequestParser(ABC):


    @abstractmethod
    def order(self,
              mode: Literal["all", "closed", "open", "by_id"],
              symbol: Optional[PAIR] = None,
              orderID: Optional[str] = None,
              clOrdID: Optional[int] = None
              ) -> dict:
        raise NotImplementedError


    @abstractmethod
    def trade(self,
              mode: Literal["by_id", "to_list"],
              symbol: PAIR,
              trdMatchID: Optional[str] = None
              ) -> dict:
        raise NotImplementedError