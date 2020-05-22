from abc import ABC, abstractmethod

class PrivateFeedReaderABC(ABC):


    @abstractmethod
    async def route_message(self, msg):
        raise NotImplementedError

