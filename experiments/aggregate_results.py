"""Aggregate experiment outputs and print Baseline vs RL comparison table.

Usage:
    python experiments/aggregate_results.py
Reads `data/experiments/summary.json` and writes `data/experiments/aggregate_table.json`.
"""

import json
import statistics
from pathlib import Path

RESULTS_DIR = Path("data/experiments")
SUMMARY_PATH = RESULTS_DIR / "summary.json"
OUT_PATH = RESULTS_DIR / "aggregate_table.json"


def safe_mean(xs):
    return statistics.mean(xs) if xs else None


def aggregate(policy_results):
    rewards = [r.get("total_reward") for r in policy_results if r.get("total_reward") is not None]
    pending_means = [
        (
            (sum(r.get("pending_over_time", [])) / len(r.get("pending_over_time", [])))
            if r.get("pending_over_time")
            else None
        )
        for r in policy_results
    ]
    # filter None
    pending_means = [p for p in pending_means if p is not None]

    avg_reward = safe_mean(rewards)
    avg_pending = safe_mean(pending_means)

    # try to extract additional metrics from final_info if present
    delays = []
    missed = []
    approvals = []
    for r in policy_results:
        fi = r.get("final_info", {}) or {}
        if isinstance(fi, dict):
            if "avg_response_delay" in fi:
                delays.append(fi.get("avg_response_delay"))
            if "missed_important" in fi:
                missed.append(fi.get("missed_important"))
            if "approval_rate" in fi:
                approvals.append(fi.get("approval_rate"))

    return {
        "avg_cumulative_reward": avg_reward,
        "avg_pending": avg_pending,
        "avg_response_delay": safe_mean(delays),
        "important_miss_rate": safe_mean(missed),
        "approval_rate": safe_mean(approvals),
    }


def main():
    if not SUMMARY_PATH.exists():
        print("Missing summary.json. Run experiments/run_experiments.py first.")
        return
    summary = json.loads(SUMMARY_PATH.read_text())
    baseline = summary.get("baseline", [])
    dqn = summary.get("dqn", [])

    agg = {
        "baseline": aggregate(baseline),
        "dqn": aggregate(dqn),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(agg, indent=2))
    print(f"Wrote aggregate table to {OUT_PATH}")
    print(json.dumps(agg, indent=2))


if __name__ == "__main__":
    main()
