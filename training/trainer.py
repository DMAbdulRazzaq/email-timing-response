import pickle
import os
import time
from environment.base import BaseEnvironment
from agent.base import BaseAgent
from utils.logger import Logger


class Trainer:

    def __init__(
        self,
        env: BaseEnvironment,
        agent: BaseAgent,
        episodes: int = 1000,
        log_every: int = 100,
        checkpoint_every: int = 0,
        checkpoint_dir: str = "saved_models",
    ):
        self._env = env
        self._agent = agent
        self._episodes = episodes
        self._logger = Logger(log_every)
        self._checkpoint_every = checkpoint_every
        self._checkpoint_dir = checkpoint_dir

    def run(self) -> list[float]:
        self._logger.section(f"Training Started — {self._episodes:,} episodes")
        reward_history = []
        start = time.time()

        for ep in range(1, self._episodes + 1):
            reward = self._run_episode()
            reward_history.append(reward)
            self._agent.decay_epsilon()
            self._logger.episode(ep, reward, self._agent.epsilon, self._agent.q_table_size)

            # checkpoint — save mid-training so Colab crash doesn't lose progress
            if self._checkpoint_every and ep % self._checkpoint_every == 0:
                path = os.path.join(self._checkpoint_dir, f"checkpoint_ep{ep}.pkl")
                self._save_agent(path)
                elapsed = (time.time() - start) / 60
                print(f"  ⏱  {elapsed:.1f} min elapsed | checkpoint → {path}")

        elapsed = (time.time() - start) / 60
        self._logger.done(f"Training complete — {elapsed:.1f} min")
        return reward_history

    def _run_episode(self) -> float:
        state = self._env.reset()
        total, done = 0.0, False
        while not done:
            action = self._agent.select_action(state)
            next_state, reward, done = self._env.step(action)
            self._agent.learn(state, action, reward, next_state, done)
            state = next_state
            total += reward
        return total

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._save_agent(path)

    def _save_agent(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self._agent, f)
        print(f"  💾 Saved → {path}")

    @staticmethod
    def load(path: str) -> BaseAgent:
        with open(path, "rb") as f:
            agent = pickle.load(f)
        print(f"  ✅ Loaded ← {path}")
        return agent
