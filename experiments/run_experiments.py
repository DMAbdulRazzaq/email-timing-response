"""Run experiments comparing heuristic baseline vs DQN policy.

Produces JSONL results and queue-length CSVs for plotting.

Usage:
    python experiments/run_experiments.py --config experiments/exp_config.yaml
"""

import argparse
import json
import os
import random
import time
from pathlib import Path

import yaml

RESULTS_DIR = Path("data/experiments")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_episode(env, policy, max_steps):
    """Run a single episode in the provided env using policy.

    env must implement: reset() -> obs, step(action) -> (obs, reward, done, info)
    policy is a callable: action = policy(obs)
    Returns: dict with metrics and queue length over time
    """
    obs = env.reset()
    total_reward = 0.0
    step = 0
    pending_over_time = []
    start_time = time.time()
    info = {}
    while step < max_steps:
        action = policy(obs)
        obs, reward, done, info = env.step(action)
        total_reward += reward
        pending = (
            getattr(info, "pending", None)
            or info.get("pending", None)
            or info.get("queue_length", 0)
        )
        pending_over_time.append(int(pending))
        step += 1
        if done:
            break
    elapsed = time.time() - start_time
    return {
        "total_reward": total_reward,
        "steps": step,
        "elapsed": elapsed,
        "pending_over_time": pending_over_time,
        "final_info": info,
    }


def load_policy_from_checkpoint(checkpoint_path):
    # Lightweight placeholder: user will supply their DQN policy loader
    def random_policy(obs):
        return random.choice([0, 1, 2])

    return random_policy


def heuristic_policy(obs):
    # Placeholder heuristic: reply to urgent, otherwise wait
    # policy action codes should match env
    if obs.get("urgent", False):
        return 1  # reply
    return 0  # wait


def main(cfg_path):
    cfg = yaml.safe_load(open(cfg_path))

    # Load environment by import string if provided
    env_module = cfg.get("env_module")
    env_class = cfg.get("env_class")
    if env_module and env_class:
        mod = __import__(env_module, fromlist=[env_class])
        Env = getattr(mod, env_class)
        env_args = cfg.get("env_args", {})
        env = Env(**env_args)
    else:
        raise RuntimeError("Please provide env_module and env_class in config")

    episodes = cfg.get("episodes", 20)
    max_steps = cfg.get("max_steps", 500)
    seed = cfg.get("seed", 1234)
    random.seed(seed)

    # Prepare policies
    baseline_policy = heuristic_policy
    dqn_policy = None
    if cfg.get("dqn_checkpoint"):
        dqn_policy = load_policy_from_checkpoint(cfg["dqn_checkpoint"])
    else:
        dqn_policy = baseline_policy

    all_results = {"baseline": [], "dqn": []}

    for ep in range(episodes):
        res_b = run_episode(env, baseline_policy, max_steps)
        all_results["baseline"].append(res_b)
        res_d = run_episode(env, dqn_policy, max_steps)
        all_results["dqn"].append(res_d)

        # save intermediate
        outp = RESULTS_DIR / f"results_ep_{ep}.jsonl"
        with open(outp, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"episode": ep, "baseline": res_b, "dqn": res_d}) + "\n")

    # Save summary
    summary_path = RESULTS_DIR / "summary.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(all_results, fh, indent=2)

    print("Saved results to", RESULTS_DIR)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="experiments/exp_config.yaml")
    args = p.parse_args()
    main(args.config)
