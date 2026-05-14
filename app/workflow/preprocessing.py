import base64
import re
from email.utils import parsedate_to_datetime
from typing import Any

from app.workflow.schemas import EmailRecord


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_header(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _decode_data(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode(errors="replace")


def extract_body(payload: dict[str, Any]) -> str:
    if "parts" in payload:
        plain_parts = []
        html_parts = []

        for part in payload["parts"]:
            text = extract_body(part)
            if not text:
                continue
            if part.get("mimeType") == "text/html":
                html_parts.append(text)
            else:
                plain_parts.append(text)

        return "\n".join(plain_parts or html_parts)

    body = payload.get("body", {})
    data = body.get("data")
    if not data:
        return ""

    return _decode_data(data)


def parse_gmail_message(message: dict[str, Any]) -> EmailRecord:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    raw_body = extract_body(payload)
    timestamp = get_header(headers, "Date")

    if timestamp:
        try:
            timestamp = parsedate_to_datetime(timestamp).isoformat()
        except (TypeError, ValueError):
            pass

    return EmailRecord(
        id=message.get("id", ""),
        thread_id=message.get("threadId", ""),
        sender=get_header(headers, "From"),
        subject=get_header(headers, "Subject"),
        body=clean_text(raw_body),
        timestamp=timestamp,
        labels=message.get("labelIds", []),
    )

