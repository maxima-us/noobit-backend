from abc import ABC, abstractmethod

class BaseSubParser(ABC):


    @abstractmethod
    async def public(self, symbol, timeframe, depth, feed) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def private(self, feed) -> dict:
        raise NotImplementedError