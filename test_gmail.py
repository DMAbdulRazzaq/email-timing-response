import base64
import json
import re
from pathlib import Path

from gmail_auth import gmail_authenticate

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "data" / "processed_emails.json"

IGNORE_SENDERS = [
    "canva",
    "newsletter",
    "marketing",
    "noreply",
]

HIRING_KEYWORDS = [
    "interview",
    "recruiter",
    "hiring",
    "job",
    "internship",
    "offer",
    "application",
]

DEADLINE_KEYWORDS = [
    "deadline",
    "due",
    "last date",
    "expires",
    "today",
    "tomorrow",
    "urgent",
]

ACTION_KEYWORDS = [
    "reply",
    "respond",
    "confirm",
    "schedule",
    "submit",
    "complete",
    "action required",
]

TRUSTED_SENDERS = [
    ".edu",
    "university",
    "professor",
    "recruiter",
    "hr@",
    "careers",
]

PROMOTION_KEYWORDS = [
    "sale",
    "discount",
    "unsubscribe",
    "promotion",
    "deal",
    "offer ends",
]


def get_body(payload):
    if "parts" in payload:
        for part in payload["parts"]:
            body_text = get_body(part)
            if body_text:
                return body_text
    else:
        mime_type = payload.get("mimeType")
        body = payload.get("body", {})
        data = body.get("data")

        if mime_type == "text/plain" and data:
            return base64.urlsafe_b64decode(data).decode()

    return ""


def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_header(headers, name):
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")

    return ""


def should_ignore_sender(sender):
    return any(word in sender.lower() for word in IGNORE_SENDERS)


def classify_email(sender, subject, body):
    sender_lower = sender.lower()
    text = f"{sender} {subject} {body}".lower()
    score = 40
    reasons = []

    if any(keyword in text for keyword in HIRING_KEYWORDS):
        score += 30
        reasons.append("Contains hiring or career keyword")

    if any(keyword in text for keyword in DEADLINE_KEYWORDS):
        score += 25
        reasons.append("Deadline or urgency detected")

    if any(keyword in text for keyword in ACTION_KEYWORDS):
        score += 20
        reasons.append("Action required")

    if any(keyword in sender_lower for keyword in TRUSTED_SENDERS):
        score += 15
        reasons.append("Sender appears trusted")

    if any(keyword in text for keyword in PROMOTION_KEYWORDS):
        score -= 35
        reasons.append("Promotional language detected")

    if should_ignore_sender(sender):
        score = min(score, 10)
        reasons.append("Sender matches ignored newsletter or marketing source")

    score = max(0, min(100, score))

    if score >= 85:
        category = "URGENT"
    elif score >= 65:
        category = "IMPORTANT"
    elif score >= 35:
        category = "NORMAL"
    elif score >= 15:
        category = "PROMOTION"
    else:
        category = "SPAM"

    if not reasons:
        reasons.append("No strong priority signals detected")

    return score, category, reasons


service = gmail_authenticate()

results = (
    service.users()
    .messages()
    .list(
        userId="me",
        maxResults=5,
    )
    .execute()
)

messages = results.get("messages", [])

print(f"\nTotal Messages Fetched: {len(messages)}\n")

processed_emails = []

for msg in messages:
    message = (
        service.users()
        .messages()
        .get(
            userId="me",
            id=msg["id"],
            format="full",
        )
        .execute()
    )

    payload = message["payload"]
    headers = payload.get("headers", [])

    subject = get_header(headers, "Subject")
    sender = get_header(headers, "From")
    timestamp = get_header(headers, "Date")

    if should_ignore_sender(sender):
        continue

    body = clean_text(get_body(payload))
    score, category, reasons = classify_email(sender, subject, body)

    email_data = {
        "id": msg["id"],
        "sender": sender,
        "subject": subject,
        "body": body,
        "timestamp": timestamp,
        "priority": score,
        "category": category,
        "reasons": reasons,
    }

    processed_emails.append(email_data)

    print("=" * 50)
    print("FROM:", sender)
    print("SUBJECT:", subject)
    print("CATEGORY:", category)
    print("PRIORITY SCORE:", score)
    print("REASON:")
    for reason in reasons:
        print("-", reason)
    print("BODY:\n", body[:500])

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(processed_emails, file, indent=2)

print(f"\nStored {len(processed_emails)} processed emails in {OUTPUT_FILE}")
