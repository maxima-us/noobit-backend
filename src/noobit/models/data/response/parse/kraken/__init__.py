from typing_extensions import Literal

from noobit.models.data.base.types import PAIR, TIMEFRAME
from noobit.models.data.response.parse.base import BaseResponseParser

from .orders import parse_orders_to_list, parse_orders_by_id
from .user_trades import parse_user_trades_to_list, parse_user_trades_by_id
from .errors import handle_error_messages
from .ohlc import parse_ohlc
from .trades import parse_public_trades
from .orderbook import parse_orderbook
from .instrument import parse_instrument
from .open_positions import parse_open_positions_to_list
from .closed_positions import parse_closed_positions_to_list


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


    def open_positions(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_open_positions_to_list(response)


    def closed_positions(self, response, mode: Literal["to_list", "by_id"], symbol: str = None):
        if mode == "to_list":
            return parse_closed_positions_to_list(response)



    # ================================================================================
    # ==== PUBLIC
    # ================================================================================


    def ohlc(self, response):
        return parse_ohlc(response)


    def trades(self, response):
        return parse_public_trades(response)


    def orderbook(self, response):
        return parse_orderbook(response)


    # corresponds to kraken ticker request
    def instrument(self, response):
        return parse_instrument(response)