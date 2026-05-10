import os
import sys

import pandas as pd
from evidently.metric_preset import DataDriftPreset, DataQualityPreset
from evidently.report import Report

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from environment.email_env import EmailEnvironment
from simulation.simulator import EmailSimulator
from simulation.sources.synthetic import SyntheticEmailSource

FEATURE_NAMES = [
    "priority_norm",
    "sender_importance_norm",
    "waiting_time_norm",
    "workload_norm",
    "time_of_day_norm",
]


def generate_data(num_samples: int, drift_multiplier: float = 1.0) -> pd.DataFrame:
    """Generate state vectors using the simulator."""
    source = SyntheticEmailSource(seed=42)
    sim = EmailSimulator(source)
    env = EmailEnvironment(sim, max_steps=num_samples)

    states = []
    state = env.reset()
    states.append(state)

    for _ in range(num_samples - 1):
        action = 0  # Dummy action
        next_state, _, done = env.step(action)
        if done:
            next_state = env.reset()
        
        # Apply synthetic drift for demonstration
        if drift_multiplier != 1.0:
            next_state = [min(1.0, max(0.0, s * drift_multiplier)) for s in next_state]
            
        states.append(next_state)

    return pd.DataFrame(states, columns=FEATURE_NAMES)


def main():
    print("1. Generating Reference Data (Normal)")
    reference_data = generate_data(1000, drift_multiplier=1.0)

    print("2. Generating Current Data (With Simulated Drift)")
    current_data = generate_data(1000, drift_multiplier=1.3)

    print("3. Generating Evidently Data Drift & Quality Report...")
    report = Report(
        metrics=[
            DataQualityPreset(),
            DataDriftPreset(),
        ]
    )
    report.run(reference_data=reference_data, current_data=current_data)

    os.makedirs("logs", exist_ok=True)
    out_path = "logs/evidently_drift_report.html"
    report.save_html(out_path)

    print(f"✅ Report saved successfully: {out_path}")
    print("Open this file in your browser to view interactive drift metrics.")


if __name__ == "__main__":
    main()
