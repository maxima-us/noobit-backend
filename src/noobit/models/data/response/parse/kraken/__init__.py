from typing_extensions import Literal

from noobit.models.data.base.types import PAIR, TIMEFRAME
from noobit.models.data.response.parse.base import BaseResponseParser

from .orders import parse_orders_to_list, parse_orders_by_id
from .user_trades import parse_user_trades_to_list, parse_user_trades_by_id
from .errors import handle_error_messages
from .ohlc import parse_ohlc
from .trades import parse_public_trades


class KrakenResponseParser(BaseResponseParser):


    def handle_errors(self, response, endpoint, data):
        return handle_error_messages(response, endpoint, data)


    def orders(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_orders_to_list(response, symbol)

        if mode == "by_id":
            return parse_orders_by_id(response, symbol)


    def user_trades(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_user_trades_to_list(response, symbol)

        if mode == "by_id":
            return parse_user_trades_by_id(response, symbol)


    def ohlc(self, response):
        return parse_ohlc(response)


    def trades(self, response):
        return parse_public_trades(response)