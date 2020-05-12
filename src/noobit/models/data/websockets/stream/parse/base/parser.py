from abc import ABC, abstractmethod

class BaseStreamParser(ABC):


    @abstractmethod
    def trade(self, message) -> dict:
        raise NotImplementedError


    @abstractmethod
    def instrument(self, message) -> dict:
        raise NotImplementedError


    @abstractmethod
    def orderbook(self, message) -> dict:
        raise NotImplementedError
