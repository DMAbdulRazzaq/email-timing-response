import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.workflow.gemini_engine import GeminiContextEngine
from app.workflow.preprocessing import parse_gmail_message
from app.workflow.priority_engine import score_email, should_ignore_sender
from app.workflow.recommender import build_recommendation
from app.workflow.storage import JsonlStore
from app.workflow.thread_context import fetch_thread_context
from gmail_auth import gmail_authenticate

RECOMMENDATIONS_FILE = ROOT / "data" / "recommendations.jsonl"


def fetch_inbox_messages(service, max_results: int = 10) -> list[dict]:
    results = (
        service.users()
        .messages()
        .list(userId="me", q="in:inbox newer_than:14d", maxResults=max_results)
        .execute()
    )
    return results.get("messages", [])


def fetch_message(service, message_id: str) -> dict:
    return service.users().messages().get(userId="me", id=message_id, format="full").execute()


def run(max_results: int = 10) -> None:
    service = gmail_authenticate()
    gemini = GeminiContextEngine()
    recommendation_store = JsonlStore(RECOMMENDATIONS_FILE)

    messages = fetch_inbox_messages(service, max_results=max_results)
    print(f"Fetched {len(messages)} inbox messages")

    for item in messages:
        raw_message = fetch_message(service, item["id"])
        email = parse_gmail_message(raw_message)

        if should_ignore_sender(email.sender):
            print(f"SKIP: {email.sender} | {email.subject}")
            continue

        thread = fetch_thread_context(service, email.thread_id) if email.thread_id else None
        email = score_email(email, follow_up_count=thread.follow_up_count if thread else 0)
        intelligence = gemini.analyze(email, thread)
        recommendation = build_recommendation(email, intelligence, thread)

        record = {
            "email": email.to_dict(),
            "thread": thread.to_dict() if thread else None,
            "intelligence": intelligence.to_dict(),
            "recommendation": recommendation.to_dict(),
            "approval_status": "pending",
        }
        recommendation_store.append(record)

        print("=" * 72)
        print("FROM:", email.sender)
        print("SUBJECT:", email.subject)
        print("CATEGORY:", email.category)
        print("PRIORITY:", email.priority)
        print("ACTION:", recommendation.action)
        print("CONFIDENCE:", round(recommendation.confidence, 2))
        print("APPROVAL:", "required" if recommendation.requires_approval else "optional")
        print("REASONS:")
        for reason in recommendation.reasons:
            print("-", reason)

    print(f"\nSaved recommendations to {RECOMMENDATIONS_FILE}")


if __name__ == "__main__":
    run()
