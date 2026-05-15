"""Plot pending emails (queue length) over time for baseline vs RL.

Reads JSON summary produced by `experiments/run_experiments.py` at `data/experiments/summary.json`.
Generates `data/experiments/queue_length_comparison.png`.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

RESULTS_PATH = Path("data/experiments/summary.json")
OUT_PATH = Path("data/experiments/queue_length_comparison.png")


def load_summary(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def average_trace(traces):
    # traces: list of lists
    maxlen = max(len(t) for t in traces)
    aligned = [t + [t[-1]] * (maxlen - len(t)) for t in traces]
    return np.mean(aligned, axis=0), np.std(aligned, axis=0)


def plot(summary):
    baseline_traces = [r["pending_over_time"] for r in summary.get("baseline", [])]
    dqn_traces = [r["pending_over_time"] for r in summary.get("dqn", [])]

    if not baseline_traces or not dqn_traces:
        print("No traces found in summary.json; run experiments first")
        return

    base_mean, base_std = average_trace(baseline_traces)
    dqn_mean, dqn_std = average_trace(dqn_traces)

    x = range(len(base_mean))
    plt.figure(figsize=(10, 5))
    plt.plot(x, base_mean, label="Heuristic Baseline", color="#d9534f")
    plt.fill_between(x, base_mean - base_std, base_mean + base_std, alpha=0.2, color="#d9534f")
    plt.plot(x, dqn_mean, label="DQN Policy", color="#0275d8")
    plt.fill_between(x, dqn_mean - dqn_std, dqn_mean + dqn_std, alpha=0.2, color="#0275d8")
    plt.xlabel("Step")
    plt.ylabel("Pending Emails (Queue Length)")
    plt.title("Pending Emails Over Time: Baseline vs DQN Policy")
    plt.legend()
    plt.grid(alpha=0.2)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT_PATH, bbox_inches="tight", dpi=150)
    print(f"Saved queue length comparison plot to {OUT_PATH}")


if __name__ == "__main__":
    if not RESULTS_PATH.exists():
        print("Missing results summary.json — run experiments/run_experiments.py first")
    else:
        summary = load_summary(RESULTS_PATH)
        plot(summary)
