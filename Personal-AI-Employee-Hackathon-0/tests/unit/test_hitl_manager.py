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
        owner_number="+15550001234",
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
    assert call_args[0][1]["to"] == "+15550001234"

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

    await manager.handle_owner_reply(f"approve {draft_id}", "+15550001234")

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

    await manager.handle_owner_reply(f"reject {draft_id}", "+15550001234")

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

    await manager.handle_owner_reply("ok", "+15550001234")

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

    await manager.handle_owner_reply(f"approve {id2}", "+15550001234")

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


# ── Coverage boost: collision guard (line 52 — _read_frontmatter no-frontmatter) ──

def test_read_frontmatter_no_frontmatter(vault):
    """_read_frontmatter returns {} when file has no --- delimiters."""
    from orchestrator.hitl_manager import _read_frontmatter as _rf
    p = vault / "plain.md"
    p.write_text("No frontmatter here", encoding="utf-8")
    assert _rf(p) == {}


# ── Coverage boost: _read_body no-frontmatter fallback (line 62) ──

def test_read_body_no_frontmatter(vault):
    """_read_body returns full text when file has no --- delimiters."""
    from orchestrator.hitl_manager import _read_body as _rb
    p = vault / "plain.md"
    p.write_text("Just body text", encoding="utf-8")
    assert _rb(p) == "Just body text"


# ── Coverage boost: collision guard while-loop body (lines 158-159) ──

@pytest.mark.asyncio
async def test_submit_draft_collision_guard(manager, vault):
    """When generated draft_id already exists on disk, a new one is generated."""
    # Pre-create a file that will collide with the first generated ID
    with patch("orchestrator.hitl_manager._generate_draft_id") as mock_gen:
        mock_gen.side_effect = ["COLLIDE-001", "COLLIDE-001", "UNIQUE-002"]
        # First call returns COLLIDE-001, file exists check triggers loop
        # Create the collision file
        (vault / "Pending_Approval" / "COLLIDE-001.md").write_text("exists", encoding="utf-8")

        draft_id = await manager.submit_draft(
            recipient="a@co.com", subject="Test", body="body",
            priority="HIGH", risk_level="low",
        )
        assert draft_id == "UNIQUE-002"
        assert (vault / "Pending_Approval" / "UNIQUE-002.md").exists()


# ── Coverage boost: empty pending in send_batch_notification (line 196) ──

@pytest.mark.asyncio
async def test_send_batch_notification_empty(manager, vault, whatsapp_client):
    """send_batch_notification with no pending drafts does nothing."""
    # Ensure pending dir is empty (remove any .md files)
    for f in (vault / "Pending_Approval").glob("*.md"):
        f.unlink()

    await manager.send_batch_notification()
    whatsapp_client.call_tool.assert_not_called()


# ── Coverage boost: draft not found on approve (lines 331-338) ──

@pytest.mark.asyncio
async def test_approve_draft_not_found(manager, vault, whatsapp_client, gmail_client):
    """Approving a nonexistent draft sends 'Draft not found' via WhatsApp."""
    await manager.handle_owner_reply("approve NOTEXIST123", "+15550001234")

    whatsapp_client.call_tool.assert_called_once()
    body = whatsapp_client.call_tool.call_args[0][1]["body"]
    assert "Draft not found" in body
    gmail_client.call_tool.assert_not_called()


# ── Coverage boost: draft not found on reject (lines 398-405) ──

@pytest.mark.asyncio
async def test_reject_draft_not_found(manager, vault, whatsapp_client, gmail_client):
    """Rejecting a nonexistent draft sends 'Draft not found' via WhatsApp."""
    await manager.handle_owner_reply("reject NOTEXIST456", "+15550001234")

    whatsapp_client.call_tool.assert_called_once()
    body = whatsapp_client.call_tool.call_args[0][1]["body"]
    assert "Draft not found" in body
    gmail_client.call_tool.assert_not_called()


# ── Coverage boost: LinkedIn post approve path (lines 345-360) ──

