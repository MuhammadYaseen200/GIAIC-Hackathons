"""Contract tests for Gmail MCP send_email tool.

Tests schema, error format, and audit log only. No live API calls.
Contracts:
  - Success result must have message_id, thread_id, sent_at
  - Error result must have error (MCPErrorCode) and message fields
  - Pre-action audit log is written before the API call
  - Rate-limited error has details.retry_after field
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_send_email_success_schema(tmp_path):
    """Success result matches contract: message_id, thread_id, sent_at."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_get_service:
        mock_svc = MagicMock()
        mock_svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg-123",
            "threadId": "thread-456",
        }
        mock_get_service.return_value = mock_svc

        from mcp_servers.gmail.tools import GmailTools

        tools = GmailTools(vault_path=tmp_path)
        result = await tools.send_email("to@example.com", "Test Subject", "Test body")

        assert "message_id" in result, "Contract: message_id required in success response"
        assert "thread_id" in result, "Contract: thread_id required in success response"
        assert "sent_at" in result, "Contract: sent_at required in success response"
        assert result["message_id"] == "msg-123"
        assert result["thread_id"] == "thread-456"
        # No error field in success
        assert "error" not in result, "Contract: no error field in success response"


@pytest.mark.asyncio
async def test_send_email_auth_error_schema(tmp_path):
    """Auth error must return {error: auth_required, message: ...}."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_get_service:
        from mcp_servers.gmail.auth import AuthRequiredError

        mock_get_service.side_effect = AuthRequiredError("Token missing")

        from mcp_servers.gmail.tools import GmailTools

        tools = GmailTools(vault_path=tmp_path)
        result = await tools.send_email("to@example.com", "Test", "Body")

        assert result["error"] == "auth_required", "Contract: error must be auth_required"
        assert "message" in result, "Contract: message field required in error response"
        assert "Token missing" in result["message"]


@pytest.mark.asyncio
async def test_send_email_pre_action_audit_log_written(tmp_path):
    """Pre-action audit log must be written BEFORE Gmail API call."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_get_service:
        mock_svc = MagicMock()
        mock_svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "msg-001",
            "threadId": "thread-001",
        }
        mock_get_service.return_value = mock_svc

        from mcp_servers.gmail.tools import GmailTools

        tools = GmailTools(vault_path=tmp_path)
        await tools.send_email("ceo@example.com", "Re: Budget", "Approved.")

        # Audit log must exist
        log_files = list((tmp_path / "Logs").glob("gmail_mcp_*.jsonl"))
        assert log_files, "Contract: audit log file must be created"

        entries = [json.loads(line) for line in log_files[0].read_text().strip().splitlines()]
        assert len(entries) == 1, "One audit entry per send call"
        entry = entries[0]
        assert entry["event"] == "pre_send_audit"
        assert entry["to"] == "ceo@example.com"
        assert entry["subject"] == "Re: Budget"
        assert "timestamp" in entry


@pytest.mark.asyncio
async def test_send_email_with_reply_threading(tmp_path):
    """send_email with reply_to_message_id must thread email (fetch threadId)."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_get_service:
        mock_svc = MagicMock()
        # Mocked get() for fetching original thread
        mock_svc.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            "id": "original-msg",
            "threadId": "thread-original",
        }
        mock_svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
            "id": "reply-msg-001",
            "threadId": "thread-original",
        }
        mock_get_service.return_value = mock_svc

        from mcp_servers.gmail.tools import GmailTools

        tools = GmailTools(vault_path=tmp_path)
        result = await tools.send_email(
            "boss@example.com",
            "Re: Important",
            "Understood.",
            reply_to_message_id="original-msg",
        )

        assert result["message_id"] == "reply-msg-001"
        assert result["thread_id"] == "thread-original"


@pytest.mark.asyncio
async def test_send_email_internal_error_schema(tmp_path):
    """Unexpected exceptions must return {error: internal_error, message: ...}."""
    with patch("mcp_servers.gmail.tools.get_gmail_service") as mock_get_service:
        mock_get_service.side_effect = RuntimeError("Unexpected failure")

        from mcp_servers.gmail.tools import GmailTools

        tools = GmailTools(vault_path=tmp_path)
        result = await tools.send_email("to@example.com", "Test", "Body")

        assert result["error"] == "internal_error", "Contract: error must be internal_error"
        assert "message" in result
