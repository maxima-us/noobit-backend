
from noobit.models.data.websockets.stream.parse.base import BaseStreamParser
from .trade import parse_trades_to_list
from .instrument import parse_instrument
from .orderbook import parse_orderbook
from .order import parse_order_snapshot_by_id, parse_order_update_by_id
from .user_trade import parse_user_trade
from .add_order import parse_add_order
from .cancel_order import parse_cancel_order
from .spread import parse_spread
from .status import parse_connection_status, parse_subscription_status
from .ohlc import parse_ohlc


class KrakenStreamParser(BaseStreamParser):


    def trade(self, message) -> list:
        return parse_trades_to_list(message)

    def instrument(self, message) -> dict:
        return parse_instrument(message)

    def spread(self, message) -> dict:
        return parse_spread(message)

    def ohlc(self, message) -> dict:
        return parse_ohlc(message)

    def orderbook(self, message) -> dict:
        return parse_orderbook(message)

    def order_snapshot(self, message) -> dict:
        return parse_order_snapshot_by_id(message)

    def order_update(self, message) -> dict:
        return parse_order_update_by_id(message)

    def user_trade(self, message) -> list:
        return parse_user_trade(message)

    def add_order(self, validated_data, token) -> dict:
        return parse_add_order(validated_data, token)

    def cancel_order(self, validated_data, token) -> dict:
        return parse_cancel_order(validated_data, token)

    def connection_status(self, message) -> dict:
        return parse_connection_status(message)

    def subscription_status(self, message) -> dict:
        return parse_subscription_status(message)