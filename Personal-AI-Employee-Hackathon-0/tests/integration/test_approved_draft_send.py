"""Integration test: approved draft in vault/Approved/ → Gmail MCP send_email → vault/Done/.

US1 AS-1: AI employee sends approved draft reply via Gmail MCP.
US1 AS-2: Draft is moved to vault/Done/ after successful send.
US1 AS-3: Draft remains in Approved/ if MCP unavailable (fallback retry).
"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def vault(tmp_path):
    """Create a complete vault structure for testing."""
    for d in ["Needs_Action", "Drafts", "Approved", "Done", "Logs"]:
        (tmp_path / d).mkdir()
    return tmp_path


def make_draft(
    vault: Path,
    to: str = "ceo@example.com",
    subject: str = "Re: Budget",
    status: str = "pending_approval",
) -> Path:
    """Create a test approved draft in vault/Approved/ with properly quoted YAML."""
    fm = {
        "status": status,
        "to": to,
        "subject": subject,
        "original_message_id": "msg-original-001",
    }
    # yaml.dump properly quotes values containing ': ' (e.g. email subjects)
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{frontmatter}---\n\nThank you for the budget proposal. Approved as discussed.\n"
    path = vault / "Approved" / "reply-001.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_approved_draft_sent_and_moved_to_done(vault):
    """US1 AS-1+2: approved draft → send_email called → moved to Done/."""
    draft_path = make_draft(vault)

    with patch("orchestrator.orchestrator.MCPClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.call_tool.return_value = {
            "message_id": "sent-msg-001",
            "thread_id": "thread-001",
            "sent_at": "2026-02-24T10:00:00Z",
        }
        MockClient.return_value = mock_client

        # Must provide provider since RalphWiggumOrchestrator requires it
        mock_provider = MagicMock()
        from orchestrator.orchestrator import RalphWiggumOrchestrator

        orch = RalphWiggumOrchestrator(provider=mock_provider, vault_path=str(vault))
        await orch._send_approved_draft(draft_path)

        # Assert: send_email called with correct args
        mock_client.call_tool.assert_called_once()
        call_args = mock_client.call_tool.call_args
        assert call_args[0][0] == "send_email", "Must call send_email tool"
        assert call_args[0][1]["to"] == "ceo@example.com"
        assert call_args[0][1]["subject"] == "Re: Budget"
        assert call_args[0][1]["reply_to_message_id"] == "msg-original-001"

        # Assert: draft moved to Done/
        assert not draft_path.exists(), "Draft must be moved from Approved/"
        assert (vault / "Done" / "reply-001.md").exists(), "Draft must appear in Done/"


@pytest.mark.asyncio
async def test_draft_stays_in_approved_when_mcp_unavailable(vault):
    """US1 AS-3: send_email fails (MCP unavailable) → draft NOT deleted, fallback called."""
    from orchestrator.mcp_client import MCPUnavailableError

    draft_path = make_draft(vault)

    with patch("orchestrator.orchestrator.MCPClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.call_tool.side_effect = MCPUnavailableError("MCP down")
        MockClient.return_value = mock_client

        mock_provider = MagicMock()
        from orchestrator.orchestrator import RalphWiggumOrchestrator

        orch = RalphWiggumOrchestrator(provider=mock_provider, vault_path=str(vault))

        # Should not raise — orchestrator handles MCPUnavailableError gracefully
        try:
            await orch._send_approved_draft(draft_path)
        except MCPUnavailableError:
            pass  # Acceptable; draft should still be in Approved/

        # Draft must NOT be moved to Done/ on MCP failure
        assert not (vault / "Done" / "reply-001.md").exists(), \
            "Draft must not appear in Done/ on MCP failure"


@pytest.mark.asyncio
async def test_scan_approved_drafts_finds_pending(vault):
    """_scan_approved_drafts returns pending_approval drafts only."""
    make_draft(vault, status="pending_approval")

    # Create a non-pending draft that should be ignored
    ignored = vault / "Approved" / "sent-already.md"
    ignored.write_text(
        "---\nstatus: done\nto: x@x.com\nsubject: X\n---\nBody\n",
        encoding="utf-8",
    )

    with patch("orchestrator.orchestrator.MCPClient") as MockClient:
        MockClient.return_value = AsyncMock()
        mock_provider = MagicMock()
        from orchestrator.orchestrator import RalphWiggumOrchestrator

        orch = RalphWiggumOrchestrator(provider=mock_provider, vault_path=str(vault))
        approved = await orch._scan_approved_drafts()

    assert len(approved) == 1, "Only pending_approval drafts should be returned"
    assert approved[0].name == "reply-001.md"


@pytest.mark.asyncio
async def test_send_approved_draft_skips_incomplete(vault):
    """_send_approved_draft skips drafts missing 'to' or 'subject' fields."""
    # Draft with missing 'to' field
    bad_draft = vault / "Approved" / "bad-draft.md"
    fm = {"status": "pending_approval", "subject": "Re: Something"}
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    bad_draft.write_text(f"---\n{frontmatter}---\nBody\n", encoding="utf-8")

    with patch("orchestrator.orchestrator.MCPClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value = mock_client
        mock_provider = MagicMock()
        from orchestrator.orchestrator import RalphWiggumOrchestrator

        orch = RalphWiggumOrchestrator(provider=mock_provider, vault_path=str(vault))
        await orch._send_approved_draft(bad_draft)

        # send_email must NOT be called for incomplete draft
        mock_client.call_tool.assert_not_called()


@pytest.mark.asyncio
async def test_send_approved_draft_handles_send_error_response(vault):
    """When Gmail MCP returns error in result, draft stays in Approved/."""
    draft_path = make_draft(vault)

    with patch("orchestrator.orchestrator.MCPClient") as MockClient:
        mock_client = AsyncMock()
        # MCP returns an error dict (not an exception)
        mock_client.call_tool.return_value = {
            "error": "auth_required",
            "message": "Token expired",
        }
        MockClient.return_value = mock_client
        mock_provider = MagicMock()
        from orchestrator.orchestrator import RalphWiggumOrchestrator

        orch = RalphWiggumOrchestrator(provider=mock_provider, vault_path=str(vault))
        await orch._send_approved_draft(draft_path)

        # Draft must NOT be moved to Done/ when error returned
        assert draft_path.exists(), "Draft must remain in Approved/ on error response"
        assert not (vault / "Done" / "reply-001.md").exists()
