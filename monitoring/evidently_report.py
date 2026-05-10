import os
import sys
import warnings

import pandas as pd
from evidently.metric_preset import DataDriftPreset
from evidently.report import Report

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from environment.email_env import EmailEnvironment
from simulation.simulator import EmailSimulator
from simulation.sources.synthetic import SyntheticEmailSource

# Suppress scipy divide by zero warnings caused by empty bins in data drift statistical tests
warnings.filterwarnings("ignore", category=RuntimeWarning)

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

    print("3. Generating Evidently Data Drift Report...")
    from evidently.options import ColorOptions
    color_scheme = ColorOptions(
        primary_color="#22c55e",
        fill_color="#06b6d4",
        zero_line_color="#a855f7",
        current_data_color="#06b6d4",
        reference_data_color="#64748b"
    )
    report = Report(metrics=[DataDriftPreset()], options=[color_scheme])
    report.run(reference_data=reference_data, current_data=current_data)

    os.makedirs("logs", exist_ok=True)
    out_path = "logs/evidently_drift_report.html"
    report.save_html(out_path)

    # Inject dark theme CSS to match index.html
    with open(out_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    dark_css = """
    <style>
        body, .MuiPaper-root { 
            background-color: #020617 !important; 
            color: #f1f5f9 !important; 
        }
        body {
            background-image:
                radial-gradient(ellipse 80% 60% at 10% 0%, rgba(59,130,246,0.08) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 90% 100%, rgba(168,85,247,0.06) 0%, transparent 50%),
                radial-gradient(ellipse 50% 50% at 50% 50%, rgba(34,197,94,0.03) 0%, transparent 70%) !important;
            background-attachment: fixed !important;
        }
        .MuiTypography-root { color: #f1f5f9 !important; }
        .MuiTableCell-root { color: #f1f5f9 !important; border-bottom: 1px solid rgba(255,255,255,0.07) !important; }
        .MuiGrid-root { background-color: transparent !important; }
        .MuiCard-root { background-color: #0f172a !important; border: 1px solid rgba(255,255,255,0.07) !important; box-shadow: none !important; }
        svg text { fill: #94a3b8 !important; }
        .MuiButtonBase-root { color: #06b6d4 !important; }
        .MuiChip-root { background-color: rgba(34,197,94,0.15) !important; color: #22c55e !important; }
        .MuiAccordionSummary-root { background-color: #0a0f1e !important; color: #f1f5f9 !important; }
        .MuiAccordionDetails-root { background-color: #020617 !important; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
    </style>
    """
    html_content = html_content.replace("</head>", f"{dark_css}</head>")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[SUCCESS] Report saved successfully: {out_path}")
    print("Open this file in your browser to view interactive drift metrics.")


if __name__ == "__main__":
    main()
