from base64 import urlsafe_b64encode
from email.message import EmailMessage


SYSTEM_LABELS = {
    "reply_now": "AI/Reply Now",
    "delay_reply": "AI/Delay Reply",
    "mark_important": "AI/Important",
    "archive": "AI/Archived",
}


def ensure_label(service, label_name: str) -> str:
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for label in labels:
        if label.get("name") == label_name:
            return label["id"]

    body = {
        "name": label_name,
        "labelListVisibility": "labelShow",
        "messageListVisibility": "show",
    }
    return service.users().labels().create(userId="me", body=body).execute()["id"]


def apply_approved_action(service, message_id: str, action: str) -> None:
    label_id = ensure_label(service, SYSTEM_LABELS.get(action, "AI/Reviewed"))
    body = {"addLabelIds": [label_id], "removeLabelIds": []}

    if action == "archive":
        body["removeLabelIds"].append("INBOX")
    if action in {"reply_now", "mark_important"}:
        body["addLabelIds"].append("IMPORTANT")
    if action == "delay_reply":
        body["addLabelIds"].append("STARRED")

    service.users().messages().modify(userId="me", id=message_id, body=body).execute()


def create_reply_draft(service, to_address: str, subject: str, body_text: str, thread_id: str):
    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    message.set_content(body_text)

    encoded = urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {"message": {"raw": encoded, "threadId": thread_id}}
    return service.users().drafts().create(userId="me", body=draft_body).execute()


def create_ai_draft(
    service,
    to_address: str,
    subject: str,
    body_text: str,
    thread_id: str,
    labels: list[str] | None = None,
) -> dict:
    """
    Create a Gmail draft from AI-generated response.
    
    Args:
        service: Gmail API service
        to_address: Recipient email
        subject: Email subject
        body_text: Email body (AI-generated)
        thread_id: Thread ID to attach to
        labels: Optional labels to apply
        
    Returns:
        Created draft object
    """
    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    message.set_content(body_text)
    
    # Add X-AI-Generated header for tracking
    message["X-AI-Generated"] = "true"
    
    encoded = urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {
        "message": {
            "raw": encoded,
            "threadId": thread_id,
        }
    }
    
    draft = service.users().drafts().create(userId="me", body=draft_body).execute()
    
    # Apply labels if provided
    if labels:
        ensure_ai_labels(service)
        draft_message_id = draft.get("message", {}).get("id")
        if draft_message_id:
            label_ids = []
            for label_name in labels:
                label_id = ensure_label(service, label_name)
                label_ids.append(label_id)
            
            if label_ids:
                service.users().messages().modify(
                    userId="me",
                    id=draft_message_id,
                    body={"addLabelIds": label_ids}
                ).execute()
    
    return draft


def ensure_ai_labels(service) -> dict[str, str]:
    """Ensure AI response labels exist."""
    ai_labels = {
        "AI/Draft": "AI/Draft",
        "AI/Pending Approval": "AI/Pending Approval",
        "AI/Sent": "AI/Sent",
        "AI/Feedback": "AI/Feedback",
    }
    
    label_ids = {}
    for key, label_name in ai_labels.items():
        label_ids[key] = ensure_label(service, label_name)
    
    return label_ids


def send_draft(service, draft_id: str) -> dict:
    """
    Send a saved draft.
    
    Args:
        service: Gmail API service
        draft_id: Draft ID to send
        
    Returns:
        Sent message object
    """
    return service.users().drafts().send(userId="me", id=draft_id).execute()


def update_draft(
    service,
    draft_id: str,
    to_address: str,
    subject: str,
    body_text: str,
    thread_id: str,
) -> dict:
    """
    Update an existing draft with new content.
    
    Args:
        service: Gmail API service
        draft_id: Draft ID to update
        to_address: Recipient email
        subject: Email subject
        body_text: Updated email body
        thread_id: Thread ID
        
    Returns:
        Updated draft object
    """
    message = EmailMessage()
    message["To"] = to_address
    message["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    message.set_content(body_text)
    message["X-AI-Generated"] = "true"
    
    encoded = urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    draft_body = {
        "message": {
            "raw": encoded,
            "threadId": thread_id,
        }
    }
    
    return service.users().drafts().update(
        userId="me",
        id=draft_id,
        body=draft_body
    ).execute()


def get_draft(service, draft_id: str) -> dict:
    """Get draft details."""
    return service.users().drafts().get(userId="me", id=draft_id, format="full").execute()


def list_drafts(service) -> list[dict]:
    """List all drafts."""
    results = service.users().drafts().list(userId="me").execute()
    return results.get("drafts", [])


def delete_draft(service, draft_id: str) -> None:
    """Delete a draft."""
    service.users().drafts().delete(userId="me", id=draft_id).execute()


def mark_draft_approved(service, draft_id: str) -> None:
    """Mark draft as AI-approved."""
    draft = get_draft(service, draft_id)
    message_id = draft.get("message", {}).get("id")
    
    if message_id:
        label_id = ensure_label(service, "AI/Pending Approval")
        remove_label_id = ensure_label(service, "AI/Draft")
        
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={
                "addLabelIds": [label_id],
                "removeLabelIds": [remove_label_id],
            }
        ).execute()


def get_draft_preview(service, draft_id: str) -> dict:
    """
    Get readable preview of draft content.
    
    Returns:
        Dict with to, subject, snippet
    """
    draft = get_draft(service, draft_id)
    message = draft.get("message", {})
    headers = message.get("payload", {}).get("headers", [])
    
    header_dict = {h["name"]: h["value"] for h in headers}
    
    return {
        "draft_id": draft_id,
        "to": header_dict.get("To", ""),
        "subject": header_dict.get("Subject", ""),
        "snippet": message.get("snippet", "")[:100],
    }

