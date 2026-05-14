import pytest
from unittest.mock import MagicMock


def make_mock_service_for_draft(create_response=None, labels_list=None):
    svc = MagicMock()
    users = svc.users.return_value

    # labels().list().execute() -> existing labels
    labels = users.labels.return_value
    labels.list.return_value.execute.return_value = {"labels": labels_list or []}

    # drafts().create(...).execute() -> create_response
    drafts = users.drafts.return_value
    create_mock = MagicMock()
    create_mock.execute.return_value = create_response or {"id": "draft123", "message": {"id": "msg123"}}
    drafts.create.return_value = create_mock
    # drafts.update(...).execute() -> updated
    update_mock = MagicMock()
    update_mock.execute.return_value = {"id": "draft123", "message": {"id": "msg123"}}
    drafts.update.return_value = update_mock
    # drafts.send(...).execute()
    send_mock = MagicMock()
    send_mock.execute.return_value = {"id": "sent123", "labelIds": []}
    drafts.send.return_value = send_mock

    # messages().modify().execute() stub
    messages = users.messages.return_value
    mod = MagicMock()
    mod.execute.return_value = {}
    messages.modify.return_value.execute.return_value = {}

    # drafts().get(...).execute() for preview
    get_mock = MagicMock()
    get_mock.execute.return_value = {"id": "draft123", "message": {"id": "msg123", "snippet": "hello", "payload": {"headers": [{"name": "To", "value": "alice@example.com"}]}}}
    drafts.get.return_value = get_mock

    return svc


def test_create_ai_draft_calls_gmail_api(monkeypatch):
    svc = make_mock_service_for_draft()

    # Import function under test
    from app.workflow.gmail_actions import create_ai_draft

    draft = create_ai_draft(svc, to_address="alice@example.com", subject="Hello", body_text="Hi", thread_id="thread1", labels=["AI/Draft"])

    assert draft is not None
    assert draft.get("id") == "draft123"
    # Basic response checks
    assert isinstance(draft, dict)


def test_update_and_send_draft(monkeypatch):
    svc = make_mock_service_for_draft()
    from app.workflow.gmail_actions import update_draft, send_draft

    updated = update_draft(svc, draft_id="draft123", to_address="bob@example.com", subject="Re: Hi", body_text="Updated body", thread_id="thread1")
    # update returns dict from execute
    assert isinstance(updated, dict)

    sent = send_draft(svc, draft_id="draft123")
    assert isinstance(sent, dict)
