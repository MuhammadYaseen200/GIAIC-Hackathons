"""Integration tests for HITL workflow (T017).

Full approve/reject/ambiguous cycles with tmp_path vault
and mocked MCPClient.call_tool.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml

from orchestrator.hitl_manager import HITLManager


@pytest.fixture
def vault(tmp_path):
    (tmp_path / "Pending_Approval").mkdir()
    (tmp_path / "Approved").mkdir()
    (tmp_path / "Rejected").mkdir()
    (tmp_path / "Logs").mkdir()
    return tmp_path


@pytest.fixture
def whatsapp_client():
    client = AsyncMock()
    client.call_tool = AsyncMock(return_value={})
    return client


@pytest.fixture
def gmail_client():
    client = AsyncMock()
    client.call_tool = AsyncMock(return_value={"message_id": "sent-999", "sent_at": "2026-03-04T12:00:00Z"})
    return client


@pytest.fixture
def manager(vault, whatsapp_client, gmail_client):
    return HITLManager(
        whatsapp_client=whatsapp_client,
        gmail_client=gmail_client,
        vault_path=vault,
        owner_number="+923001234567",
        batch_delay_seconds=0,
        reminder_hours=24,
        timeout_hours=48,
        max_concurrent_drafts=5,
    )


def _read_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 2:
            return yaml.safe_load(parts[1]) or {}
    return {}


# ── Full approve cycle ──

@pytest.mark.asyncio
async def test_full_approve_cycle(manager, vault, whatsapp_client, gmail_client):
    # Step 1: submit draft
    draft_id = await manager.submit_draft(
        recipient="boss@company.com",
        subject="Re: Important",
        body="Here is the reply draft.",
        priority="HIGH",
        risk_level="low",
    )

    # Verify file in Pending_Approval
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    assert draft_path.exists()

    # Step 2: send batch notification
    await manager.send_batch_notification()
    whatsapp_client.call_tool.assert_called_once()
    call_args = whatsapp_client.call_tool.call_args
    assert call_args[0][0] == "send_message"

    # Verify notified_at updated
    meta = _read_frontmatter(draft_path)
    assert meta["notified_at"] is not None

    # Step 3: owner approves
    whatsapp_client.call_tool.reset_mock()
    await manager.handle_owner_reply(f"approve {draft_id}", "+923001234567")

    # Gmail MCP send_email called
    gmail_client.call_tool.assert_called_once()
    send_args = gmail_client.call_tool.call_args
    assert send_args[0][0] == "send_email"
    assert send_args[0][1]["to"] == "boss@company.com"
    assert send_args[0][1]["subject"] == "Re: Important"
    assert "reply draft" in send_args[0][1]["body"]

    # File moved to Approved
    assert not draft_path.exists()
    assert (vault / "Approved" / f"{draft_id}.md").exists()

    # HITL decision logged
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    assert log_path.exists()
    entries = [json.loads(line) for line in log_path.read_text().strip().split("\n")]
    assert any(e["draft_id"] == draft_id and e["decision"] == "approved" for e in entries)


# ── Full reject cycle ──

@pytest.mark.asyncio
async def test_full_reject_cycle(manager, vault, gmail_client):
    draft_id = await manager.submit_draft(
        recipient="client@co.com",
        subject="Re: Contract",
        body="Draft contract reply.",
        priority="MED",
        risk_level="low",
    )

    await manager.handle_owner_reply(f"reject {draft_id}", "+923001234567")

    # Gmail NOT called
    gmail_client.call_tool.assert_not_called()

    # File moved to Rejected
    assert not (vault / "Pending_Approval" / f"{draft_id}.md").exists()
    assert (vault / "Rejected" / f"{draft_id}.md").exists()

    # Decision logged
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    entries = [json.loads(line) for line in log_path.read_text().strip().split("\n")]
    assert any(e["draft_id"] == draft_id and e["decision"] == "rejected" for e in entries)


# ── Ambiguous reply ──

@pytest.mark.asyncio
async def test_ambiguous_reply_keeps_pending(manager, vault, gmail_client, whatsapp_client):
    draft_id = await manager.submit_draft(
        recipient="team@co.com",
        subject="Re: Update",
        body="Draft update.",
        priority="LOW",
        risk_level="low",
    )

    await manager.handle_owner_reply("sounds good", "+923001234567")

    # Gmail NOT called
    gmail_client.call_tool.assert_not_called()

    # File still in Pending_Approval
    assert (vault / "Pending_Approval" / f"{draft_id}.md").exists()

    # Clarification message sent via WhatsApp
    whatsapp_client.call_tool.assert_called()
    last_call = whatsapp_client.call_tool.call_args
    body = last_call[0][1]["body"]
    assert "approve" in body.lower() or "reject" in body.lower()
