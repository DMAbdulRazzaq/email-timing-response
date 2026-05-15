from app.workflow.schemas import (ActionRecommendation, EmailRecord,
                                  IntelligenceResult, ThreadContext)


def build_recommendation(
    email: EmailRecord,
    intelligence: IntelligenceResult,
    thread: ThreadContext | None = None,
) -> ActionRecommendation:
    reasons = list(email.reasons)
    reasons.append(f"Gemini/context action: {intelligence.recommended_action}")
    if intelligence.urgency_reasoning:
        reasons.append(intelligence.urgency_reasoning)
    if thread and thread.message_count > 1:
        reasons.append(f"Thread-aware analysis used {thread.message_count} messages")

    action = intelligence.recommended_action
    if email.category in {"PROMOTION", "SPAM"} and email.priority < 20:
        action = "archive"
    if email.priority >= 85:
        action = "reply_now"

    return ActionRecommendation(
        message_id=email.id,
        thread_id=email.thread_id,
        action=action,
        priority=email.priority,
        category=email.category,
        confidence=intelligence.confidence,
        reasons=reasons,
        requires_approval=action in {"reply_now", "archive", "mark_important"},
        draft_text=intelligence.suggested_reply,
    )
