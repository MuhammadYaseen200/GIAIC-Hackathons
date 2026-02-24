"""Full contract tests for all 6 Gmail MCP tools.

Contracts verified:
  - Success response shape (required fields, no error field)
  - Error response shape (error: MCPErrorCode, message: str)
  - Specific error codes per tool error taxonomy
  - auth_required when token missing
  - rate_limited (429) has details.retry_after
  - not_found (404) for missing message_id
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from googleapiclient.errors import HttpError
from unittest.mock import Mock


def make_http_error(status: int, reason: str = "Error") -> HttpError:
    """Create a mock HttpError for a given HTTP status code."""
    resp = Mock()
    resp.status = status
    resp.reason = reason
    return HttpError(resp=resp, content=reason.encode())


# ── health_check ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_success_schema(tmp_path):
    """health_check success: status, authenticated_as, token_expires_at."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.getProfile.return_value.execute.return_value = {
            "emailAddress": "user@gmail.com"
        }
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).health_check()
        assert result["status"] == "ok"
        assert "authenticated_as" in result
        assert "token_expires_at" in result
        assert "error" not in result


@pytest.mark.asyncio
async def test_health_check_auth_error(tmp_path):
    """health_check returns auth_required when token missing."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        from mcp_servers.gmail.auth import AuthRequiredError
        mock_svc.side_effect = AuthRequiredError("No token")
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).health_check()
        assert result["error"] == "auth_required"
        assert "message" in result


# ── send_email ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_send_email_success_schema(tmp_path):
    """send_email success: message_id, thread_id, sent_at."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg-001", "threadId": "thread-001"
        }
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).send_email("x@x.com", "S", "B")
        assert "message_id" in result and "thread_id" in result and "sent_at" in result
        assert "error" not in result


@pytest.mark.asyncio
async def test_send_email_rate_limited(tmp_path):
    """send_email rate_limited (429) has error=rate_limited + details.retry_after."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
            make_http_error(429, "Rate Limit Exceeded")
        )
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).send_email("x@x.com", "S", "B")
        assert result["error"] == "rate_limited"
        assert "details" in result
        assert "retry_after" in result["details"]


@pytest.mark.asyncio
async def test_send_email_api_error(tmp_path):
    """send_email Gmail API error returns send_failed."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.send.return_value.execute.side_effect = (
            make_http_error(500, "Internal Server Error")
        )
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).send_email("x@x.com", "S", "B")
        assert result["error"] == "send_failed"
        assert "message" in result


# ── list_emails ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_emails_success_schema(tmp_path):
    """list_emails success: emails (list), total_count (int)."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            "messages": [{"id": "m1"}, {"id": "m2"}]
        }
        # Mock get() for metadata fetch
        svc.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "snippet": "Hello...",
            "payload": {"headers": [
                {"name": "Subject", "value": "Test"},
                {"name": "From", "value": "sender@x.com"},
                {"name": "Date", "value": "Mon, 1 Jan 2026 10:00:00 +0000"},
            ]},
        }
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).list_emails(query="is:unread", max_results=10)
        assert "emails" in result
        assert "total_count" in result
        assert isinstance(result["emails"], list)
        assert "error" not in result


@pytest.mark.asyncio
async def test_list_emails_empty(tmp_path):
    """list_emails returns emails=[] and total_count=0 when no messages."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.list.return_value.execute.return_value = {}
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).list_emails()
        assert result["emails"] == []
        assert result["total_count"] == 0


@pytest.mark.asyncio
async def test_list_emails_auth_error(tmp_path):
    """list_emails returns auth_required when token missing."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        from mcp_servers.gmail.auth import AuthRequiredError
        mock_svc.side_effect = AuthRequiredError("No token")
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).list_emails()
        assert result["error"] == "auth_required"


# ── get_email ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_email_success_schema(tmp_path):
    """get_email success: id, subject, sender, to, date, body, has_attachments."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        import base64
        body_data = base64.urlsafe_b64encode(b"Hello World").decode()
        svc = MagicMock()
        svc.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "m1",
            "snippet": "Hello",
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Test Subject"},
                    {"name": "From", "value": "from@x.com"},
                    {"name": "To", "value": "to@x.com"},
                    {"name": "Date", "value": "2026-01-01"},
                ],
                "parts": [{"mimeType": "text/plain", "body": {"data": body_data}, "filename": ""}],
            },
        }
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).get_email("m1")
        required = {"id", "subject", "sender", "to", "date", "body", "has_attachments"}
        assert required.issubset(result.keys()), f"Missing fields: {required - result.keys()}"
        assert result["body"] == "Hello World"
        assert result["has_attachments"] is False


@pytest.mark.asyncio
async def test_get_email_not_found(tmp_path):
    """get_email returns not_found for 404 HTTP error."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.messages.return_value.get.return_value.execute.side_effect = (
            make_http_error(404, "Not Found")
        )
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).get_email("missing-id")
        assert result["error"] == "not_found"
        assert "message" in result


# ── move_email ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_move_email_success_schema(tmp_path):
    """move_email success: moved=True, message_id, label."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": [{"id": "DONE", "name": "DONE"}]
        }
        svc.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).move_email("m1", "DONE")
        assert result["moved"] is True
        assert result["message_id"] == "m1"
        assert result["label"] == "DONE"
        assert "error" not in result


@pytest.mark.asyncio
async def test_move_email_not_found(tmp_path):
    """move_email returns not_found for 404 HTTP error."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": []
        }
        svc.users.return_value.messages.return_value.modify.return_value.execute.side_effect = (
            make_http_error(404, "Not Found")
        )
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).move_email("missing-id", "DONE")
        assert result["error"] == "not_found"


# ── add_label ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_label_success_schema(tmp_path):
    """add_label success: labeled=True, message_id, label."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": [{"id": "Label_1", "name": "AI_PROCESSED"}]
        }
        svc.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).add_label("m1", "AI_PROCESSED")
        assert result["labeled"] is True
        assert result["message_id"] == "m1"
        assert result["label"] == "AI_PROCESSED"


@pytest.mark.asyncio
async def test_add_label_creates_missing_label(tmp_path):
    """add_label creates the label if it doesn't exist yet."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_svc:
        svc = MagicMock()
        svc.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            "labels": []  # no existing labels
        }
        svc.users.return_value.labels.return_value.create.return_value.execute.return_value = {
            "id": "Label_new", "name": "NEW_LABEL"
        }
        svc.users.return_value.messages.return_value.modify.return_value.execute.return_value = {}
        mock_svc.return_value = svc
        from mcp_servers.gmail.tools import GmailTools
        result = await GmailTools(tmp_path).add_label("m1", "NEW_LABEL")
        assert result["labeled"] is True
        # Verify labels.create was called
        svc.users.return_value.labels.return_value.create.assert_called_once()
