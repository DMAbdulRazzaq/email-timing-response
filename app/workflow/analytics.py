from collections import Counter, defaultdict
from statistics import mean


def build_dashboard_metrics(emails: list[dict], feedback_events: list[dict]) -> dict:
    priority_values = [item.get("priority", 0) for item in emails]
    categories = Counter(item.get("category", "UNKNOWN") for item in emails)
    actions = Counter(item.get("action", "unknown") for item in emails)
    rewards = [event.get("reward", 0.0) for event in feedback_events]

    sender_scores = defaultdict(list)
    for item in emails:
        sender_scores[item.get("sender", "unknown")].append(item.get("priority", 0))

    sender_importance = {
        sender: round(mean(scores), 2)
        for sender, scores in sorted(
            sender_scores.items(),
            key=lambda pair: mean(pair[1]),
            reverse=True,
        )
    }

    return {
        "total_emails": len(emails),
        "avg_priority": round(mean(priority_values), 2) if priority_values else 0,
        "priority_distribution": dict(categories),
        "action_distribution": dict(actions),
        "sender_importance_ranking": sender_importance,
        "avg_reward": round(mean(rewards), 2) if rewards else 0,
        "feedback_events": len(feedback_events),
        "reward_trend": rewards[-50:],
    }
