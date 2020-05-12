from abc import ABC, abstractmethod

class BaseSubParser(ABC):


    @abstractmethod
    def parse(self, pairs, timeframe, depth, feed) -> dict:
        raise NotImplementedError