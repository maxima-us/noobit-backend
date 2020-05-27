from abc import ABC, abstractmethod



class StratABC(ABC):


    @abstractmethod
    def user_setup(self):
        raise NotImplementedError


    @abstractmethod
    def long_condition(self):
        raise NotImplementedError


    @abstractmethod
    def short_condition(self):
        raise NotImplementedError


    @abstractmethod
    def user_tick(self):
        raise NotImplementedError
