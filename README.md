# Email Timing Response — MLOps Project

> **Course:** Machine Learning Operations (24AM6AEMLO) | VTU / BMSCE, A.Y 2025-26  
> **Department:** Machine Learning — B.E. in Artificial Intelligence and Machine Learning

A **Deep Q-Network (DQN)** reinforcement-learning agent that learns the optimal time to respond to emails by maximising a reward signal based on email priority, sender importance, workload, and time of day.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Quick Start](#quick-start)
5. [Training the Agent](#training-the-agent)
6. [MLflow Experiment Tracking](#mlflow-experiment-tracking)
7. [Running the Inference API](#running-the-inference-api)
8. [Running Tests](#running-tests)
9. [Docker Deployment](#docker-deployment)
10. [Monitoring](#monitoring)
11. [Model Versioning](#model-versioning)
12. [CI/CD Pipeline](#cicd-pipeline)

---

## Project Overview

| Dimension  | Detail |
|------------|--------|
| **State**  | 5 features: priority, sender importance, waiting time, workload, time of day (normalized to [0,1]) |
| **Actions**| 4: `reply_now`, `delay_reply`, `mark_important`, `archive` |
| **Algorithm** | Double DQN with experience replay and target network |
| **Reward** | Custom function rewarding timely replies to high-priority mail |

> Next-stage architecture for thread-aware Gmail automation, Gemini intelligence,
> human approval, feedback rewards, and analytics is documented in
> [NEXT_STAGE_ARCHITECTURE.md](NEXT_STAGE_ARCHITECTURE.md).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        EMAIL TIMING RESPONSE                        │
└─────────────────────────────────────────────────────────────────────┘

  DATA LAYER                 TRAINING LAYER            INFERENCE LAYER
  ──────────                 ──────────────            ───────────────
  ┌──────────┐               ┌───────────┐             ┌─────────────┐
  │ Enron    │               │ Trainer   │             │  FastAPI    │
  │ Dataset  ├──►EmailSim───►│  (DQN)   ├──►models/──►│  /predict   │
  └──────────┘               └─────┬─────┘             └──────┬──────┘
  ┌──────────┐                     │                          │
  │Synthetic │               ┌─────▼─────┐             ┌──────▼──────┐
  │Generator │               │  Email    │             │  Monitoring │
  └──────────┘               │  Environ- │             │  Metrics    │
                             │  ment     │             │  Drift      │
                             └─────┬─────┘             │  Logging    │
                                   │                   └─────────────┘
                             ┌─────▼─────┐
                             │  Reward   │
                             │Calculator │
                             └───────────┘

  MLOPS LAYER
  ───────────
  GitHub Actions: Lint ──► Tests ──► Docker Build ──► Deploy (staging)

  EXPERIMENT TRACKING
  ───────────────────
  MLflow: Params ──► Metrics ──► Artifacts ──► Model Registry
          │              │            │
          ▼              ▼            ▼
     Hyperparams   Episode Rewards  Weights (.pt)
     Source Info    Avg Reward       Reward Curves
     Algorithm     Epsilon Decay    Drift Reports
```

### Component Responsibilities

| Component | Role |
|-----------|------|
| `agent/dqn.py` | Double DQN — QNetwork, ReplayBuffer, DQNAgent |
| `environment/email_env.py` | RL environment (state/action/reward loop) |
| `environment/reward.py` | Domain-specific reward shaping |
| `simulation/` | Email stream sources (synthetic, Enron, NLP) |
| `training/trainer.py` | Episode loop with checkpointing |
| `app/main.py` | FastAPI inference service |
| `monitoring/` | Structured logging, metrics, drift detection |
| `monitoring/mlflow_logger.py` | MLflow logging helpers for training & inference |
| `mlflow_config.py` | Centralised MLflow configuration |
| `pipelines/` | End-to-end training and batch inference |
| `tests/` | pytest unit + integration tests |
| `docker/Dockerfile` | Two-stage container image |
| `.github/workflows/ci_cd.yml` | Lint → Test → Build → Deploy |

---

## Project Structure

```
email_timing_response/
│
├── app/                          # FastAPI inference service
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   └── gmail_integration.py
│
├── monitoring/                   # Observability
│   ├── __init__.py
│   ├── drift_detection.py
│   ├── logging_config.py
│   ├── metrics.py
│   └── mlflow_logger.py          # MLflow logging utilities
│
├── tests/                        # pytest test suite
│   ├── __init__.py
│   ├── test_model.py
│   ├── test_api.py
│   ├── test_data.py
│   └── test_mlflow.py            # MLflow integration tests
│
├── pipelines/                    # MLOps pipelines (MLflow-tracked)
│   ├── __init__.py
│   ├── training_pipeline.py      # Full DQN training + MLflow
│   ├── inference_pipeline.py     # Batch inference + MLflow
│   ├── train_local_dqn.py        # Quick local training + MLflow
│   └── train_now.py              # Enron full training + MLflow
│
├── .github/workflows/ci_cd.yml   # CI/CD
├── docker/Dockerfile             # Container image
│
├── agent/                        # DQN agent 
│   ├── __init__.py
│   ├── base.py
│   ├── dqn.py
|   └── q_learning.py
│
├── data/                         # Email dataclass + Enron loader
│   ├── __init__.py
│   ├── email_data.py
│   └── enron_loader.py
│
├── environment/                  # RL environment
│   ├── __init__.py
│   ├── base.py
│   ├── email_env.py
|   └── reward.py
│
├── models/                       # Saved weights
│   ├── dqn_weights.pt
│   └── dqn.pkl
│
├── simulation/                   # Email simulators 
│   ├── sources/
│   ├── __init__.py
│   └── simulator.py
│
├── training/                     # Trainer + evaluator
│   ├── evaluator.py
|   └── trainer.py
│
├── ui/                           # Flask web UI
│   ├── templates/
│   │   ├── index.html
│   └── web_ui.py
│
├── utils/                        # Logger
│   ├── __init__.py
│   └── logger.py
│
├── scripts/                      # Utility scripts
│   └── mlflow_server.py          # Launch MLflow tracking UI
│
├── mlruns/                       # MLflow local tracking store (git-ignored)
│
├── .gitignore
├── .dockerignore
├── docker-compose.yml
├── pytest.ini
├── config.py
├── mlflow_config.py              # MLflow configuration
├── main.py
├── requirements.txt
├── README.md
└── DEPLOYMENT.md
```

---

## Quick Start

```bash
git clone <repo-url> && cd email_timing_response

# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate

# You should see:
(venv)

# Install dependencies
pip install -r requirements.txt

# Train (with MLflow tracking)
python pipelines/training_pipeline.py --episodes 10000

# View training runs in MLflow UI
python scripts/mlflow_server.py
# Open http://127.0.0.1:5050 in your browser

# Serve
uvicorn app.main:app --reload --port 8000

# Predict
## Linux
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"subject":"Urgent meeting","sender":"boss@co.com","priority":3,
       "sender_importance":3,"waiting_time":5,"workload":2,"time_of_day":14}'

## Windows
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:8000/predict" `
  -ContentType "application/json" `
  -Body '{
    "subject":"Urgent meeting",
    "sender":"boss@co.com",
    "priority":3,
    "sender_importance":3,
    "waiting_time":5,
    "workload":2,
    "time_of_day":14
  }'
```

---

## Training the Agent

```bash
# Full pipeline (versioned checkpoints + MLflow)
python pipelines/training_pipeline.py --episodes 10000 --source synthetic

# Train without MLflow tracking
python pipelines/training_pipeline.py --episodes 10000 --no-mlflow

# Legacy local script (MLflow-tracked)
python pipelines\train_local_dqn.py

# Colab: open train_colab.ipynb, run all cells, download models/dqn_weights.pt
```

---

## MLflow Experiment Tracking

This project uses [MLflow](https://mlflow.org/) for comprehensive experiment tracking, model versioning, and monitoring.

### What Gets Tracked

| Pipeline | Logged Data |
|----------|------------|
| `training_pipeline.py` | Hyperparameters, per-episode rewards, epsilon decay, training duration, model weights, reward curves |
| `train_local_dqn.py` | Same as above for local quick training runs |
| `train_now.py` | Both Q-Learning and DQN runs tracked in separate experiments |
| `inference_pipeline.py` | Prediction counts, confidence stats, latency percentiles, drift reports |

### MLflow Experiments

| Experiment Name | Purpose |
|----------------|---------|
| `email-dqn-training` | All DQN training runs |
| `email-qlearning-training` | Q-Learning training runs |
| `email-inference-monitoring` | Batch inference metrics & drift |

### Launch the MLflow UI

```bash
# Start the tracking UI (default: http://127.0.0.1:5050)
python scripts/mlflow_server.py

# Custom port
python scripts/mlflow_server.py --port 8090
```

### Configuration

MLflow settings are centralised in `mlflow_config.py`:

```python
from mlflow_config import MLflowConfig

# Override tracking URI via environment variable:
# export MLFLOW_TRACKING_URI=http://your-mlflow-server:5000
```

### Architecture

```
mlflow_config.py                  ← Central configuration
    │
    ├── monitoring/mlflow_logger.py ← Reusable logging helpers
    │       │
    │       ├── log_training_params()
    │       ├── log_episode_metrics()
    │       ├── log_evaluation_results()
    │       ├── log_model_artifact()
    │       ├── log_reward_curve()
    │       ├── log_drift_report()
    │       └── log_inference_metrics()
    │
    ├── pipelines/training_pipeline.py  ← Uses helpers above
    ├── pipelines/train_local_dqn.py    ← Uses helpers above
    ├── pipelines/train_now.py          ← Uses helpers above
    └── pipelines/inference_pipeline.py ← Uses helpers above
```

---

## Running the Inference API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| POST | `/predict` | Run inference on one email |
| GET | `/model/version` | List checkpoints |
| POST | `/model/version/{file}` | Hot-swap checkpoint |
| GET | `/docs` | Swagger UI |

---

## Running Tests

```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

Test modules:
- `test_model.py` — DQN agent, Q-Network, ReplayBuffer
- `test_api.py` — FastAPI endpoint integration tests
- `test_data.py` — Email dataclass, reward calculator, environment
- `test_mlflow.py` — MLflow configuration, logger helpers, tracking

---

## Docker Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for the complete guide.

```bash
docker build -f docker/Dockerfile -t email-timing-response .
docker run -p 8000:8000 -v $(pwd)/models:/app/models email-timing-response
```

---

## Monitoring

| File | Contents |
|------|----------|
| `logs/app.log` | JSON structured logs (rotating 5 MB × 5) |
| `logs/metrics.json` | Prediction counts, confidence, latency percentiles |
| `logs/drift_report.json` | Per-feature PSI drift scores and alerts |
| `mlruns/` | MLflow experiment tracking data (params, metrics, artifacts) |

---

## Model Versioning

```
models/
├── dqn_weights.pt                  # default (latest training)
├── dqn_weights_20250510_0930.pt    # timestamped checkpoint
└── dqn.pkl                         # legacy pickle fallback
```

Hot-swap without restart:
```bash
curl -X POST http://localhost:8000/model/version/dqn_weights_20250510_0930.pt
```

---

## CI/CD Pipeline

```
Push to main/develop
        │
        ▼
  ┌─────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐
  │  Lint   │──►│   Tests      │──►│ Docker Build │──►│  Deploy  │
  │ black   │   │ (py3.10/3.11)│   │  Push GHCR   │   │ Staging  │
  │ flake8  │   │  + Coverage  │   │              │   │(main only│
  └─────────┘   └──────────────┘   └──────────────┘   └──────────┘
```

## Training Results

![DQN Reward Curve](assets/reward_curve_dqn.png)
![Q-Learning Reward Curve](assets/reward_curve.png)
