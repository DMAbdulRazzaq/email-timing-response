from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

ACTION_LABELS = ["reply_now", "delay_reply", "mark_important", "archive"]


@dataclass
class EmailRecord:
    id: str
    thread_id: str
    sender: str
    subject: str
    body: str
    timestamp: str = ""
    labels: list[str] = field(default_factory=list)
    priority: int = 40
    category: str = "NORMAL"
    reasons: list[str] = field(default_factory=list)
    features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ThreadContext:
    thread_id: str
    message_count: int
    follow_up_count: int
    latest_sender: str
    previous_subjects: list[str]
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntelligenceResult:
    summary: str
    tone: str
    urgency_reasoning: str
    suggested_reply: str
    recommended_action: str
    confidence: float
    risks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionRecommendation:
    message_id: str
    thread_id: str
    action: str
    priority: int
    category: str
    confidence: float
    reasons: list[str]
    requires_approval: bool = True
    draft_text: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackEvent:
    message_id: str
    thread_id: str
    recommended_action: str
    user_action: str
    reward: float
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
