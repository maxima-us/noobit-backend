from .trade import parse_trades_to_list
from .instrument import parse_instrument
from .orderbook import parse_orderbook

class KrakenStreamParser():


    def trade(self, message) -> dict:
        return parse_trades_to_list(message)

    def instrument(self, message) -> dict:
        return parse_instrument(message)

    def orderbook(self, message) -> dict:
        return parse_orderbook(message)