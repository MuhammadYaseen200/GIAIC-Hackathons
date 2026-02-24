"""E2E integration test: full _run_poll_cycle() with mocked LLM + mocked MCPClient.

Tests that the orchestrator correctly:
1. Polls vault/Needs_Action/ for pending emails
2. Calls LLM for decision
3. Routes vault operation through MCPClient (Obsidian MCP)
4. Logs the decision
"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.fixture
def vault(tmp_path):
    for d in ["Needs_Action", "Done", "Drafts", "Approved", "Logs"]:
        (tmp_path / d).mkdir()
    return tmp_path


def create_pending_email(vault: Path, message_id: str = "msg-e2e-001") -> Path:
    """Create a pending email note in vault/Needs_Action/."""
    fm = {
        "message_id": message_id,
        "status": "pending",
        "from": "ceo@corp.com",
        "subject": "Budget Review",
        "received_at": "2026-02-24T09:00:00Z",
        "priority": "normal",
    }
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{frontmatter}---\n\nPlease review the Q4 budget proposal.\n"
    path = vault / "Needs_Action" / f"{message_id}.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.asyncio
async def test_full_cycle_archive_routes_through_mcp(vault):
    """Full poll cycle: archive decision → move_note MCP call made."""
    email_path = create_pending_email(vault)

    with patch("orchestrator.orchestrator.MCPClient") as MockMCP:
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {"moved": True}
        MockMCP.return_value = mock_mcp

        # Mock LLM provider
        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "mock"
        mock_provider.model_name.return_value = "mock-model"
        mock_provider.complete = AsyncMock(return_value=(
            '{"decision":"archive","confidence":0.95,"reasoning":"No action needed"}',
            100, 50,
        ))

        from orchestrator.orchestrator import RalphWiggumOrchestrator
        orch = RalphWiggumOrchestrator(
            provider=mock_provider,
            vault_path=str(vault),
        )
        orch._obsidian_mcp = mock_mcp

        await orch._run_poll_cycle()

        # Verify MCPClient call_tool was called (move_note for archive)
        assert mock_mcp.call_tool.called, "MCPClient.call_tool must be called during archive"
        tool_names = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
        assert "move_note" in tool_names, f"move_note must be called, got: {tool_names}"


@pytest.mark.asyncio
async def test_full_cycle_draft_reply_writes_via_mcp(vault):
    """Full poll cycle: draft_reply decision → write_note MCP call for draft."""
    email_path = create_pending_email(vault, "msg-draft-001")

    with patch("orchestrator.orchestrator.MCPClient") as MockMCP:
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {"path": "Drafts/draft.md", "frontmatter": {}, "body": ""}
        MockMCP.return_value = mock_mcp

        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "mock"
        mock_provider.model_name.return_value = "mock-model"
        mock_provider.complete = AsyncMock(return_value=(
            '{"decision":"draft_reply","confidence":0.85,"reasoning":"Reply needed",'
            '"reply_body":"Thank you for the budget review."}',
            100, 60,
        ))

        from orchestrator.orchestrator import RalphWiggumOrchestrator
        orch = RalphWiggumOrchestrator(
            provider=mock_provider,
            vault_path=str(vault),
        )
        orch._obsidian_mcp = mock_mcp

        await orch._run_poll_cycle()

        assert mock_mcp.call_tool.called
        tool_names = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
        assert "write_note" in tool_names, f"write_note must be called for draft_reply, got: {tool_names}"


@pytest.mark.asyncio
async def test_approved_drafts_sent_in_same_cycle(vault):
    """Full poll cycle includes approved draft processing."""
    import yaml

    # Create approved draft
    fm = {"status": "pending_approval", "to": "boss@corp.com", "subject": "Re: Budget"}
    frontmatter = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    draft_path = vault / "Approved" / "reply-001.md"
    draft_path.write_text(
        f"---\n{frontmatter}---\n\nApproved for budget increase.\n",
        encoding="utf-8",
    )

    with patch("orchestrator.orchestrator.MCPClient") as MockMCP:
        mock_mcp = AsyncMock()
        mock_mcp.call_tool.return_value = {
            "message_id": "sent-001",
            "thread_id": "thread-001",
            "sent_at": "2026-02-24T10:00:00Z",
        }
        MockMCP.return_value = mock_mcp

        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "mock"
        mock_provider.model_name.return_value = "mock-model"

        from orchestrator.orchestrator import RalphWiggumOrchestrator
        orch = RalphWiggumOrchestrator(
            provider=mock_provider,
            vault_path=str(vault),
        )
        orch._gmail_mcp = mock_mcp

        await orch._run_poll_cycle()

        # Verify send_email was called for the approved draft
        tool_names = [c[0][0] for c in mock_mcp.call_tool.call_args_list]
        assert "send_email" in tool_names, f"send_email must be called for approved draft, got: {tool_names}"

        # Draft must be moved to Done/
        assert not draft_path.exists(), "Draft must be moved from Approved/ after send"
        assert (vault / "Done" / "reply-001.md").exists(), "Draft must appear in Done/"
