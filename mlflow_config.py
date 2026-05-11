"""
MLflow configuration for the Email Timing Response project.

Centralises experiment names, tracking URI, and model registry settings
so every pipeline script uses the same defaults.

Usage:
    from mlflow_config import MLflowConfig, init_mlflow
    init_mlflow()                          # sets tracking URI + experiment
    mlflow.start_run(run_name="my_run")    # then use mlflow as usual
"""

import os

import mlflow


class MLflowConfig:
    """All MLflow-related constants live here."""

    # Local file-store — override via MLFLOW_TRACKING_URI env var
    TRACKING_URI: str = os.environ.get(
        "MLFLOW_TRACKING_URI",
        f"file:///{os.path.abspath('mlruns').replace(os.sep, '/')}",
    )

    # Experiment names
    EXPERIMENT_DQN: str = "email-dqn-training"
    EXPERIMENT_QL: str = "email-qlearning-training"
    EXPERIMENT_INFERENCE: str = "email-inference-monitoring"

    # Registered model name in the MLflow Model Registry
    REGISTERED_MODEL_NAME: str = "email-dqn-agent"

    # Artifact sub-directories inside an MLflow run
    ARTIFACT_MODELS_DIR: str = "model_artifacts"
    ARTIFACT_PLOTS_DIR: str = "plots"
    ARTIFACT_METRICS_DIR: str = "metrics"


def init_mlflow(experiment_name: str = MLflowConfig.EXPERIMENT_DQN) -> str:
    """
    One-call setup: set tracking URI and create/get the experiment.

    Returns:
        experiment_id (str)
    """
    mlflow.set_tracking_uri(MLflowConfig.TRACKING_URI)
    experiment = mlflow.set_experiment(experiment_name)
    return experiment.experiment_id
