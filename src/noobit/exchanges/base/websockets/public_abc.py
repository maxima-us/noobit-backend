from abc import ABC, abstractmethod

class PublicFeedReaderABC(ABC):


    @abstractmethod
    async def route_message(self, msg):
        """route message to appropriate method to publish
        one of coros :
            - publish_heartbeat
            - publish_system_status
            - publish_subscription_status
            - publish_data

        To be implemented by ExchangeFeedReader
        """
        raise NotImplementedError

