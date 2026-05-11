"""
Launch the MLflow tracking UI.

Usage:
    python scripts/mlflow_server.py              # default port 5050
    python scripts/mlflow_server.py --port 8090   # custom port

The UI will be available at http://127.0.0.1:<port>
"""

import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mlflow_config import MLflowConfig


def main():
    parser = argparse.ArgumentParser(description="Launch MLflow UI")
    parser.add_argument(
        "--port", type=int, default=5050, help="Port for the MLflow UI (default: 5050)"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)"
    )
    args = parser.parse_args()

    # Resolve the backend store from tracking URI
    tracking_uri = MLflowConfig.TRACKING_URI
    backend_store = tracking_uri

    # If it's a file URI, extract the path for --backend-store-uri
    if tracking_uri.startswith("file:///"):
        backend_store = tracking_uri

    print("=" * 60)
    print("  MLflow Tracking UI")
    print(f"  Backend : {backend_store}")
    print(f"  URL     : http://{args.host}:{args.port}")
    print("=" * 60)

    cmd = [
        sys.executable,
        "-m",
        "mlflow",
        "ui",
        "--backend-store-uri",
        backend_store,
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    subprocess.run(cmd)


if __name__ == "__main__":
    main()
