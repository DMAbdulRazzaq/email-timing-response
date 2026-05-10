import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from monitoring.model_registry import (
    DQN_MODEL_NAME,
    QL_MODEL_NAME,
    compare_runs,
    promote_model,
    register_dqn_model,
    register_ql_model,
)
from training.trainer import train_dqn, train_q_learning


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Email Timing Response training pipeline"
    )
    parser.add_argument("--agent", choices=["dqn", "q_learning"], default="dqn")
    parser.add_argument("--episodes", type=int, default=Config.EPISODES)
    parser.add_argument("--source", choices=["synthetic", "enron"], default="synthetic")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--register", action="store_true")
    parser.add_argument("--promote", action="store_true")
    return parser.parse_args()


def _register_model(agent_type: str, run_id: str):
    if agent_type == "dqn":
        return register_dqn_model(run_id)
    return register_ql_model(run_id)


def run(args: argparse.Namespace | None = None):
    args = args or parse_args()
    if args.agent == "dqn":
        result = train_dqn(args.episodes, args.run_name, args.source)
        model_name = DQN_MODEL_NAME
    else:
        result = train_q_learning(args.episodes, args.run_name, args.source)
        model_name = QL_MODEL_NAME

    registered_model = None
    if args.register:
        registered_model = _register_model(args.agent, result["run_id"])
        print(
            "Registered model "
            f"{registered_model.name} version {registered_model.version}"
        )

    if args.promote:
        if registered_model is None:
            registered_model = _register_model(args.agent, result["run_id"])
        promote_model(model_name, registered_model.version)
        print(f"Promoted {model_name} version {registered_model.version} to Production")

    print(compare_runs(top_n=5))
    return result


if __name__ == "__main__":
    run()
