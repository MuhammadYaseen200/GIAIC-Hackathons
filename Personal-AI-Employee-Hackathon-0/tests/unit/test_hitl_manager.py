"""Unit tests for HITLManager (T016).

Tests the vault-filesystem state machine for draft approval:
submit_draft, send_batch_notification, handle_owner_reply,
check_timeouts, concurrent drafts, collision detection.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import yaml

from orchestrator.hitl_manager import HITLManager, PRIORITY_EMOJI


@pytest.fixture
def vault(tmp_path):
    """Create a vault directory structure."""
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
    client.call_tool = AsyncMock(return_value={"message_id": "sent-123", "sent_at": "2026-03-04T00:00:00Z"})
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


# ── T016: submit_draft creates correct vault file ───────────────────────

@pytest.mark.asyncio
async def test_submit_draft_creates_file_with_correct_frontmatter(manager, vault):
    draft_id = await manager.submit_draft(
        recipient="boss@company.com",
        subject="Re: Urgent Q1",
        body="Draft body text here",
        priority="HIGH",
        risk_level="low",
    )

    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    assert draft_path.exists()

    meta = _read_frontmatter(draft_path)
    assert meta["type"] == "approval_request"
    assert meta["status"] == "pending"
    assert meta["risk_level"] == "low"
    assert meta["priority"] == "HIGH"
    assert meta["reversible"] is False
    assert meta["notified_at"] is None
    assert meta["draft_id"] == draft_id
    assert meta["recipient"] == "boss@company.com"
    assert meta["subject"] == "Re: Urgent Q1"


# ── T016: send_batch_notification calls WhatsApp MCP with correct format ──

@pytest.mark.asyncio
async def test_send_batch_notification_format(manager, vault, whatsapp_client):
    await manager.submit_draft(
        recipient="boss@co.com", subject="Urgent", body="body",
        priority="HIGH", risk_level="low",
    )
    await manager.submit_draft(
        recipient="client@co.com", subject="Meeting", body="body",
        priority="MED", risk_level="low",
    )
    await manager.submit_draft(
        recipient="info@co.com", subject="Update", body="body",
        priority="LOW", risk_level="low",
    )

    await manager.send_batch_notification()

    whatsapp_client.call_tool.assert_called_once()
    call_args = whatsapp_client.call_tool.call_args
    assert call_args[0][0] == "send_message"
    body = call_args[0][1]["body"]
    assert call_args[0][1]["to"] == "+923001234567"

    # Verify emojis present
    assert "\U0001f534" in body  # red circle for HIGH
    assert "\U0001f7e1" in body  # yellow circle for MED
    assert "\U0001f7e2" in body  # green circle for LOW
    assert "approve" in body.lower() or "reject" in body.lower()


# ── T016: handle_owner_reply approve → Gmail called + file moved ─────────

@pytest.mark.asyncio
async def test_handle_approve_sends_email_and_moves_file(manager, vault, gmail_client, whatsapp_client):
    draft_id = await manager.submit_draft(
        recipient="boss@co.com", subject="Re: Q1", body="Draft content",
        priority="HIGH", risk_level="low",
    )

    await manager.handle_owner_reply(f"approve {draft_id}", "+923001234567")

    # Gmail MCP send_email called
    gmail_client.call_tool.assert_called_once()
    call_args = gmail_client.call_tool.call_args
    assert call_args[0][0] == "send_email"
    assert call_args[0][1]["to"] == "boss@co.com"
    assert call_args[0][1]["subject"] == "Re: Q1"

    # File moved to Approved/
    assert not (vault / "Pending_Approval" / f"{draft_id}.md").exists()
    assert (vault / "Approved" / f"{draft_id}.md").exists()

    # Decision logged
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    assert log_path.exists()
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["draft_id"] == draft_id
    assert entry["decision"] == "approved"


# ── T016: handle_owner_reply reject → Gmail NOT called + file in Rejected ──

@pytest.mark.asyncio
async def test_handle_reject_no_email_and_moves_to_rejected(manager, vault, gmail_client):
    draft_id = await manager.submit_draft(
        recipient="boss@co.com", subject="Re: Q1", body="Draft content",
        priority="MED", risk_level="low",
    )

    await manager.handle_owner_reply(f"reject {draft_id}", "+923001234567")

    # Gmail MCP NOT called
    gmail_client.call_tool.assert_not_called()

    # File moved to Rejected/
    assert not (vault / "Pending_Approval" / f"{draft_id}.md").exists()
    assert (vault / "Rejected" / f"{draft_id}.md").exists()

    # Decision logged
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["decision"] == "rejected"


# ── T016: handle_owner_reply ambiguous → clarification, no irreversible ──

@pytest.mark.asyncio
async def test_handle_ambiguous_reply_sends_clarification(manager, vault, gmail_client, whatsapp_client):
    draft_id = await manager.submit_draft(
        recipient="boss@co.com", subject="Re: Q1", body="Draft content",
        priority="MED", risk_level="low",
    )

    await manager.handle_owner_reply("ok", "+923001234567")

    # Gmail NOT called
    gmail_client.call_tool.assert_not_called()

    # WhatsApp clarification sent
    whatsapp_client.call_tool.assert_called()
    last_call = whatsapp_client.call_tool.call_args
    body = last_call[0][1]["body"]
    assert "approve" in body.lower() or "reject" in body.lower()

    # File still in Pending_Approval
    assert (vault / "Pending_Approval" / f"{draft_id}.md").exists()


# ── T016: check_timeouts at 24h → awaiting_reminder + reminder sent ──

@pytest.mark.asyncio
async def test_check_timeouts_24h_sends_reminder(manager, vault, whatsapp_client):
    draft_id = await manager.submit_draft(
        recipient="boss@co.com", subject="Re: Q1", body="body",
        priority="MED", risk_level="low",
    )

    # Backdate created_at to 25 hours ago
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    meta = _read_frontmatter(draft_path)
    old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    meta["created_at"] = old_time
    body_text = draft_path.read_text().split("---", 2)[2].strip() if "---" in draft_path.read_text() else ""
    content = f"---\n{yaml.dump(meta, default_flow_style=False)}---\n\n{body_text}\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.check_timeouts()

    # Status updated to awaiting_reminder
    meta_after = _read_frontmatter(draft_path)
    assert meta_after["status"] == "awaiting_reminder"

    # Reminder sent via WhatsApp
    whatsapp_client.call_tool.assert_called()
    last_call = whatsapp_client.call_tool.call_args
    body = last_call[0][1]["body"]
    assert "reminder" in body.lower() or "pending" in body.lower()


# ── T016: check_timeouts at 48h → timed_out, no Gmail call ──

@pytest.mark.asyncio
async def test_check_timeouts_48h_times_out(manager, vault, gmail_client, whatsapp_client):
    draft_id = await manager.submit_draft(
        recipient="boss@co.com", subject="Re: Q1", body="body",
        priority="MED", risk_level="low",
    )

    # Backdate created_at to 49 hours ago
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    meta = _read_frontmatter(draft_path)
    old_time = (datetime.now(timezone.utc) - timedelta(hours=49)).isoformat()
    meta["created_at"] = old_time
    body_text = draft_path.read_text().split("---", 2)[2].strip() if "---" in draft_path.read_text() else ""
    content = f"---\n{yaml.dump(meta, default_flow_style=False)}---\n\n{body_text}\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.check_timeouts()

    # Status updated to timed_out
    meta_after = _read_frontmatter(draft_path)
    assert meta_after["status"] == "timed_out"

    # Gmail NOT called
    gmail_client.call_tool.assert_not_called()


# ── T016: 3 concurrent drafts — approve draft 2 only ──

@pytest.mark.asyncio
async def test_concurrent_drafts_approve_one(manager, vault, gmail_client):
    id1 = await manager.submit_draft(
        recipient="a@co.com", subject="Draft 1", body="body1",
        priority="HIGH", risk_level="low",
    )
    id2 = await manager.submit_draft(
        recipient="b@co.com", subject="Draft 2", body="body2",
        priority="MED", risk_level="low",
    )
    id3 = await manager.submit_draft(
        recipient="c@co.com", subject="Draft 3", body="body3",
        priority="LOW", risk_level="low",
    )

    await manager.handle_owner_reply(f"approve {id2}", "+923001234567")

    # Draft 2 moved to Approved
    assert not (vault / "Pending_Approval" / f"{id2}.md").exists()
    assert (vault / "Approved" / f"{id2}.md").exists()

    # Drafts 1 and 3 still in Pending_Approval
    assert (vault / "Pending_Approval" / f"{id1}.md").exists()
    assert (vault / "Pending_Approval" / f"{id3}.md").exists()


# ── T016: draft ID collision detection ──

@pytest.mark.asyncio
async def test_draft_id_collision_detection(manager, vault):
    """Two drafts created in quick succession get different IDs."""
    id1 = await manager.submit_draft(
        recipient="a@co.com", subject="Draft 1", body="body1",
        priority="HIGH", risk_level="low",
    )
    id2 = await manager.submit_draft(
        recipient="b@co.com", subject="Draft 2", body="body2",
        priority="MED", risk_level="low",
    )

    assert id1 != id2
    assert (vault / "Pending_Approval" / f"{id1}.md").exists()
    assert (vault / "Pending_Approval" / f"{id2}.md").exists()
