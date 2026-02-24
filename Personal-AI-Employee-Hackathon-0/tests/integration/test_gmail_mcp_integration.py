"""Integration tests for all 5 Gmail MCP tools with mocked OAuth service.

Tests each tool returns the correct schema and behaviour
without making live API calls (patch get_gmail_service).
"""
import base64
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
from googleapiclient.errors import HttpError


def make_http_error(status: int, reason: str = "Error") -> HttpError:
    resp = Mock()
    resp.status = status
    resp.reason = reason
    return HttpError(resp=resp, content=reason.encode())


@pytest.fixture
def vault(tmp_path):
    for d in ["Needs_Action", "Drafts", "Approved", "Done", "Logs"]:
        (tmp_path / d).mkdir()
    return tmp_path


@pytest.fixture
def mock_service():
    """A pre-configured MagicMock Gmail service."""
    svc = MagicMock()
    return svc


# ── send_email integration ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_email_full_flow(vault, mock_service):
    """send_email: audit log written + success result returned."""
    mock_service.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        "id": "sent-001", "threadId": "thread-001"
    }
    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        tools = GmailTools(vault_path=vault)
        result = await tools.send_email("ceo@example.com", "Re: Budget", "Approved.")

        assert result["message_id"] == "sent-001"
        assert result["thread_id"] == "thread-001"
        assert "sent_at" in result

        # Audit log verified
        logs = list((vault / "Logs").glob("gmail_mcp_*.jsonl"))
        assert logs, "Audit log must be written"
        entry = json.loads(logs[0].read_text().strip())
        assert entry["to"] == "ceo@example.com"
        assert entry["subject"] == "Re: Budget"


# ── list_emails integration ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_emails_returns_email_list(vault, mock_service):
    """list_emails: returns emails list with correct fields."""
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
        "messages": [{"id": "m1"}, {"id": "m2"}]
    }
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "m1",
        "snippet": "Hello snippet",
        "payload": {"headers": [
            {"name": "Subject", "value": "Test Subject"},
            {"name": "From", "value": "boss@example.com"},
            {"name": "Date", "value": "Mon, 24 Feb 2026 10:00:00 +0000"},
        ]},
    }
    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).list_emails(query="is:unread", max_results=5)

    assert "emails" in result
    assert "total_count" in result
    assert result["total_count"] == 2
    email = result["emails"][0]
    assert "id" in email
    assert "subject" in email
    assert "sender" in email
    assert "date" in email
    assert "snippet" in email


@pytest.mark.asyncio
async def test_list_emails_defaults(vault, mock_service):
    """list_emails works with no query arg (defaults to is:unread)."""
    mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {}
    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).list_emails()
    assert result["emails"] == []
    assert result["total_count"] == 0


# ── get_email integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_email_returns_full_email(vault, mock_service):
    """get_email: returns full email with decoded body."""
    body_bytes = base64.urlsafe_b64encode(b"Hello, this is the email body.")
    mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
        "id": "m001",
        "snippet": "Hello...",
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Important Meeting"},
                {"name": "From", "value": "sender@corp.com"},
                {"name": "To", "value": "me@gmail.com"},
                {"name": "Date", "value": "2026-02-24"},
            ],
            "parts": [
                {"mimeType": "text/plain", "body": {"data": body_bytes.decode()}, "filename": ""},
            ],
        },
    }
    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).get_email("m001")

    assert result["id"] == "m001"
    assert result["subject"] == "Important Meeting"
    assert result["sender"] == "sender@corp.com"
    assert result["body"] == "Hello, this is the email body."
    assert result["has_attachments"] is False


# ── move_email integration ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_email_returns_moved_true(vault, mock_service):
    """move_email: returns moved=True with message_id and label."""
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [{"id": "Label_AI", "name": "AI_PROCESSED"}]
    }
    mock_service.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}

    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).move_email("m001", "AI_PROCESSED")

    assert result["moved"] is True
    assert result["message_id"] == "m001"
    assert result["label"] == "AI_PROCESSED"


# ── add_label integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_label_returns_labeled_true(vault, mock_service):
    """add_label: returns labeled=True with message_id and label."""
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": [{"id": "Label_1", "name": "PRIORITY"}]
    }
    mock_service.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}

    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).add_label("m001", "PRIORITY")

    assert result["labeled"] is True
    assert result["message_id"] == "m001"
    assert result["label"] == "PRIORITY"


@pytest.mark.asyncio
async def test_add_label_creates_new_label(vault, mock_service):
    """add_label creates label via API when it doesn't exist."""
    mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
        "labels": []
    }
    mock_service.users.return_value.labels.return_value.create.return_value.execute.return_value = {
        "id": "Label_new", "name": "BRAND_NEW"
    }
    mock_service.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}

    with patch("mcp_servers.gmail.tools.get_gmail_service", return_value=mock_service):
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(vault).add_label("m001", "BRAND_NEW")

    assert result["labeled"] is True
    mock_service.users.return_value.labels.return_value.create.assert_called_once()
