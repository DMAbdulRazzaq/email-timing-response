"""
Personalization Memory — Learns from user feedback to adapt response generation.

Tracks:
- Approved drafts
- Edited drafts
- Rejected drafts
- Tone preferences
- Length preferences
- Reply style patterns
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.workflow.storage import JsonlStore


@dataclass
class DraftAction:
    """Record of user interaction with a generated draft."""

    response_id: str
    sender: str
    action: str  # approved|edited|rejected
    original_tone: str
    generated_text: str
    user_action_text: str = ""  # edited text if edited
    edit_distance: int = 0  # character diff if edited
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    feedback_notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PersonalizationMemory:
    """Learns from user response interactions."""

    def __init__(self, storage_path: Path | str = "data/draft_interactions.jsonl"):
        """
        Initialize personalization memory.

        Args:
            storage_path: Path to JSONL file storing draft interactions
        """
        self.store = JsonlStore(storage_path)
        self.session_cache = {
            "preferred_tone": "professional",
            "preferred_length": "medium",
            "reply_style": "formal",
            "sender_preferences": {},
        }
        self._load_aggregate_stats()

    def record_action(
        self,
        response_id: str,
        sender: str,
        action: str,
        tone: str,
        generated_text: str,
        user_text: str = "",
        feedback: str = "",
    ) -> DraftAction:
        """
        Record user interaction with AI-generated draft.

        Args:
            response_id: ID of generated response
            sender: Email sender
            action: approved|edited|rejected
            tone: Original tone used
            generated_text: Original generated text
            user_text: Modified text if edited
            feedback: Optional user feedback notes

        Returns:
            Recorded DraftAction
        """
        if action not in ["approved", "edited", "rejected"]:
            raise ValueError(f"Invalid action: {action}")

        edit_distance = 0
        if action == "edited" and user_text:
            edit_distance = self._calculate_edit_distance(generated_text, user_text)

        draft_action = DraftAction(
            response_id=response_id,
            sender=sender,
            action=action,
            original_tone=tone,
            generated_text=generated_text,
            user_action_text=user_text,
            edit_distance=edit_distance,
            feedback_notes=feedback,
        )

        self.store.append(draft_action.to_dict())
        self._update_sender_preferences(sender, action, tone)
        self._update_tone_preferences(tone, action)

        return draft_action

    def get_sender_preferences(self, sender: str) -> dict[str, Any]:
        """Get learned preferences for specific sender."""
        # Count interactions by tone and action
        actions = self.store.read_all()
        sender_actions = [a for a in actions if a.get("sender") == sender]

        if not sender_actions:
            return {
                "total_interactions": 0,
                "approval_rate": 0.0,
                "preferred_tone": None,
                "typical_length": None,
                "edit_frequency": 0.0,
            }

        total = len(sender_actions)
        approved = sum(1 for a in sender_actions if a.get("action") == "approved")
        edited = sum(1 for a in sender_actions if a.get("action") == "edited")

        tone_counts = {}
        for a in sender_actions:
            tone = a.get("original_tone", "unknown")
            tone_counts[tone] = tone_counts.get(tone, 0) + 1

        preferred_tone = max(tone_counts, key=tone_counts.get) if tone_counts else None

        return {
            "total_interactions": total,
            "approval_rate": approved / total if total > 0 else 0.0,
            "preferred_tone": preferred_tone,
            "typical_length": self._infer_length_preference(sender_actions),
            "edit_frequency": edited / total if total > 0 else 0.0,
            "tone_distribution": tone_counts,
        }

    def get_tone_effectiveness(self) -> dict[str, float]:
        """Get effectiveness metrics for each tone."""
        actions = self.store.read_all()

        tone_stats = {}
        for action in actions:
            tone = action.get("original_tone", "unknown")
            action_type = action.get("action")

            if tone not in tone_stats:
                tone_stats[tone] = {"approved": 0, "edited": 0, "rejected": 0, "total": 0}

            if action_type == "approved":
                tone_stats[tone]["approved"] += 1
            elif action_type == "edited":
                tone_stats[tone]["edited"] += 1
            elif action_type == "rejected":
                tone_stats[tone]["rejected"] += 1

            tone_stats[tone]["total"] += 1

        # Calculate effectiveness score (approved + 0.5*edited) / total
        effectiveness = {}
        for tone, stats in tone_stats.items():
            if stats["total"] > 0:
                effectiveness[tone] = (stats["approved"] + 0.5 * stats["edited"]) / stats["total"]
            else:
                effectiveness[tone] = 0.0

        return effectiveness

    def recommend_tone_for_sender(self, sender: str) -> str:
        """
        Recommend best tone for specific sender based on history.

        Args:
            sender: Email sender

        Returns:
            Recommended tone
        """
        prefs = self.get_sender_preferences(sender)
        if prefs.get("preferred_tone"):
            return prefs["preferred_tone"]

        # Fall back to globally most effective tone
        effectiveness = self.get_tone_effectiveness()
        if effectiveness:
            return max(effectiveness, key=effectiveness.get)

        return "professional"

    def get_personalization_hints(self) -> dict[str, Any]:
        """
        Get overall personalization hints to pass to response generator.

        Returns:
            Dict with preferred_length, reply_style, signature patterns
        """
        actions = self.store.read_all()

        if not actions:
            return {
                "preferred_length": "medium",
                "reply_style": "formal",
                "signature": "Best regards",
            }

        # Analyze approved+edited actions to infer style
        approved_edits = [a for a in actions if a.get("action") in ["approved", "edited"]]

        if not approved_edits:
            return {
                "preferred_length": "medium",
                "reply_style": "formal",
                "signature": "Best regards",
            }

        lengths = [
            self._infer_length(a.get("user_action_text", a.get("generated_text", "")))
            for a in approved_edits
        ]
        avg_length = sum(lengths) / len(lengths) if lengths else 150

        # Infer length preference
        if avg_length < 100:
            preferred_length = "concise"
        elif avg_length < 250:
            preferred_length = "medium"
        else:
            preferred_length = "verbose"

        return {
            "preferred_length": preferred_length,
            "reply_style": "formal",  # Could enhance this with more analysis
            "signature": "Best regards",
            "average_reply_length": avg_length,
        }

    def _update_sender_preferences(self, sender: str, action: str, tone: str) -> None:
        """Update cached sender preferences."""
        if sender not in self.session_cache["sender_preferences"]:
            self.session_cache["sender_preferences"][sender] = {
                "tones_used": {},
                "approval_count": 0,
                "rejection_count": 0,
            }

        sender_prefs = self.session_cache["sender_preferences"][sender]
        sender_prefs["tones_used"][tone] = sender_prefs["tones_used"].get(tone, 0) + 1

        if action == "approved":
            sender_prefs["approval_count"] += 1
        elif action == "rejected":
            sender_prefs["rejection_count"] += 1

    def _update_tone_preferences(self, tone: str, action: str) -> None:
        """Update cached tone preferences."""
        # This could trigger adaptive learning
        pass

    def _calculate_edit_distance(self, original: str, edited: str) -> int:
        """Simple character difference as edit distance proxy."""
        return abs(len(original) - len(edited)) + sum(1 for a, b in zip(original, edited) if a != b)

    def _infer_length(self, text: str) -> int:
        """Infer response length in characters."""
        return len(text.strip())

    def _infer_length_preference(self, actions: list[dict]) -> str:
        """Infer user's preferred response length from history."""
        approved_lengths = []
        for action in actions:
            if action.get("action") == "approved":
                text = action.get("user_action_text") or action.get("generated_text", "")
                approved_lengths.append(len(text))

        if not approved_lengths:
            return None

        avg_length = sum(approved_lengths) / len(approved_lengths)

        if avg_length < 100:
            return "concise"
        elif avg_length < 250:
            return "medium"
        else:
            return "verbose"

    def export_profile(self) -> dict[str, Any]:
        """Export complete user profile for model training."""
        return {
            "session_cache": self.session_cache,
            "tone_effectiveness": self.get_tone_effectiveness(),
            "all_interactions": self.store.read_all(),
            "personalization_hints": self.get_personalization_hints(),
        }

    def _load_aggregate_stats(self) -> None:
        """Load aggregate stats from storage into the session cache.

        Called at init to seed `session_cache` with historical preferences.
        """
        try:
            actions = self.store.read_all()
        except Exception:
            actions = []

        # Initialize sender preferences and global defaults
        self.session_cache["sender_preferences"] = {}
        if not actions:
            # nothing to load
            return

        # Populate sender preferences from history
        for a in actions:
            sender = a.get("sender")
            if not sender:
                continue
            if sender not in self.session_cache["sender_preferences"]:
                self.session_cache["sender_preferences"][sender] = {
                    "tones_used": {},
                    "approval_count": 0,
                    "rejection_count": 0,
                }
            sp = self.session_cache["sender_preferences"][sender]
            tone = a.get("original_tone", "professional")
            sp["tones_used"][tone] = sp["tones_used"].get(tone, 0) + 1
            if a.get("action") == "approved":
                sp["approval_count"] += 1
            elif a.get("action") == "rejected":
                sp["rejection_count"] += 1

        # Seed preferred_tone and preferred_length from overall data
        effectiveness = self.get_tone_effectiveness()
        if effectiveness:
            preferred = max(effectiveness, key=effectiveness.get)
            self.session_cache["preferred_tone"] = preferred

        hints = self.get_personalization_hints()
        if hints and hints.get("preferred_length"):
            self.session_cache["preferred_length"] = hints.get("preferred_length")
