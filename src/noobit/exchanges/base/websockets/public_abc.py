from abc import ABC, abstractmethod

class PublicFeedReaderABC(ABC):


    @abstractmethod
    async def route_message(self, msg):
        raise NotImplementedError

