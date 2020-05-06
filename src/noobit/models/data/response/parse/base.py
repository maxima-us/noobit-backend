from abc import ABC, abstractmethod
from typing import Union

from noobit.models.data.base.errors import ErrorResult, OKResult


# check below to enforce attributes on subclass of BaseClass
# https://stackoverflow.com/questions/23831510/abstract-attribute-not-property


class BaseResponseParser(ABC):


    @abstractmethod
    def handle_errors(self, response, endpoint, data) -> Union[OKResult, ErrorResult]:
        """Type checking should happen within the method.
        """
        raise NotImplementedError


    @abstractmethod
    def orders(self, response, mode, symbol) -> Union[dict, list]:
        """Type checking happens outside of the method, in the base api file.
        """
        raise NotImplementedError


    @abstractmethod
    def user_trades(self, response, mode, symbol) -> Union[dict, list]:
        raise NotImplementedError


    # public trades
    @abstractmethod
    def trades(self, response):
        raise NotImplementedError


    @abstractmethod
    def ohlc(self, response):
        raise NotImplementedError