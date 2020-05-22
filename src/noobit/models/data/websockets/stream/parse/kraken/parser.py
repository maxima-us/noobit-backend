
from noobit.models.data.websockets.stream.parse.base import BaseStreamParser
from .trade import parse_trades_to_list
from .instrument import parse_instrument
from .orderbook import parse_orderbook
from .order import parse_order_snapshot_by_id, parse_order_update_by_id
from .user_trade import parse_user_trade

class KrakenStreamParser(BaseStreamParser):


    def trade(self, message) -> list:
        return parse_trades_to_list(message)

    def instrument(self, message) -> dict:
        return parse_instrument(message)

    def orderbook(self, message) -> dict:
        return parse_orderbook(message)

    def order_snapshot(self, message) -> dict:
        return parse_order_snapshot_by_id(message)

    def order_update(self, message) -> dict:
        return parse_order_update_by_id(message)

    def user_trade(self, message) -> list:
        return parse_user_trade(message)