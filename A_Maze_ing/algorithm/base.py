from abc import ABC, abstractmethod

class Algorithm(ABC):

    @abstractmethod
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def run(self):
        pass
