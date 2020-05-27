from abc import ABC, abstractmethod

class BaseSubParser(ABC):


    @abstractmethod
    async def public(self, pairs, timeframe, depth, feed) -> dict:
        raise NotImplementedError

    @abstractmethod
    async def private(self, pairs, feed) -> dict:
        raise NotImplementedError