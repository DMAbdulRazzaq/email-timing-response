"""
Trains the DQN locally on synthetic emails with the new normalized
state space, contextual reward structure, and score-based NLP.
Because the state vector is properly normalized now, this will
converge to perfect behavior in just ~10k episodes (seconds).

All metrics and artefacts are logged to MLflow automatically.
"""

import os
import pickle
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import mlflow

from agent.dqn import DQNAgent
from environment.email_env import EmailEnvironment
from mlflow_config import MLflowConfig, init_mlflow
from monitoring.mlflow_logger import (log_episode_metrics, log_model_artifact,
                                      log_reward_curve, log_training_params)
from simulation.simulator import EmailSimulator
from simulation.sources.synthetic import SyntheticEmailSource

EPISODES = 12_000
LOG_EVERY = 2_000
SAVE_PATH = "models/dqn.pkl"

print("=" * 60)
print("  Local DQN Training (Normalized State + Context Rewards)")
print(f"  Episodes : {EPISODES:,}")
print("=" * 60)

source = SyntheticEmailSource(seed=42)
sim = EmailSimulator(source)
env = EmailEnvironment(sim, max_steps=40)

ALPHA = 0.001
GAMMA = 0.95
EPSILON_START = 1.0
EPSILON_MIN = 0.01
EPSILON_DECAY = 0.9992
BATCH_SIZE = 64
TARGET_UPDATE = 500
BUFFER_CAP = 20_000

agent = DQNAgent(
    state_size=5,
    action_size=4,
    alpha=ALPHA,
    gamma=GAMMA,
    epsilon=EPSILON_START,
    epsilon_min=EPSILON_MIN,
    epsilon_decay=EPSILON_DECAY,
    batch_size=BATCH_SIZE,
    target_update=TARGET_UPDATE,
    buffer_capacity=BUFFER_CAP,
)

os.makedirs("models", exist_ok=True)
history = []
start = time.time()

# ── MLflow tracking ───────────────────────────────────────────────────────────
init_mlflow(MLflowConfig.EXPERIMENT_DQN)

with mlflow.start_run(run_name=f"local-dqn-{time.strftime('%Y%m%d_%H%M%S')}"):
    log_training_params(
        {
            "algorithm": "Double-DQN",
            "script": "train_local_dqn.py",
            "episodes": EPISODES,
            "source": "synthetic",
            "state_size": 5,
            "action_size": 4,
            "alpha": ALPHA,
            "gamma": GAMMA,
            "epsilon_start": EPSILON_START,
            "epsilon_min": EPSILON_MIN,
            "epsilon_decay": EPSILON_DECAY,
            "batch_size": BATCH_SIZE,
            "target_update": TARGET_UPDATE,
            "buffer_capacity": BUFFER_CAP,
            "max_steps_per_episode": 40,
        }
    )

    for ep in range(1, EPISODES + 1):
        state = env.reset()
        total = 0.0
        for _ in range(env._max_steps):
            action = agent.select_action(state)
            next_state, reward, done = env.step(action)
            agent.learn(state, action, reward, next_state, done)
            state = next_state
            total += reward
            if done:
                break

        agent.decay_epsilon()
        history.append(total)

        if ep % LOG_EVERY == 0:
            avg = sum(history[-LOG_EVERY:]) / LOG_EVERY
            elapsed = time.time() - start
            print(
                f"  Ep {ep:>6,} | avg reward: {avg:>+6.1f} | "
                f"eps: {agent.epsilon:.3f} | {elapsed:.1f}s"
            )
            # Log to MLflow at each checkpoint
            log_episode_metrics(
                episode=ep,
                reward=total,
                epsilon=agent.epsilon,
                avg_reward=avg,
            )

    # Final save
    agent.epsilon = agent.epsilon_min
    with open(SAVE_PATH, "wb") as f:
        pickle.dump(agent, f)

    elapsed = time.time() - start

    # ── Log final metrics and artefacts to MLflow ─────────────────────────────
    final_avg = sum(history[-500:]) / min(500, len(history))
    mlflow.log_metrics(
        {
            "final_avg_reward_500": final_avg,
            "final_epsilon": agent.epsilon,
            "training_seconds": round(elapsed, 2),
            "total_episodes": EPISODES,
        }
    )
    log_model_artifact(SAVE_PATH)
    log_reward_curve(history)
    mlflow.set_tag("script", "train_local_dqn")

    print(f"\n  Training finished in {elapsed:.1f} seconds  ->  {SAVE_PATH}")
    print("  📊 MLflow run logged. View at: http://127.0.0.1:5050")
