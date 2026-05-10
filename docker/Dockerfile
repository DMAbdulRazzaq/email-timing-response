# ── Stage 1: build dependencies ──────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System build deps (for torch compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt && \
    pip install --prefix=/install --no-cache-dir fastapi uvicorn[standard] pydantic


# ── Stage 2: runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy project source (exclude large training artefacts via .dockerignore)
COPY agent/           agent/
COPY app/             app/
COPY data/            data/
COPY environment/     environment/
COPY monitoring/      monitoring/
COPY pipelines/       pipelines/
COPY simulation/      simulation/
COPY training/        training/
COPY utils/           utils/
COPY config.py        .
COPY main.py          .

# Models directory — mount a volume in production to persist trained weights
RUN mkdir -p models logs
VOLUME ["/app/models", "/app/logs"]

# Non-root ownership
RUN chown -R appuser:appgroup /app
USER appuser

# Environment defaults (override at runtime)
ENV LOG_LEVEL=INFO \
    LOG_DIR=/app/logs \
    METRICS_PATH=/app/logs/metrics.json \
    PORT=8000

EXPOSE 8000

# Liveness check — matches /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Start FastAPI via uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
