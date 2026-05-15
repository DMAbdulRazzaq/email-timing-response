from app.workflow.preprocessing import parse_gmail_message
from app.workflow.schemas import ThreadContext

FOLLOW_UP_TERMS = ["follow up", "following up", "reminder", "checking in", "any update"]


def fetch_thread_context(service, thread_id: str) -> ThreadContext:
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    messages = [parse_gmail_message(item) for item in thread.get("messages", [])]

    text = " ".join(f"{msg.subject} {msg.body}".lower() for msg in messages)
    follow_up_count = sum(text.count(term) for term in FOLLOW_UP_TERMS)
    latest = messages[-1] if messages else None

    return ThreadContext(
        thread_id=thread_id,
        message_count=len(messages),
        follow_up_count=follow_up_count,
        latest_sender=latest.sender if latest else "",
        previous_subjects=[msg.subject for msg in messages[:-1]],
        summary=_compact_summary(messages),
    )


def _compact_summary(messages) -> str:
    if not messages:
        return ""
    snippets = [f"{msg.sender}: {msg.subject}" for msg in messages[-4:]]
    return " | ".join(snippets)
