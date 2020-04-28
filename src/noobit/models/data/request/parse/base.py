from abc import ABC, abstractmethod

from typing_extensions import Literal

from noobit.models.data.base.types import PAIR


class BaseRequestParser(ABC):


    @abstractmethod
    def order(self, filter: Literal["all", "closed", "open", "by_id"], symbol: PAIR, clOrdID: int):
        raise NotImplementedError

