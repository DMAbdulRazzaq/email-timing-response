from abc import ABC, abstractmethod

import numpy as np


class BaseEnvironment(ABC):
    """
    Standard RL environment interface (mirrors OpenAI Gym convention).

    Every environment must implement:
        reset() → initial state
        step()  → next state, reward, done flag
    """

    @abstractmethod
    def reset(self) -> np.ndarray:
        """Reset environment to start of episode. Returns initial state."""

    @abstractmethod
    def step(self, action: int) -> tuple[np.ndarray, float, bool]:
        """
        Apply action. Returns (next_state, reward, done).
            next_state : state vector of the next email
            reward     : float reward for this action
            done       : True when episode ends
        """
