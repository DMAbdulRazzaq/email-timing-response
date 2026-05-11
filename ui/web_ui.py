"""
web_ui.py  —  Flask inference server for the RL Email Triage Agent.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import torch
from flask import Flask, jsonify, render_template, request

from config import Config
from data.email_data import Email
from environment.reward import RewardCalculator
from main import get_trained_agent
from simulation.sources.nlp_extractor import NLPEmailExtractor
from simulation.sources.sender_memory import SenderMemory

app = Flask(__name__)
extractor = NLPEmailExtractor()
sender_memory = SenderMemory()

# Arrival-time store.
# Keyed by hash(subject|sender).
# Set on /infer (first keystroke), popped on /decide_nlp (decision time).
# Tracks real "time in inbox before action".
_arrival_times: dict = {}

# Learning validation: session reward tracking.
ROLLING_WINDOW = 50  # last N decisions for rolling average
_session_stats = {
    "decisions": 0,
    "total_reward": 0.0,
    "history": [],  # rolling window of recent rewards (capped at ROLLING_WINDOW)
    "action_counts": {0: 0, 1: 0, 2: 0, 3: 0},  # distribution of actions taken
}

AGENT_MODE = os.environ.get("AGENT_MODE", "dqn")
_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = get_trained_agent(mode=AGENT_MODE)
        # Start epsilon at 0.3 so the online learning buffer gets diverse samples.
        # Decays every 10 decisions via decay_epsilon() called in _decide().
        _agent.epsilon = 0.3
        print(
            "[INIT] Online learning enabled. epsilon = 0.3 "
            "(will decay over interactions)"
        )
    return _agent


# Routes.


@app.route("/agent_status")
def agent_status():
    agent = get_agent()
    return jsonify(
        {
            "mode": AGENT_MODE,
            "epsilon": round(agent.epsilon, 4),
        }
    )


@app.route("/debug")
def debug():
    """
    Full debug snapshot — epsilon, sender memory, device info, session stats.
    """
    agent = get_agent()
    hist = _session_stats["history"]
    rolling_avg = (sum(hist) / len(hist)) if hist else 0.0
    return jsonify(
        {
            "epsilon": round(agent.epsilon, 4),
            "sender_memory": sender_memory.snapshot(),
            "model_device": str(agent._device),
            "agent_mode": AGENT_MODE,
            "session": {
                "decisions": _session_stats["decisions"],
                "total_reward": round(_session_stats["total_reward"], 2),
                "rolling_avg_reward": round(rolling_avg, 3),
                "rolling_window": len(hist),
                "action_distribution": {
                    "reply_now": _session_stats["action_counts"][0],
                    "delay_reply": _session_stats["action_counts"][1],
                    "mark_important": _session_stats["action_counts"][2],
                    "archive": _session_stats["action_counts"][3],
                },
            },
        }
    )


def _decide(email: Email):
    """
    Greedy inference pass — UI always sees the model's current best action.
    After deciding, the agent learns from the reward signal (online adaptation).
    Epsilon decays every 10 decisions; exploration only affects the learning
    buffer, NOT the action shown in the UI (which is always greedy).
    """
    state = email.to_state_vector()
    agent = get_agent()
    saved_eps = agent.epsilon
    agent.epsilon = 0.0  # greedy for UI — user always sees best action
    action = agent.select_action(state)
    agent.epsilon = saved_eps

    reward = RewardCalculator().calculate(email, action)
    label = ["reply_now", "delay_reply", "mark_important", "archive"][action]

    # Structured debug log + Q-value explosion guard.
    with torch.no_grad():
        t = torch.tensor(state, dtype=torch.float32).unsqueeze(0).to(agent._device)
        q_vals = [round(x, 3) for x in agent._policy_net(t)[0].tolist()]

    q_max = max(q_vals)
    q_warn = (
        "  *** Q-VALUE EXPLOSION — check training stability ***" if q_max > 500 else ""
    )

    print(
        f"\n[DECIDE] subject={email.subject!r:.45}  sender={email.sender!r:.30}\n"
        f"         state    = {[round(x, 3) for x in state.tolist()]}\n"
        f"         q_values = {q_vals}   (0=reply 1=delay 2=mark 3=archive){q_warn}\n"
        f"         action   = {action} ({label})   reward = {reward}   "
        f"epsilon = {round(saved_eps, 4)}   wait = {email.waiting_time}min"
    )

    # Online learning: adapt to new reward signal without full retrain.
    # next_state = state (same-state approximation).
    # We don't have the next email yet.
    # Once replay buffer hits batch_size (64), each call does a gradient step.
    agent.learn(state, action, reward, state, False)

    # Session stats + epsilon decay.
    _session_stats["decisions"] += 1
    _session_stats["total_reward"] += reward
    _session_stats["action_counts"][action] += 1
    hist = _session_stats["history"]
    hist.append(reward)
    if len(hist) > ROLLING_WINDOW:
        hist.pop(0)

    rolling_avg = sum(hist) / len(hist)

    # Decay epsilon every 10 decisions so exploration gradually reduces
    if _session_stats["decisions"] % 10 == 0:
        agent.decay_epsilon()
        print(f"         [DECAY]  epsilon now = {agent.epsilon:.4f}")

    print(
        f"         session  = {_session_stats['decisions']} decisions  "
        f"rolling_avg = {rolling_avg:.2f}  "
        f"total = {_session_stats['total_reward']:.1f}"
    )

    return label, reward, state


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/infer", methods=["POST"])
def infer():
    """
    Live-preview inference (called on every keystroke via debounce).
    Also records the email's 'arrival time' for Phase 2 waiting_time calculation.
    """
    data = request.get_json()
    subject = data.get("subject", "").strip()
    sender = data.get("sender", "").strip()

    # Record arrival time the first time this subject+sender is typed.
    # Using hash(subject|sender) as key — simple and collision-resistant.
    key = hash(f"{subject}|{sender}")
    if key not in _arrival_times:
        _arrival_times[key] = datetime.now()

    reasoning = extractor.explain(subject, sender)
    return jsonify(reasoning)


@app.route("/decide_nlp", methods=["POST"])
def decide_nlp():
    """Auto-mode decision: NLP extracts features, agent decides."""
    data = request.get_json()
    subject, sender = data["subject"].strip(), data["sender"].strip()

    # Compute real waiting time (arrival → now).
    key = hash(f"{subject}|{sender}")
    arrival = _arrival_times.pop(key, None)  # pop → clear for next submission
    waiting_mins = (
        int((datetime.now() - arrival).total_seconds() / 60) if arrival else 0
    )

    # Adapt sender importance via session memory.
    rule_si = extractor._classify_sender(sender)
    adapted_si = sender_memory.get_importance(sender, rule_si)

    # Build email with corrected features.
    email = extractor.extract(
        subject, sender, waiting_time=waiting_mins, sender_importance=adapted_si
    )
    reasoning = extractor.explain(subject, sender)

    # Agent decides.
    label, reward, state = _decide(email)
    action_int = ["reply_now", "delay_reply", "mark_important", "archive"].index(label)

    # Update sender memory.
    sender_memory.update(sender, action_int, reward)

    return jsonify(
        {
            "action": label,
            "reward": reward,
            "state_vector": [round(x, 2) for x in state.tolist()],
            "raw_p": email.priority,
            "raw_si": email.sender_importance,
            "raw_w": email.waiting_time,
            "raw_wl": email.workload,
            "raw_t": email.time_of_day,
            "subject": subject,
            "sender": sender,
            "reasoning": reasoning,
            # Live observability
            "epsilon": round(get_agent().epsilon, 4),
            "agent_mode": AGENT_MODE,
            "sender_memory": sender_memory.snapshot(),
        }
    )


@app.route("/decide", methods=["POST"])
def decide():
    """Manual-mode decision: caller provides raw feature values via sliders."""
    data = request.get_json()
    email = Email(
        subject=data["subject"],
        sender=data["sender"],
        priority=int(data["priority"]),
        sender_importance=int(data["sender_importance"]),
        waiting_time=int(data["waiting_time"]),
        workload=int(data["workload"]),
        time_of_day=int(data["time_of_day"]),
    )
    label, reward, state = _decide(email)
    return jsonify(
        {
            "action": label,
            "reward": reward,
            "state_vector": [round(x, 2) for x in state.tolist()],
            "raw_p": email.priority,
            "raw_si": email.sender_importance,
            "raw_w": email.waiting_time,
            "raw_wl": email.workload,
            "raw_t": email.time_of_day,
            "subject": data["subject"],
            "sender": data["sender"],
            # Live observability
            "epsilon": round(get_agent().epsilon, 4),
            "agent_mode": AGENT_MODE,
        }
    )


if __name__ == "__main__":
    print("Loading agent...")
    get_agent()
    print(f"Starting server on http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
