from abc import ABC, abstractmethod
import numpy as np


class BaseAgent(ABC):
    @abstractmethod
    def select_action(self, state: np.ndarray) -> int:
        pass

    @abstractmethod
    def learn(self, state, action, reward, next_state, done) -> None:
        pass
