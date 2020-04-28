from abc import ABC, abstractmethod


# check below to enforce attributes on subclass of BaseClass
# https://stackoverflow.com/questions/23831510/abstract-attribute-not-property


class BaseResponseParser(ABC):


    @abstractmethod
    def order(self, response, mode):
        raise NotImplementedError
