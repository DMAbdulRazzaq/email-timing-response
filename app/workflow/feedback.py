from pathlib import Path

from app.workflow.schemas import FeedbackEvent
from app.workflow.storage import JsonlStore


ACTION_REWARD = {
    ("reply_now", "reply_now"): 10.0,
    ("mark_important", "mark_important"): 7.0,
    ("delay_reply", "delay_reply"): 5.0,
    ("archive", "archive"): 6.0,
    ("archive", "reply_now"): -10.0,
    ("reply_now", "archive"): -8.0,
}


class FeedbackStore:
    def __init__(self, path: Path | str = "data/feedback_events.jsonl"):
        self.store = JsonlStore(path)

    def record(
        self,
        message_id: str,
        thread_id: str,
        recommended_action: str,
        user_action: str,
        notes: str = "",
    ) -> FeedbackEvent:
        reward = reward_from_correction(recommended_action, user_action)
        event = FeedbackEvent(
            message_id=message_id,
            thread_id=thread_id,
            recommended_action=recommended_action,
            user_action=user_action,
            reward=reward,
            notes=notes,
        )
        self.store.append(event.to_dict())
        return event

    def events(self) -> list[dict]:
        return self.store.read_all()


def reward_from_correction(recommended_action: str, user_action: str) -> float:
    if (recommended_action, user_action) in ACTION_REWARD:
        return ACTION_REWARD[(recommended_action, user_action)]
    if recommended_action == user_action:
        return 4.0
    return -4.0

