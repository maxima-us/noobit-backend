from noobit.models.data.response.parse.base import BaseResponseParser
from .orders import parse_orders_to_list, parse_orders_by_id
from .errors import handle_error_messages


class KrakenResponseParser(BaseResponseParser):


    def order(self, response, mode, symbol: str = None):
        if mode == "to_list":
            return parse_orders_to_list(response, symbol)

        if mode == "by_id":
            return parse_orders_by_id(response, symbol)


    def handle_errors(self, response, endpoint, data):
        return handle_error_messages(response, endpoint, data)