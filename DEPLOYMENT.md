# Deployment Guide — Email Timing Response

This document covers all supported deployment paths: local development,
Docker (single container), and a production-ready cloud setup.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10 or 3.11 | |
| Docker | 24+ | For containerised deployment |
| Git | any | |
| Trained model | `models/dqn_weights.pt` | Run training pipeline first |

---

## 1. Local Development (No Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Train (skip if using pre-trained weights)
python pipelines/training_pipeline.py --episodes 10000

# Start API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"ok","model_loaded":true,"model_version":"...","uptime_seconds":2.1}
```

---

## 2. Docker — Single Container

### Build

```bash
docker build -f docker/Dockerfile -t email-timing-response:latest .
```

The Dockerfile uses a two-stage build:
- **Stage 1 (builder):** Installs all Python deps.
- **Stage 2 (runtime):** Copies only what's needed; runs as a non-root user.

### Run

```bash
docker run -d \
  --name email-api \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  -e LOG_LEVEL=INFO \
  email-timing-response:latest
```

| Flag | Purpose |
|------|---------|
| `-v models:/app/models` | Persist trained weights across container restarts |
| `-v logs:/app/logs` | Access structured logs on the host |
| `-e LOG_LEVEL=INFO` | Override log verbosity (DEBUG / INFO / WARNING) |

### Stop / remove

```bash
docker stop email-api && docker rm email-api
```

### Health check

The image includes a built-in Docker HEALTHCHECK. Inspect with:

```bash
docker inspect --format='{{.State.Health.Status}}' email-api
```

---

## 3. Docker Compose (API + optional monitoring)

Create `docker-compose.yml` in the project root:

```yaml
version: "3.9"

services:
  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    environment:
      - LOG_LEVEL=INFO
      - METRICS_PATH=/app/logs/metrics.json
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c",
             "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Run:
```bash
docker compose up -d
docker compose logs -f api
```

---

## 4. Cloud Deployment — General Steps

### 4a. Build and push to GitHub Container Registry (GHCR)

```bash
# Login
echo $GITHUB_TOKEN | docker login ghcr.io -u <username> --password-stdin

# Tag and push
docker tag email-timing-response:latest ghcr.io/<org>/<repo>:latest
docker push ghcr.io/<org>/<repo>:latest
```

### 4b. Deploy on a Linux VM (e.g. AWS EC2, GCP Compute Engine)

```bash
# On the server
docker pull ghcr.io/<org>/<repo>:latest
docker run -d \
  -p 80:8000 \
  -v /data/models:/app/models \
  -v /data/logs:/app/logs \
  ghcr.io/<org>/<repo>:latest
```

### 4c. Deploy on Render / Railway (PaaS, no Dockerfile required)

1. Connect your GitHub repo.
2. Set **Root Directory** to `.` and **Dockerfile Path** to `docker/Dockerfile`.
3. Set the port to `8000`.
4. Add environment variable `LOG_LEVEL=INFO`.
5. Mount a persistent disk at `/app/models` for weights.

### 4d. Deploy on Fly.io

```bash
# Install flyctl, then:
fly launch --dockerfile docker/Dockerfile --internal-port 8000
fly volumes create models_vol --size 1
fly deploy
```

---

## 5. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Python logging level |
| `LOG_DIR` | `logs` | Directory for rotating log files |
| `METRICS_PATH` | `logs/metrics.json` | Path for metrics JSON dump |
| `PORT` | `8000` | Port uvicorn listens on |

---

## 6. Model Updates (Zero-Downtime)

The API supports hot-swapping without a restart:

```bash
# 1. Copy new weights to the models/ volume
scp models/dqn_weights_v2.pt server:/data/models/

# 2. Swap via API
curl -X POST http://your-host/model/version/dqn_weights_v2.pt
```

Response:
```json
{"status":"ok","loaded":"dqn_weights_v2.pt","version":"20250511_1445"}
```

---

## 7. Running Tests in CI / Locally

```bash
# Unit tests
pytest tests/test_model.py tests/test_data.py -v

# API tests (mocked agent, no GPU required)
pytest tests/test_api.py -v

# Full suite with coverage
pytest tests/ -v --cov=. --cov-report=html
open htmlcov/index.html
```

---

## 8. Observability Checklist

After deployment, verify:

- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] `POST /predict` returns a valid `action_label`
- [ ] `logs/app.log` is being written (check `docker logs email-api`)
- [ ] `logs/metrics.json` is updated after predictions
- [ ] Drift detection is running (call `pipelines/inference_pipeline.py --demo`)

---

## 9. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `/health` returns `model_loaded: false` | `dqn_weights.pt` missing from `models/` volume | Re-train or mount correct volume |
| `503 Model not loaded` | Same as above | Same fix |
| `ImportError: No module named 'agent'` | Container not running from `/app` | Check `WORKDIR` in Dockerfile |
| Container exits immediately | Requirements not installed | Check `docker build` logs |
| High latency (> 500ms) | CPU-only inference with large batch | Expected; GPU not required for single prediction |
