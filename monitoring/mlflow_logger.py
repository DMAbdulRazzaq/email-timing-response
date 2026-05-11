"""
MLflow helper utilities for logging training metrics, model artifacts,
and inference-time monitoring data.

This module wraps common MLflow calls so pipeline scripts stay clean.

Usage:
    from monitoring.mlflow_logger import (
        log_training_params,
        log_episode_metrics,
        log_model_artifact,
        log_evaluation_results,
        log_reward_curve,
    )
"""

import os
import tempfile
from typing import Any, Dict, List, Optional

import mlflow
import mlflow.pytorch

from mlflow_config import MLflowConfig


# ── Training helpers ──────────────────────────────────────────────────────────


def log_training_params(params: Dict[str, Any]) -> None:
    """Log all hyper-parameters at the start of a training run."""
    mlflow.log_params(params)


def log_episode_metrics(
    episode: int,
    reward: float,
    epsilon: float,
    avg_reward: Optional[float] = None,
    loss: Optional[float] = None,
) -> None:
    """Log per-episode scalar metrics."""
    metrics = {
        "episode_reward": reward,
        "epsilon": epsilon,
    }
    if avg_reward is not None:
        metrics["avg_reward"] = avg_reward
    if loss is not None:
        metrics["loss"] = loss
    mlflow.log_metrics(metrics, step=episode)


def log_evaluation_results(results: Dict[str, Any]) -> None:
    """Log evaluation metrics (mean reward, accuracy, etc.)."""
    mlflow.log_metrics(
        {
            "eval_mean_reward": results["mean_reward"],
            "eval_accuracy": results["accuracy"],
            "eval_min_reward": results["min_reward"],
            "eval_max_reward": results["max_reward"],
        }
    )


def log_model_artifact(
    weights_path: str,
    artifact_dir: str = MLflowConfig.ARTIFACT_MODELS_DIR,
) -> None:
    """Log a saved model file (e.g. .pt or .pkl) as an MLflow artifact."""
    if os.path.exists(weights_path):
        mlflow.log_artifact(weights_path, artifact_path=artifact_dir)


def log_reward_curve(
    reward_history: List[float],
    save_path: str = "reward_curve_mlflow.png",
) -> None:
    """
    Generate a reward-vs-episode plot and log it as an artifact.
    Uses matplotlib directly to avoid importing the Evaluator class.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        episodes = range(1, len(reward_history) + 1)
        window = min(50, len(reward_history) // 5 or 1)
        rolling = np.convolve(
            reward_history, np.ones(window) / window, mode="valid"
        )

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(
            episodes,
            reward_history,
            color="#94a3b8",
            alpha=0.4,
            linewidth=0.8,
            label="Raw reward",
        )
        if len(rolling) > 0:
            ax.plot(
                episodes[window - 1:],
                rolling,
                color="#38bdf8",
                linewidth=2.2,
                label=f"Rolling avg (w={window})",
            )
        ax.axhline(0, color="#475569", linewidth=0.8, linestyle="--")
        ax.set_xlabel("Episode")
        ax.set_ylabel("Total Reward")
        ax.set_title("DQN Agent — Reward vs Episodes")
        ax.legend()
        ax.grid(True, alpha=0.2)
        fig.tight_layout()

        # Save to temp file and log as artifact
        tmp_dir = tempfile.mkdtemp()
        plot_path = os.path.join(tmp_dir, save_path)
        fig.savefig(plot_path, dpi=150)
        plt.close(fig)
        mlflow.log_artifact(plot_path, artifact_path=MLflowConfig.ARTIFACT_PLOTS_DIR)

    except Exception as e:
        print(f"  ⚠  Could not log reward curve: {e}")


def log_drift_report(drift_report: Dict[str, Any]) -> None:
    """Log drift detection results as MLflow metrics and a JSON artifact."""
    import json
    import tempfile

    if drift_report.get("status") == "insufficient_data":
        return

    # Log aggregate drift status
    status_map = {"ok": 0, "warning": 1, "critical": 2}
    mlflow.log_metric(
        "drift_status",
        status_map.get(drift_report.get("status", "ok"), 0),
    )

    # Log per-feature PSI
    for feat_name, feat_data in drift_report.get("features", {}).items():
        mlflow.log_metric(f"drift_psi_{feat_name}", feat_data.get("psi", 0.0))
        mlflow.log_metric(
            f"drift_z_{feat_name}", abs(feat_data.get("z_score", 0.0))
        )

    # Log full report as JSON artifact
    tmp_dir = tempfile.mkdtemp()
    report_path = os.path.join(tmp_dir, "drift_report.json")
    with open(report_path, "w") as f:
        json.dump(drift_report, f, indent=2)
    mlflow.log_artifact(report_path, artifact_path=MLflowConfig.ARTIFACT_METRICS_DIR)


def log_inference_metrics(metrics_snapshot: Dict[str, Any]) -> None:
    """Log inference-time metrics (counts, latency, confidence) to MLflow."""
    import json
    import tempfile

    flat = {
        "inf_total_predictions": metrics_snapshot.get("total_predictions", 0),
        "inf_avg_confidence": metrics_snapshot.get("avg_confidence", 0.0),
        "inf_latency_p50_ms": metrics_snapshot.get("latency_p50_ms", 0.0),
        "inf_latency_p95_ms": metrics_snapshot.get("latency_p95_ms", 0.0),
    }
    mlflow.log_metrics(flat)

    # Also log full snapshot as artifact
    tmp_dir = tempfile.mkdtemp()
    snap_path = os.path.join(tmp_dir, "inference_metrics.json")
    with open(snap_path, "w") as f:
        json.dump(metrics_snapshot, f, indent=2)
    mlflow.log_artifact(snap_path, artifact_path=MLflowConfig.ARTIFACT_METRICS_DIR)