@pytest.mark.asyncio
async def test_approve_linkedin_post(manager, vault, whatsapp_client, gmail_client):
    """Approving a linkedin_post sets status=approved in place, no email sent."""
    draft_id = "linkedin-test-001"
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    fm = {
        "type": "linkedin_post",
        "status": "pending",
        "draft_id": draft_id,
        "recipient": "",
        "subject": "My LinkedIn Post",
        "priority": "MED",
        "risk_level": "low",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nLinkedIn post body\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.handle_owner_reply(f"approve {draft_id}", "+15550001234")

    # File stays in Pending_Approval (not moved to Approved/)
    assert draft_path.exists()
    meta = _read_frontmatter(draft_path)
    assert meta["status"] == "approved"
    assert "decided_at" in meta

    # Gmail NOT called (LinkedIn doesn't send email)
    gmail_client.call_tool.assert_not_called()

    # WhatsApp confirmation sent
    whatsapp_client.call_tool.assert_called_once()
    body = whatsapp_client.call_tool.call_args[0][1]["body"]
    assert "LinkedIn" in body and "approved" in body.lower()

    # Audit log written
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    assert log_path.exists()
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["decision"] == "approved"
    assert entry["draft_id"] == draft_id


# ── Coverage boost: LinkedIn post reject path (lines 412-427) ──

@pytest.mark.asyncio
async def test_reject_linkedin_post(manager, vault, whatsapp_client, gmail_client):
    """Rejecting a linkedin_post sets status=rejected in place, no email sent."""
    draft_id = "linkedin-test-002"
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    fm = {
        "type": "linkedin_post",
        "status": "pending",
        "draft_id": draft_id,
        "recipient": "",
        "subject": "My LinkedIn Post",
        "priority": "LOW",
        "risk_level": "low",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nLinkedIn post body\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.handle_owner_reply(f"reject {draft_id}", "+15550001234")

    # File stays in Pending_Approval (LinkedIn path updates in place)
    assert draft_path.exists()
    meta = _read_frontmatter(draft_path)
    assert meta["status"] == "rejected"
    assert "decided_at" in meta

    # Gmail NOT called
    gmail_client.call_tool.assert_not_called()

    # WhatsApp rejection confirmation sent
    whatsapp_client.call_tool.assert_called_once()
    body = whatsapp_client.call_tool.call_args[0][1]["body"]
    assert "rejected" in body.lower()

    # Audit log written
    log_path = vault / "Logs" / "hitl_decisions.jsonl"
    entry = json.loads(log_path.read_text().strip().split("\n")[-1])
    assert entry["decision"] == "rejected"


# ── Coverage boost: _find_draft prefix/suffix/frontmatter match (lines 461-475) ──

@pytest.mark.asyncio
async def test_find_draft_by_suffix_match(manager, vault):
    """_find_draft matches by suffix of filename stem."""
    draft_id = "20260310-120000-abcd1234"
    draft_path = vault / "Pending_Approval" / f"{draft_id}.md"
    fm = {
        "type": "approval_request",
        "status": "pending",
        "draft_id": draft_id,
        "recipient": "x@co.com",
        "subject": "Test",
        "priority": "LOW",
        "risk_level": "low",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nbody\n"
    draft_path.write_text(content, encoding="utf-8")

    # Match by suffix (last part of the ID)
    await manager.handle_owner_reply("approve abcd1234", "+15550001234")

    # Should have found and approved it
    assert (vault / "Approved" / f"{draft_id}.md").exists()


# ── Coverage boost: check_timeouts with no created_at (line 286) ──

@pytest.mark.asyncio
async def test_check_timeouts_no_created_at(manager, vault, whatsapp_client):
    """check_timeouts skips drafts with no created_at field."""
    draft_path = vault / "Pending_Approval" / "no-date-draft.md"
    fm = {
        "type": "approval_request",
        "status": "pending",
        "draft_id": "no-date-draft",
        "recipient": "x@co.com",
        "subject": "Test",
        "priority": "LOW",
        "risk_level": "low",
        # No created_at!
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nbody\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.check_timeouts()

    # Status unchanged — draft was skipped
    meta = _read_frontmatter(draft_path)
    assert meta["status"] == "pending"
    whatsapp_client.call_tool.assert_not_called()


# ── Coverage boost: check_timeouts with invalid created_at (lines 290-291) ──

@pytest.mark.asyncio
async def test_check_timeouts_invalid_date(manager, vault, whatsapp_client):
    """check_timeouts skips drafts with unparseable created_at."""
    draft_path = vault / "Pending_Approval" / "bad-date-draft.md"
    fm = {
        "type": "approval_request",
        "status": "pending",
        "draft_id": "bad-date-draft",
        "recipient": "x@co.com",
        "subject": "Test",
        "priority": "LOW",
        "risk_level": "low",
        "created_at": "not-a-date",
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nbody\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.check_timeouts()

    meta = _read_frontmatter(draft_path)
    assert meta["status"] == "pending"
    whatsapp_client.call_tool.assert_not_called()


# ── Coverage boost: check_timeouts with naive datetime (line 294) ──

@pytest.mark.asyncio
async def test_check_timeouts_naive_datetime(manager, vault, whatsapp_client):
    """check_timeouts handles naive datetime (no tzinfo) by assuming UTC."""
    draft_path = vault / "Pending_Approval" / "naive-date-draft.md"
    # Use a naive ISO string (no +00:00 or Z suffix) that is 25h old
    naive_time = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%S")
    fm = {
        "type": "approval_request",
        "status": "pending",
        "draft_id": "naive-date-draft",
        "recipient": "x@co.com",
        "subject": "Test",
        "priority": "LOW",
        "risk_level": "low",
        "created_at": naive_time,
    }
    content = f"---\n{yaml.dump(fm, default_flow_style=False)}---\n\nbody\n"
    draft_path.write_text(content, encoding="utf-8")

    await manager.check_timeouts()

    meta = _read_frontmatter(draft_path)
    assert meta["status"] == "awaiting_reminder"
    whatsapp_client.call_tool.assert_called()
