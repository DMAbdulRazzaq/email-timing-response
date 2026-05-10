"""
Trains the DQN locally on synthetic emails with the new normalized 
state space, contextual reward structure, and score-based NLP.
Because the state vector is properly normalized now, this will 
converge to perfect behavior in just ~10k episodes (seconds).
"""

import os, sys, pickle, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import torch
import numpy as np

from simulation.sources.synthetic import SyntheticEmailSource
from simulation.simulator import EmailSimulator
from environment.email_env import EmailEnvironment
from agent.dqn import DQNAgent
from environment.reward import RewardCalculator

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
agent = DQNAgent(
    state_size=5,
    action_size=4,
    alpha=0.001,
    gamma=0.95,
    epsilon=1.0,
    epsilon_min=0.01,
    epsilon_decay=0.9992,  # fully greedy around ep 6000
    batch_size=64,
    target_update=500,
    buffer_capacity=20_000,
)

os.makedirs("models", exist_ok=True)
history = []
start = time.time()

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

# Final save
agent.epsilon = agent.epsilon_min
with open(SAVE_PATH, "wb") as f:
    pickle.dump(agent, f)

elapsed = time.time() - start
print(f"\n  Training finished in {elapsed:.1f} seconds  ->  {SAVE_PATH}")
