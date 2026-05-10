import os
import pickle
import time

import mlflow

from agent.base import BaseAgent
from environment.base import BaseEnvironment
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

        with mlflow.start_run(nested=True):
            mlflow.log_param("episodes", self._episodes)
            if hasattr(self._agent, "gamma"):
                mlflow.log_param("gamma", self._agent.gamma)
            if hasattr(self._agent, "alpha"):
                mlflow.log_param("alpha", self._agent.alpha)

            for ep in range(1, self._episodes + 1):
                reward = self._run_episode()
                reward_history.append(reward)
                self._agent.decay_epsilon()
                self._logger.episode(ep, reward, self._agent.epsilon, self._agent.q_table_size)
                
                # MLflow metrics (log every N episodes to avoid slowing down training)
                if ep % self._logger.log_every == 0:
                    avg_reward = sum(reward_history[-self._logger.log_every:]) / self._logger.log_every
                    mlflow.log_metric("avg_reward", avg_reward, step=ep)
                    mlflow.log_metric("epsilon", self._agent.epsilon, step=ep)

                # checkpoint — save mid-training so Colab crash doesn't lose progress
                if self._checkpoint_every and ep % self._checkpoint_every == 0:
                    path = os.path.join(self._checkpoint_dir, f"checkpoint_ep{ep}.pkl")
                    self._save_agent(path)
                    mlflow.log_artifact(path)
                    elapsed = (time.time() - start) / 60
                    print(f"  ⏱  {elapsed:.1f} min elapsed | checkpoint → {path}")

            elapsed = (time.time() - start) / 60
            self._logger.done(f"Training complete — {elapsed:.1f} min")
            mlflow.log_metric("total_training_time_min", elapsed)
            
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
        if mlflow.active_run():
            mlflow.log_artifact(path)

    @staticmethod
    def load(path: str) -> BaseAgent:
        with open(path, "rb") as f:
            agent = pickle.load(f)
        print(f"  ✅ Loaded ← {path}")
        return agent
