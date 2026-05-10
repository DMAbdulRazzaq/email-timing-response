import numpy as np

from data.email_data import Email
from environment.base import BaseEnvironment
from environment.reward import RewardCalculator
from simulation.simulator import EmailSimulator


class EmailEnvironment(BaseEnvironment):
    """
    The RL world.

    One episode = one inbox session of `max_steps` emails.
    Each step:
        1. Agent receives current email as state vector
        2. Agent picks an action (0-3)
        3. Environment calculates reward
        4. Environment loads next email as new state
        5. Episode ends after max_steps emails

    State space  : 5 continuous features  [priority, sender_importance,
                                            waiting_time, workload, time_of_day]
    Action space : 4 discrete actions     [reply_now, delay_reply,
                                            mark_important, archive]
    """

    STATE_SIZE = 5
    ACTION_SIZE = 4

    def __init__(self, simulator: EmailSimulator, max_steps: int = 50):
        self._simulator = simulator
        self._reward_calc = RewardCalculator()
        self._max_steps = max_steps

        self._current_email: Email = None
        self._step_count: int = 0

    # ── public interface ──────────────────────────────────────────

    def reset(self) -> np.ndarray:
        self._step_count = 0
        self._current_email = self._simulator.next_email()
        return self._current_email.to_state_vector()

    def step(self, action: int) -> tuple[np.ndarray, float, bool]:
        if self._current_email is None:
            raise RuntimeError("Call reset() before step().")

        reward = self._reward_calc.calculate(self._current_email, action)

        self._step_count += 1
        done = self._step_count >= self._max_steps
        self._current_email = self._simulator.next_email()
        next_state = self._current_email.to_state_vector()

        return next_state, reward, done

    # ── helpers ───────────────────────────────────────────────────

    @property
    def current_email(self) -> Email:
        return self._current_email

    @property
    def action_labels(self) -> dict:
        return {
            0: "reply_now",
            1: "delay_reply",
            2: "mark_important",
            3: "archive",
        }
