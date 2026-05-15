"""
Response Feedback — Tracks AI response interactions and generates RL rewards.

Provides feedback signals for RL training:
- Draft approved → positive reward
- Draft edited → neutral/learning reward
- Draft rejected → negative reward
- User satisfaction signals
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.workflow.storage import JsonlStore


@dataclass
class ResponseFeedback:
    """User feedback on an AI-generated response."""

    response_id: str
    sender: str
    original_action: str
    generated_tone: str
    user_feedback_type: str  # approved|edited|rejected
    reward_signal: float
    safety_passed: bool = True
    approval_time_seconds: float = 0.0  # Time to approve/reject
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    feedback_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ResponseFeedbackTracker:
    """Tracks user feedback on AI-generated responses for learning."""

    # Reward mapping for different feedback types
    FEEDBACK_REWARDS = {
        "approved": 10.0,  # User liked it
        "approved_quick": 12.0,  # User approved quickly - was very clear
        "edited": 2.0,  # User had to edit - partially correct
        "rejected": -5.0,  # User rejected - was wrong
    }

    def __init__(self, storage_path: Path | str = "data/response_feedback.jsonl"):
        """
        Initialize response feedback tracker.

        Args:
            storage_path: Path to JSONL file storing feedback
        """
        self.store = JsonlStore(storage_path)
        self.session_stats = {
            "total_feedbacks": 0,
            "approvals": 0,
            "edits": 0,
            "rejections": 0,
            "total_reward": 0.0,
        }

    def record_feedback(
        self,
        response_id: str,
        sender: str,
        original_action: str,
        generated_tone: str,
        feedback_type: str,  # approved|edited|rejected
        safety_passed: bool = True,
        approval_time_seconds: float = 0.0,
        feedback_notes: str = "",
    ) -> ResponseFeedback:
        """
        Record user feedback on generated response.

        Args:
            response_id: ID of generated response
            sender: Email sender
            original_action: Original RL action (reply_now, etc.)
            generated_tone: Tone used for generation
            feedback_type: User feedback type
            safety_passed: Whether safety checks passed
            approval_time_seconds: Time user took to approve/reject
            feedback_notes: Optional feedback notes from user

        Returns:
            ResponseFeedback with reward signal
        """
        reward = self._calculate_reward(feedback_type, approval_time_seconds, safety_passed)

        feedback = ResponseFeedback(
            response_id=response_id,
            sender=sender,
            original_action=original_action,
            generated_tone=generated_tone,
            user_feedback_type=feedback_type,
            reward_signal=reward,
            safety_passed=safety_passed,
            approval_time_seconds=approval_time_seconds,
            feedback_notes=feedback_notes,
        )

        self.store.append(feedback.to_dict())
        self._update_session_stats(feedback_type, reward)

        return feedback

    def _calculate_reward(
        self,
        feedback_type: str,
        approval_time_seconds: float = 0.0,
        safety_passed: bool = True,
    ) -> float:
        """
        Calculate RL reward from feedback.

        Args:
            feedback_type: User feedback (approved|edited|rejected)
            approval_time_seconds: Time user took to approve
            safety_passed: Whether safety checks passed

        Returns:
            Reward signal for RL training
        """
        base_reward = self.FEEDBACK_REWARDS.get(feedback_type, 0.0)

        # Bonus if user approved very quickly (confident generation)
        if feedback_type == "approved" and 0 < approval_time_seconds < 5:
            return self.FEEDBACK_REWARDS.get("approved_quick", 12.0)

        # Penalty if safety didn't pass but user still approved
        if feedback_type == "approved" and not safety_passed:
            base_reward *= 0.7  # Reduce reward confidence

        # Extra penalty for rejections after safety warnings
        if feedback_type == "rejected" and not safety_passed:
            base_reward *= 1.5  # Stronger negative signal

        return base_reward

    def _update_session_stats(self, feedback_type: str, reward: float) -> None:
        """Update session statistics."""
        self.session_stats["total_feedbacks"] += 1
        self.session_stats["total_reward"] += reward

        if feedback_type == "approved":
            self.session_stats["approvals"] += 1
        elif feedback_type == "edited":
            self.session_stats["edits"] += 1
        elif feedback_type == "rejected":
            self.session_stats["rejections"] += 1

    def get_tone_performance(self) -> dict[str, Any]:
        """
        Get performance metrics for each tone.

        Returns:
            Metrics: approval_rate, avg_reward, edit_rate, rejection_rate
        """
        feedbacks = self.store.read_all()
        tone_metrics = {}

        for feedback in feedbacks:
            tone = feedback.get("generated_tone", "unknown")

            if tone not in tone_metrics:
                tone_metrics[tone] = {
                    "total": 0,
                    "approvals": 0,
                    "edits": 0,
                    "rejections": 0,
                    "total_reward": 0.0,
                }

            feedback_type = feedback.get("user_feedback_type")
            reward = feedback.get("reward_signal", 0.0)

            tone_metrics[tone]["total"] += 1
            tone_metrics[tone]["total_reward"] += reward

            if feedback_type == "approved":
                tone_metrics[tone]["approvals"] += 1
            elif feedback_type == "edited":
                tone_metrics[tone]["edits"] += 1
            elif feedback_type == "rejected":
                tone_metrics[tone]["rejections"] += 1

        # Compute derived metrics
        performance = {}
        for tone, metrics in tone_metrics.items():
            total = metrics["total"]
            if total > 0:
                performance[tone] = {
                    "approval_rate": metrics["approvals"] / total,
                    "edit_rate": metrics["edits"] / total,
                    "rejection_rate": metrics["rejections"] / total,
                    "avg_reward": metrics["total_reward"] / total,
                    "total_interactions": total,
                }
            else:
                performance[tone] = {
                    "approval_rate": 0.0,
                    "edit_rate": 0.0,
                    "rejection_rate": 0.0,
                    "avg_reward": 0.0,
                    "total_interactions": 0,
                }

        return performance

    def get_sender_performance(self, sender: str) -> dict[str, Any]:
        """Get performance metrics for specific sender."""
        feedbacks = self.store.read_all()
        sender_feedbacks = [f for f in feedbacks if f.get("sender") == sender]

        if not sender_feedbacks:
            return {
                "total_interactions": 0,
                "approval_rate": 0.0,
                "avg_reward": 0.0,
            }

        total = len(sender_feedbacks)
        approvals = sum(1 for f in sender_feedbacks if f.get("user_feedback_type") == "approved")
        total_reward = sum(f.get("reward_signal", 0.0) for f in sender_feedbacks)

        return {
            "total_interactions": total,
            "approval_rate": approvals / total if total > 0 else 0.0,
            "avg_reward": total_reward / total if total > 0 else 0.0,
        }

    def export_rl_training_data(self) -> dict[str, Any]:
        """
        Export feedback data formatted for RL training.

        Returns:
            Training data with states, actions, rewards
        """
        feedbacks = self.store.read_all()

        training_examples = []
        for feedback in feedbacks:
            training_examples.append(
                {
                    "response_id": feedback.get("response_id"),
                    "sender": feedback.get("sender"),
                    "action": feedback.get("original_action"),
                    "tone": feedback.get("generated_tone"),
                    "reward": feedback.get("reward_signal"),
                    "feedback_type": feedback.get("user_feedback_type"),
                    "timestamp": feedback.get("generated_at"),
                }
            )

        return {
            "total_examples": len(training_examples),
            "examples": training_examples,
            "tone_performance": self.get_tone_performance(),
            "session_stats": self.session_stats,
        }

    def get_session_stats(self) -> dict[str, Any]:
        """Get current session statistics."""
        total = self.session_stats["total_feedbacks"]

        if total == 0:
            return {
                "total_feedbacks": 0,
                "approvals": 0,
                "edits": 0,
                "rejections": 0,
                "total_reward": 0.0,
                "avg_reward_per_feedback": 0.0,
                "approval_rate": 0.0,
            }

        return {
            "total_feedbacks": total,
            "approvals": self.session_stats["approvals"],
            "edits": self.session_stats["edits"],
            "rejections": self.session_stats["rejections"],
            "total_reward": self.session_stats["total_reward"],
            "avg_reward_per_feedback": self.session_stats["total_reward"] / total,
            "approval_rate": self.session_stats["approvals"] / total,
        }
