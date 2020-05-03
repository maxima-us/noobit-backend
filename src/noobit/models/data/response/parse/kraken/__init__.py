from noobit.models.data.response.parse.base import BaseResponseParser
from typing_extensions import Literal
from .orders import parse_orders_to_list, parse_orders_by_id
from .trades import parse_trades_to_list, parse_trades_by_id
from .errors import handle_error_messages


class KrakenResponseParser(BaseResponseParser):


    def handle_errors(self, response, endpoint, data):
        return handle_error_messages(response, endpoint, data)


    def order(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_orders_to_list(response, symbol)

        if mode == "by_id":
            return parse_orders_by_id(response, symbol)


    def trade(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_trades_to_list(response, symbol)

        if mode == "by_id":
            return parse_trades_by_id(response, symbol)