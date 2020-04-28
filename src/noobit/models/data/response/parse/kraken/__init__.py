from noobit.models.data.response.parse.base import BaseResponseParser
from noobit.models.data.response.parse.kraken.orders import parse_orders_to_list, parse_orders_by_id


class KrakenResponseParser(BaseResponseParser):


    def order(self, response, symbol, mode):
        if mode == "to_list":
            return parse_orders_to_list(response, symbol)

        if mode == "by_id":
            return parse_orders_by_id(response, symbol)