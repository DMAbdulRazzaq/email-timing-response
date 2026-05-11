"""
Tests for MLflow integration.

Validates that MLflow configuration, logger utilities, and tracking
work correctly without requiring a running MLflow server.

Run: pytest tests/test_mlflow.py -v
"""

import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── MLflowConfig tests ───────────────────────────────────────────────────────


class TestMLflowConfig:
    def test_config_has_required_attributes(self):
        from mlflow_config import MLflowConfig

        assert hasattr(MLflowConfig, "TRACKING_URI")
        assert hasattr(MLflowConfig, "EXPERIMENT_DQN")
        assert hasattr(MLflowConfig, "EXPERIMENT_QL")
        assert hasattr(MLflowConfig, "EXPERIMENT_INFERENCE")
        assert hasattr(MLflowConfig, "REGISTERED_MODEL_NAME")

    def test_tracking_uri_format(self):
        from mlflow_config import MLflowConfig

        uri = MLflowConfig.TRACKING_URI
        # Should be a file URI or an HTTP URI
        assert uri.startswith("file:///") or uri.startswith(
            "http"
        ), f"Tracking URI should start with file:/// or http, got: {uri}"

    def test_experiment_names_are_strings(self):
        from mlflow_config import MLflowConfig

        assert isinstance(MLflowConfig.EXPERIMENT_DQN, str)
        assert isinstance(MLflowConfig.EXPERIMENT_QL, str)
        assert isinstance(MLflowConfig.EXPERIMENT_INFERENCE, str)

    def test_experiment_names_not_empty(self):
        from mlflow_config import MLflowConfig

        assert len(MLflowConfig.EXPERIMENT_DQN) > 0
        assert len(MLflowConfig.EXPERIMENT_QL) > 0
        assert len(MLflowConfig.EXPERIMENT_INFERENCE) > 0


# ── init_mlflow tests ────────────────────────────────────────────────────────


class TestInitMLflow:
    def test_init_mlflow_returns_experiment_id(self):
        """init_mlflow should return a valid experiment ID string."""
        from mlflow_config import init_mlflow

        # Use a temp directory to avoid polluting project mlruns
        with tempfile.TemporaryDirectory() as tmp:
            uri = f"file:///{tmp.replace(os.sep, '/')}"
            with patch("mlflow_config.MLflowConfig.TRACKING_URI", uri):
                exp_id = init_mlflow("test-experiment")
                assert isinstance(exp_id, str)
                assert len(exp_id) > 0

    def test_init_mlflow_sets_tracking_uri(self):
        import mlflow

        from mlflow_config import init_mlflow

        with tempfile.TemporaryDirectory() as tmp:
            uri = f"file:///{tmp.replace(os.sep, '/')}"
            with patch("mlflow_config.MLflowConfig.TRACKING_URI", uri):
                init_mlflow("test-experiment")
                assert mlflow.get_tracking_uri() == uri


# ── MLflow logger helper tests ───────────────────────────────────────────────


class TestMLflowLogger:
    def test_log_training_params(self):
        """log_training_params should call mlflow.log_params."""
        from monitoring.mlflow_logger import log_training_params

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            params = {"alpha": 0.001, "episodes": 10000}
            log_training_params(params)
            mock_mlflow.log_params.assert_called_once_with(params)

    def test_log_episode_metrics_basic(self):
        """log_episode_metrics should call mlflow.log_metrics with step."""
        from monitoring.mlflow_logger import log_episode_metrics

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            log_episode_metrics(episode=100, reward=5.5, epsilon=0.5)
            mock_mlflow.log_metrics.assert_called_once()
            call_args = mock_mlflow.log_metrics.call_args
            metrics = call_args[0][0]
            assert "episode_reward" in metrics
            assert "epsilon" in metrics
            assert metrics["episode_reward"] == 5.5
            assert metrics["epsilon"] == 0.5
            assert call_args[1]["step"] == 100

    def test_log_episode_metrics_with_optional_fields(self):
        from monitoring.mlflow_logger import log_episode_metrics

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            log_episode_metrics(episode=200, reward=3.0, epsilon=0.3, avg_reward=4.5, loss=0.01)
            metrics = mock_mlflow.log_metrics.call_args[0][0]
            assert "avg_reward" in metrics
            assert "loss" in metrics

    def test_log_evaluation_results(self):
        from monitoring.mlflow_logger import log_evaluation_results

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            results = {
                "mean_reward": 10.5,
                "accuracy": 85.2,
                "min_reward": -2.0,
                "max_reward": 25.0,
            }
            log_evaluation_results(results)
            mock_mlflow.log_metrics.assert_called_once()
            metrics = mock_mlflow.log_metrics.call_args[0][0]
            assert metrics["eval_mean_reward"] == 10.5
            assert metrics["eval_accuracy"] == 85.2

    def test_log_model_artifact_existing_file(self):
        from monitoring.mlflow_logger import log_model_artifact

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            # Create a temp file to simulate a model
            with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
                f.write(b"fake model data")
                tmp_path = f.name
            try:
                log_model_artifact(tmp_path)
                mock_mlflow.log_artifact.assert_called_once()
            finally:
                os.unlink(tmp_path)

    def test_log_model_artifact_missing_file(self):
        from monitoring.mlflow_logger import log_model_artifact

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            log_model_artifact("/nonexistent/file.pt")
            mock_mlflow.log_artifact.assert_not_called()

    def test_log_drift_report_insufficient_data(self):
        from monitoring.mlflow_logger import log_drift_report

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            log_drift_report({"status": "insufficient_data", "n_samples": 10})
            mock_mlflow.log_metric.assert_not_called()

    def test_log_drift_report_with_features(self):
        from monitoring.mlflow_logger import log_drift_report

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            report = {
                "status": "ok",
                "features": {
                    "priority_norm": {"psi": 0.05, "z_score": 0.3},
                    "workload_norm": {"psi": 0.02, "z_score": 0.1},
                },
                "alerts": [],
            }
            log_drift_report(report)
            # Should log drift_status + per-feature PSI/z metrics
            assert mock_mlflow.log_metric.call_count >= 5

    def test_log_inference_metrics(self):
        from monitoring.mlflow_logger import log_inference_metrics

        with patch("monitoring.mlflow_logger.mlflow") as mock_mlflow:
            snap = {
                "total_predictions": 100,
                "avg_confidence": 0.85,
                "latency_p50_ms": 1.2,
                "latency_p95_ms": 5.6,
            }
            log_inference_metrics(snap)
            mock_mlflow.log_metrics.assert_called_once()
            metrics = mock_mlflow.log_metrics.call_args[0][0]
            assert metrics["inf_total_predictions"] == 100
