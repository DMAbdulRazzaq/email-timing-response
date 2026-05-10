"""
train_now.py
- Downloads Enron dataset if not present
- Trains Q-Learning + DQN for 100,000 episodes using GPU if available
- Saves both models to models/qlearning.pkl and models/dqn.pkl
"""

import os
import sys
import io

# Force UTF-8 output so logging never crashes on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_DIR)

import urllib.request
import tarfile

from config import Config
from simulation.simulator import EmailSimulator
from environment.email_env import EmailEnvironment
from agent.q_learning import QLearningAgent
from agent.dqn import DQNAgent
from training.trainer import Trainer

ENRON_DIR = os.path.join(PROJECT_DIR, "enron_dataset")
MODELS_DIR = os.path.join(PROJECT_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(ENRON_DIR, exist_ok=True)

DQN_PATH = os.path.join(MODELS_DIR, "dqn.pkl")
QL_PATH = os.path.join(MODELS_DIR, "qlearning.pkl")

EPISODES = 100_000
LOG_EVERY = 10_000

# ── Download Enron dataset if not present ─────────────────────────────────────
enron_has_files = any(True for _ in os.walk(ENRON_DIR) if _[2])

if not enron_has_files:
    print("Downloading Enron dataset from CMU (~1.7GB, please wait)...")
    TAR_PATH = os.path.join(PROJECT_DIR, "enron.tar.gz")

    class ProgressBar:
        def __init__(self):
            self._last = -1

        def __call__(self, block_num, block_size, total_size):
            if total_size > 0:
                pct = int(block_num * block_size * 100 / total_size)
                pct = min(pct, 100)
                if pct != self._last:
                    print(f"\r  Downloading... {pct}%", end="", flush=True)
                    self._last = pct

    urllib.request.urlretrieve(
        "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz", TAR_PATH, ProgressBar()
    )
    print("\nExtracting, this may take a few minutes...")
    with tarfile.open(TAR_PATH, "r:gz") as tar:
        tar.extractall(ENRON_DIR)
    print(f"Extracted to {ENRON_DIR}")
else:
    print(f"Enron dataset already present at {ENRON_DIR}")

# ── Email source ──────────────────────────────────────────────────────────────
from simulation.sources.enron import EnronEmailSource


def make_source():
    return EnronEmailSource(ENRON_DIR, max_emails=50_000)


print(f"\nLoading Enron emails...")

# ── Train Q-Learning ──────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  STEP 1/2: Training Q-Learning — {EPISODES:,} episodes")
print("=" * 60)

ql = QLearningAgent(
    alpha=Config.QL_ALPHA,
    gamma=Config.QL_GAMMA,
    epsilon=Config.QL_EPSILON,
    epsilon_min=Config.QL_EPSILON_MIN,
    epsilon_decay=Config.QL_EPSILON_DECAY,
)

source_ql = make_source()
sim_ql = EmailSimulator(source_ql)
env_ql = EmailEnvironment(sim_ql, max_steps=Config.MAX_STEPS)

trainer_ql = Trainer(env_ql, ql, episodes=EPISODES, log_every=LOG_EVERY)
trainer_ql.run()

# Use agent's own save() to avoid pickle lambda issue
ql.save(QL_PATH)
print(f"\nQ-Learning model saved -> {QL_PATH}\n")

# ── Train DQN ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"  STEP 2/2: Training DQN — {EPISODES:,} episodes (GPU if available)")
print("=" * 60)

dqn = DQNAgent(
    alpha=Config.DQN_ALPHA,
    gamma=Config.DQN_GAMMA,
    epsilon=Config.DQN_EPSILON,
    epsilon_min=Config.DQN_EPSILON_MIN,
    epsilon_decay=Config.DQN_EPSILON_DECAY,
    batch_size=Config.DQN_BATCH_SIZE,
    target_update=Config.DQN_TARGET_UPDATE,
    buffer_capacity=Config.DQN_BUFFER_CAP,
)

source_dqn = make_source()
sim_dqn = EmailSimulator(source_dqn)
env_dqn = EmailEnvironment(sim_dqn, max_steps=Config.MAX_STEPS)

trainer_dqn = Trainer(env_dqn, dqn, episodes=EPISODES, log_every=LOG_EVERY)
trainer_dqn.run()

# DQN uses full pickle (no lambda) so trainer.save() works fine
trainer_dqn.save(DQN_PATH)
print(f"\nDQN model saved -> {DQN_PATH}\n")

print("=" * 60)
print("  TRAINING COMPLETE!")
print(f"  Models saved in: {MODELS_DIR}")
print("  Now launch the web UI with:  python ui/web_ui.py")
print("=" * 60)
