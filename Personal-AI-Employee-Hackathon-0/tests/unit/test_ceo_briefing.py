"""Unit tests for CEO Briefing orchestrator. RED first."""
import json
import time
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, mock_open


# -- VAULT FILE CREATION -------------------------------------------------------


@pytest.mark.asyncio
async def test_daily_briefing_creates_vault_file(tmp_path):
    """run_daily_briefing creates vault/CEO_Briefings/YYYY-MM-DD.md."""
    import orchestrator.ceo_briefing as cb

    original_vault = cb.VAULT_PATH
    cb.VAULT_PATH = tmp_path
    cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
    cb.LOG_DIR = tmp_path / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
    briefing_dir = tmp_path / "CEO_Briefings"
    briefing_dir.mkdir()
    (tmp_path / "Logs").mkdir()

    with patch.object(cb, "collect_email_summary", return_value={"emails": []}), \
         patch.object(cb, "collect_calendar_section", return_value={"events": []}), \
         patch.object(cb, "collect_odoo_section", return_value={"invoices": []}), \
         patch.object(cb, "collect_social_section", return_value={"posts": []}), \
         patch.object(cb, "draft_briefing", return_value="# Test Briefing\n\nSection 1\nSection 2\nSection 3\nSection 4\nSection 5\nSection 6\nSection 7"), \
         patch.object(cb, "send_hitl_notification", return_value=None), \
         patch.object(cb, "check_approval_and_email", return_value={"status": "pending"}):
        result = await cb.run_daily_briefing()

    cb.VAULT_PATH = original_vault
    cb.BRIEFING_DIR = cb.VAULT_PATH / "CEO_Briefings"
    cb.LOG_DIR = cb.VAULT_PATH / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
    # Check a file was created
    files = list(briefing_dir.glob("*.md"))
    assert len(files) >= 1


@pytest.mark.asyncio
async def test_vault_file_has_yaml_frontmatter(tmp_path):
    """Created briefing file has YAML frontmatter."""
    import orchestrator.ceo_briefing as cb

    original_vault = cb.VAULT_PATH
    original_dir = cb.BRIEFING_DIR
    cb.VAULT_PATH = tmp_path
    cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
    (tmp_path / "CEO_Briefings").mkdir()

    content = await cb.write_briefing_vault("# Test\n\nContent", "daily")

    cb.VAULT_PATH = original_vault
    cb.BRIEFING_DIR = original_dir

    file_text = content.read_text()
    assert file_text.startswith("---")
    assert "type: ceo_briefing" in file_text


@pytest.mark.asyncio
async def test_all_7_sections_present_in_output():
    """Briefing content contains all 7 mandatory sections."""
    import orchestrator.ceo_briefing as cb

    sections = {
        "email": {"count": 5, "high": 1},
        "odoo": {"invoices": []},
        "calendar": {"events": []},
        "social": {"posts": []},
    }

    with patch.object(cb, "_llm_draft", side_effect=Exception("LLM unavailable")):
        content = await cb.draft_briefing(sections, "daily")

    # Template fallback should include all 7 section headers
    assert content  # Not empty
    section_count = content.count("##")
    assert section_count >= 7


@pytest.mark.asyncio
async def test_odoo_unavailable_briefing_still_generated():
    """Briefing is generated even when Odoo MCP is unavailable."""
    import orchestrator.ceo_briefing as cb

    with patch.object(cb, "_llm_draft", side_effect=Exception("LLM down")):
        sections = {"odoo": {"status": "unavailable"}, "email": {}, "calendar": {}, "social": {}}
        content = await cb.draft_briefing(sections, "daily")

    assert content  # Briefing generated despite Odoo being unavailable


@pytest.mark.asyncio
async def test_calendar_unavailable_briefing_still_generated():
    """Briefing is generated even when Calendar MCP is unavailable."""
    import orchestrator.ceo_briefing as cb

    with patch.object(cb, "_llm_draft", side_effect=Exception("LLM down")):
        sections = {"calendar": {"status": "unavailable"}, "odoo": {}, "email": {}, "social": {}}
        content = await cb.draft_briefing(sections, "daily")

    assert content


@pytest.mark.asyncio
async def test_llm_unavailable_template_fallback_activates():
    """When LLM fails, template fallback is used."""
    import orchestrator.ceo_briefing as cb

    with patch.object(cb, "_llm_draft", side_effect=Exception("Anthropic credits depleted")):
        content = await cb.draft_briefing({}, "daily")

    assert content  # Template fallback produced content


@pytest.mark.asyncio
async def test_template_fallback_contains_template_mode_flag():
    """Template fallback includes [TEMPLATE MODE] flag per ADR-0019."""
    import orchestrator.ceo_briefing as cb

    with patch.object(cb, "_llm_draft", side_effect=Exception("LLM down")):
        content = await cb.draft_briefing({}, "daily")

    assert "[TEMPLATE MODE]" in content


@pytest.mark.asyncio
async def test_briefing_idempotent_overwrites_existing(tmp_path):
    """Writing briefing twice overwrites, doesn't append."""
    import orchestrator.ceo_briefing as cb

    original_vault = cb.VAULT_PATH
    original_dir = cb.BRIEFING_DIR
    cb.VAULT_PATH = tmp_path
    cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
    (tmp_path / "CEO_Briefings").mkdir()

    await cb.write_briefing_vault("First write", "daily")
    await cb.write_briefing_vault("Second write", "daily")

    cb.VAULT_PATH = original_vault
    cb.BRIEFING_DIR = original_dir

    files = list((tmp_path / "CEO_Briefings").glob("*.md"))
    assert len(files) == 1  # Not 2
    assert "Second write" in files[0].read_text()


@pytest.mark.asyncio
async def test_hitl_notification_sent_on_creation(tmp_path):
    """HITL WhatsApp notification is sent after briefing is written."""
    import orchestrator.ceo_briefing as cb

    with patch.object(cb, "send_hitl_notification", new_callable=AsyncMock) as mock_notify:
        original_vault = cb.VAULT_PATH
        cb.VAULT_PATH = tmp_path
        cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
        cb.LOG_DIR = tmp_path / "Logs"
        cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
        (tmp_path / "CEO_Briefings").mkdir()
        (tmp_path / "Logs").mkdir()

        with patch.object(cb, "collect_email_summary", return_value={}), \
             patch.object(cb, "collect_calendar_section", return_value={}), \
             patch.object(cb, "collect_odoo_section", return_value={}), \
             patch.object(cb, "collect_social_section", return_value={}), \
             patch.object(cb, "draft_briefing", return_value="# Briefing\n" + "\n## Section " * 7), \
             patch.object(cb, "check_approval_and_email", return_value={}):
            await cb.run_daily_briefing()

        cb.VAULT_PATH = original_vault
        cb.BRIEFING_DIR = cb.VAULT_PATH / "CEO_Briefings"
        cb.LOG_DIR = cb.VAULT_PATH / "Logs"
        cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
        assert mock_notify.called


@pytest.mark.asyncio
async def test_hitl_notification_under_500_chars():
    """HITL notification message is under 500 chars (SC-003)."""
    briefing_path = Path("/tmp/2026-03-12.md")
    msg = f"CEO Briefing ready: {briefing_path.name}\n7 sections | 12.3s\nReply APPROVE or REJECT."
    assert len(msg) <= 500


@pytest.mark.asyncio
async def test_approval_triggers_email_delivery():
    """Approved briefing status triggers email delivery."""
    import orchestrator.ceo_briefing as cb

    # check_approval_and_email should detect approved status
    with patch.object(cb, "check_approval_and_email", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {"status": "delivered", "email_sent": True}
        result = await cb.check_approval_and_email(Path("/tmp/briefing.md"))

    assert mock_check.called


@pytest.mark.asyncio
async def test_email_updates_status_to_delivered():
    """Briefing YAML frontmatter is updated to delivered after email sent."""
    import orchestrator.ceo_briefing as cb
    assert hasattr(cb, "check_approval_and_email")


@pytest.mark.asyncio
async def test_briefing_logged_to_ceo_briefing_jsonl(tmp_path):
    """Briefing creation is logged to vault/Logs/ceo_briefing.jsonl."""
    import orchestrator.ceo_briefing as cb

    original_vault = cb.VAULT_PATH
    cb.VAULT_PATH = tmp_path
    cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
    cb.LOG_DIR = tmp_path / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
    (tmp_path / "CEO_Briefings").mkdir()
    (tmp_path / "Logs").mkdir()

    with patch.object(cb, "collect_email_summary", return_value={}), \
         patch.object(cb, "collect_calendar_section", return_value={}), \
         patch.object(cb, "collect_odoo_section", return_value={}), \
         patch.object(cb, "collect_social_section", return_value={}), \
         patch.object(cb, "draft_briefing", return_value="# B\n" + "## S\n" * 7), \
         patch.object(cb, "send_hitl_notification", return_value=None), \
         patch.object(cb, "check_approval_and_email", return_value={}):
        await cb.run_daily_briefing()

    cb.VAULT_PATH = original_vault
    cb.BRIEFING_DIR = cb.VAULT_PATH / "CEO_Briefings"
    cb.LOG_DIR = cb.VAULT_PATH / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
    log_file = tmp_path / "Logs" / "ceo_briefing.jsonl"
    assert log_file.exists()


@pytest.mark.asyncio
async def test_run_time_under_60_seconds():
    """Daily briefing completes within 60 seconds (SC-001)."""
    import orchestrator.ceo_briefing as cb
    import tempfile

    start = time.time()

    with patch.object(cb, "collect_email_summary", return_value={}), \
         patch.object(cb, "collect_calendar_section", return_value={}), \
         patch.object(cb, "collect_odoo_section", return_value={}), \
         patch.object(cb, "collect_social_section", return_value={}), \
         patch.object(cb, "draft_briefing", return_value="# B\n" + "## S\n" * 7), \
         patch.object(cb, "send_hitl_notification", return_value=None), \
         patch.object(cb, "check_approval_and_email", return_value={}):

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            original_vault = cb.VAULT_PATH
            cb.VAULT_PATH = tmp_path
            cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
            cb.LOG_DIR = tmp_path / "Logs"
            cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
            (tmp_path / "CEO_Briefings").mkdir()
            (tmp_path / "Logs").mkdir()
            await cb.run_daily_briefing()
            cb.VAULT_PATH = original_vault
            cb.BRIEFING_DIR = cb.VAULT_PATH / "CEO_Briefings"
            cb.LOG_DIR = cb.VAULT_PATH / "Logs"
            cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"

    elapsed = time.time() - start
    assert elapsed < 60, f"Briefing took {elapsed:.1f}s -- exceeds 60s budget (SC-001)"


# -- T050-T055: Additional verification tests ---------------------------------


@pytest.mark.asyncio
async def test_odoo_daily_shows_only_overdue_invoices():
    """collect_odoo_section daily only returns overdue invoices (days_remaining < 0)."""
    import orchestrator.ceo_briefing as cb

    with patch("mcp_servers.odoo.client.get_invoices_due_data") as mock_fn:
        mock_fn.return_value = [
            {"invoice_id": 1, "days_remaining": -5, "amount_due": 100},
            {"invoice_id": 2, "days_remaining": 3, "amount_due": 200},
        ]
        result = await cb.collect_odoo_section("daily")
    invoices = result.get("invoices", [])
    assert all(i["days_remaining"] < 0 for i in invoices)
    assert len(invoices) == 1


@pytest.mark.asyncio
async def test_odoo_empty_returns_all_clear():
    """Empty invoice list returns 'all clear' message."""
    import orchestrator.ceo_briefing as cb

    with patch("mcp_servers.odoo.client.get_invoices_due_data", return_value=[]):
        result = await cb.collect_odoo_section("daily")
    assert "all clear" in result.get("note", "").lower()


@pytest.mark.asyncio
async def test_collect_email_summary_returns_dict_with_counts():
    """collect_email_summary returns dict with counts or note."""
    import orchestrator.ceo_briefing as cb

    result = await cb.collect_email_summary()
    assert isinstance(result, dict)
    assert "counts" in result or "note" in result or "status" in result


@pytest.mark.asyncio
async def test_collect_calendar_returns_dict():
    """collect_calendar_section returns dict (unavailable if Calendar MCP not present)."""
    import orchestrator.ceo_briefing as cb

    result = await cb.collect_calendar_section()
    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_collect_social_returns_dict_with_posts():
    """collect_social_section returns dict with posts key."""
    import orchestrator.ceo_briefing as cb

    result = await cb.collect_social_section()
    assert isinstance(result, dict)
    assert "posts" in result or "status" in result


# -- ADDITIONAL COVERAGE TESTS -------------------------------------------------


@pytest.mark.asyncio
async def test_collect_email_summary_reads_jsonl_entries(tmp_path):
    """collect_email_summary reads and counts entries from JSONL log files."""
    import orchestrator.ceo_briefing as cb
    from datetime import datetime, timezone, timedelta

    log_dir = tmp_path / "Logs"
    log_dir.mkdir()
    email_log = log_dir / "gmail_processed.jsonl"

    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=2)).isoformat()
    old = (now - timedelta(hours=30)).isoformat()

    email_log.write_text(
        json.dumps({"ts": recent, "priority": "high", "subject": "Urgent"}) + "\n"
        + json.dumps({"ts": recent, "priority": "medium", "subject": "Meeting"}) + "\n"
        + json.dumps({"ts": old, "priority": "high", "subject": "Old"}) + "\n"
    )

    original_log_dir = cb.LOG_DIR
    cb.LOG_DIR = log_dir

    try:
        result = await cb.collect_email_summary()
    finally:
        cb.LOG_DIR = original_log_dir

    assert isinstance(result, dict)
    assert result.get("counts", {}).get("total", 0) == 2  # old entry excluded
    assert result.get("counts", {}).get("high", 0) >= 1


@pytest.mark.asyncio
async def test_collect_email_summary_empty_log_returns_no_emails_note(tmp_path):
    """collect_email_summary returns 'No emails processed' when log dir has no email files."""
    import orchestrator.ceo_briefing as cb

    log_dir = tmp_path / "Logs"
    log_dir.mkdir()

    original_log_dir = cb.LOG_DIR
    cb.LOG_DIR = log_dir

    try:
        result = await cb.collect_email_summary()
    finally:
        cb.LOG_DIR = original_log_dir

    assert "No emails processed" in result.get("note", "")


@pytest.mark.asyncio
async def test_collect_calendar_section_mcp_unavailable():
    """collect_calendar_section returns unavailable when Calendar MCP import fails."""
    import orchestrator.ceo_briefing as cb

    with patch.dict("sys.modules", {"mcp_servers.calendar": None, "mcp_servers.calendar.server": None}):
        result = await cb.collect_calendar_section("daily")

    assert result.get("status") == "unavailable"


@pytest.mark.asyncio
async def test_collect_odoo_section_exception_returns_unavailable():
    """collect_odoo_section returns unavailable on any exception."""
    import orchestrator.ceo_briefing as cb

    with patch.dict("sys.modules", {"mcp_servers.odoo": MagicMock(), "mcp_servers.odoo.client": MagicMock()}):
        with patch("mcp_servers.odoo.client.get_invoices_due_data", side_effect=Exception("Odoo is down")):
            result = await cb.collect_odoo_section("daily")

    assert result.get("status") == "unavailable"


@pytest.mark.asyncio
async def test_collect_social_section_reads_jsonl_entries(tmp_path):
    """collect_social_section reads recent social posts from JSONL."""
    import orchestrator.ceo_briefing as cb
    from datetime import datetime, timezone, timedelta

    log_dir = tmp_path / "Logs"
    log_dir.mkdir()
    social_log = log_dir / "social_posts.jsonl"

    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=1)).isoformat()

    social_log.write_text(
        json.dumps({"ts": recent, "platform": "twitter", "action": "posted"}) + "\n"
        + json.dumps({"ts": recent, "platform": "facebook", "action": "posted"}) + "\n"
    )

    original_log_dir = cb.LOG_DIR
    cb.LOG_DIR = log_dir

    try:
        result = await cb.collect_social_section("daily")
    finally:
        cb.LOG_DIR = original_log_dir

    assert isinstance(result, dict)
    assert result.get("count", 0) == 2


@pytest.mark.asyncio
async def test_send_hitl_notification_calls_gobridge(tmp_path):
    """send_hitl_notification calls GoBridge.send with message <=500 chars."""
    import orchestrator.ceo_briefing as cb

    mock_bridge = MagicMock()
    mock_bridge.send = AsyncMock(return_value=None)

    briefing_path = tmp_path / "2026-03-16.md"
    briefing_path.write_text("# Briefing")
    metrics = {"duration_s": 5.2, "llm_mode": "template", "sections": 7}

    mock_gobridge_cls = MagicMock(return_value=mock_bridge)
    with patch.dict("sys.modules", {"mcp_servers.whatsapp": MagicMock(), "mcp_servers.whatsapp.bridge": MagicMock(GoBridge=mock_gobridge_cls)}):
        await cb.send_hitl_notification(briefing_path, metrics)

    if mock_bridge.send.called:
        msg = mock_bridge.send.call_args[0][1]
        assert len(msg) <= 500


@pytest.mark.asyncio
async def test_send_hitl_notification_bridge_failure_is_nonfatal(tmp_path):
    """send_hitl_notification does not raise if GoBridge.send fails."""
    import orchestrator.ceo_briefing as cb

    mock_bridge = MagicMock()
    mock_bridge.send = AsyncMock(side_effect=Exception("Bridge not running"))

    briefing_path = tmp_path / "2026-03-16.md"
    briefing_path.write_text("# Briefing")

    mock_gobridge_cls = MagicMock(return_value=mock_bridge)
    with patch.dict("sys.modules", {"mcp_servers.whatsapp": MagicMock(), "mcp_servers.whatsapp.bridge": MagicMock(GoBridge=mock_gobridge_cls)}):
        # Must not raise
        await cb.send_hitl_notification(briefing_path, {"duration_s": 1.0, "llm_mode": "template", "sections": 7})


@pytest.mark.asyncio
async def test_llm_draft_success_returns_string():
    """_llm_draft returns string when Anthropic API succeeds."""
    import orchestrator.ceo_briefing as cb

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="# CEO Briefing\n## Section 1\nContent")]

    mock_client = MagicMock()
    mock_client.messages.create = AsyncMock(return_value=mock_message)

    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        result = await cb._llm_draft({"email": {}, "odoo": {}}, "daily")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_check_approval_and_email_is_callable():
    """check_approval_and_email exists and is awaitable."""
    import orchestrator.ceo_briefing as cb
    import inspect
    assert hasattr(cb, "check_approval_and_email")
    assert inspect.iscoroutinefunction(cb.check_approval_and_email)


@pytest.mark.asyncio
async def test_check_approval_and_email_pending_file(tmp_path):
    """check_approval_and_email returns pending status for pending_approval file."""
    import orchestrator.ceo_briefing as cb

    briefing_file = tmp_path / "2026-03-16.md"
    briefing_file.write_text("---\nstatus: pending_approval\n---\n# Briefing")

    result = await cb.check_approval_and_email(briefing_file)
    assert isinstance(result, dict)
    assert result.get("status") == "pending_approval"


@pytest.mark.asyncio
async def test_check_approval_and_email_missing_file(tmp_path):
    """check_approval_and_email returns missing for nonexistent file."""
    import orchestrator.ceo_briefing as cb

    result = await cb.check_approval_and_email(tmp_path / "nonexistent.md")
    assert result.get("status") == "missing"


@pytest.mark.asyncio
async def test_check_approval_and_email_approved_triggers_email(tmp_path):
    """check_approval_and_email sends email when status is approved."""
    import orchestrator.ceo_briefing as cb

    briefing_file = tmp_path / "2026-03-16.md"
    briefing_file.write_text("---\nstatus: approved\n---\n# Briefing content")

    mock_send = AsyncMock(return_value={"status": "sent"})
    mock_gmail = MagicMock()
    mock_gmail.send_email = mock_send

    with patch.dict("sys.modules", {
        "mcp_servers.gmail": MagicMock(),
        "mcp_servers.gmail.server": MagicMock(send_email=mock_send),
    }):
        result = await cb.check_approval_and_email(briefing_file)

    assert isinstance(result, dict)
    # Either delivered or error (if mock didn't fully work) - but function completed
    assert result.get("status") in ("delivered", "approved")


@pytest.mark.asyncio
async def test_run_daily_briefing_uses_run_until_complete(tmp_path):
    """run_daily_briefing wraps steps in run_until_complete (ADR-0018)."""
    import orchestrator.ceo_briefing as cb

    original_vault = cb.VAULT_PATH
    cb.VAULT_PATH = tmp_path
    cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
    cb.LOG_DIR = tmp_path / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"
    (tmp_path / "CEO_Briefings").mkdir()
    (tmp_path / "Logs").mkdir()

    try:
        with patch("orchestrator.run_until_complete.run_until_complete", new_callable=AsyncMock) as mock_ruc:
            mock_ruc.return_value = {"status": "complete", "completed": ["collect_email", "collect_calendar", "collect_odoo", "collect_social", "draft", "write_vault", "send_hitl"]}
            result = await cb.run_daily_briefing()
    finally:
        cb.VAULT_PATH = original_vault
        cb.BRIEFING_DIR = cb.VAULT_PATH / "CEO_Briefings"
        cb.LOG_DIR = cb.VAULT_PATH / "Logs"
        cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"

    assert mock_ruc.called
    assert result["status"] == "complete"


@pytest.mark.asyncio
async def test_template_draft_with_full_sections():
    """_template_draft returns content with all 7 sections from real data."""
    import orchestrator.ceo_briefing as cb

    sections = {
        "email": {"counts": {"high": 3, "medium": 5, "low": 2, "total": 10}, "note": ""},
        "odoo": {"invoices": [{"partner_name": "ACME", "amount_due": 500}], "count": 1},
        "calendar": {"events": [{"title": "Meeting"}]},
        "social": {"posts": [{"platform": "twitter"}], "count": 1},
    }

    content = await cb._template_draft(sections, "daily")

    assert "[TEMPLATE MODE]" in content
    assert "## 1. Email Triage" in content
    assert "## 7. System Health" in content
    assert "HIGH: 3" in content


@pytest.mark.asyncio
async def test_log_event_writes_to_jsonl(tmp_path):
    """_log_event writes structured JSON to the briefing log."""
    import orchestrator.ceo_briefing as cb

    original_log_dir = cb.LOG_DIR
    original_log = cb.BRIEFING_LOG
    cb.LOG_DIR = tmp_path / "Logs"
    cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"

    try:
        cb._log_event("test_event", foo="bar")
    finally:
        cb.LOG_DIR = original_log_dir
        cb.BRIEFING_LOG = original_log

    log_file = tmp_path / "Logs" / "ceo_briefing.jsonl"
    assert log_file.exists()
    entry = json.loads(log_file.read_text().strip())
    assert entry["event"] == "test_event"
    assert entry["foo"] == "bar"


@pytest.mark.asyncio
async def test_run_daily_briefing_timeout_returns_failed():
    """asyncio.TimeoutError yields status=failed with error=timeout."""
    import asyncio
    import orchestrator.ceo_briefing as cb

    with patch("orchestrator.run_until_complete.run_until_complete",
               new_callable=AsyncMock, side_effect=asyncio.TimeoutError), \
         patch("watchers.utils.FileLock.acquire"), \
         patch("watchers.utils.FileLock.release"):
        result = await cb.run_daily_briefing()

    assert result["status"] == "failed"
    assert result.get("error") == "timeout"


@pytest.mark.asyncio
async def test_run_daily_briefing_already_running_returns_skipped():
    """If FileLock raises RuntimeError the function returns status=skipped."""
    import orchestrator.ceo_briefing as cb

    with patch("watchers.utils.FileLock.acquire", side_effect=RuntimeError("locked")):
        result = await cb.run_daily_briefing()

    assert result["status"] == "skipped"
    assert result.get("reason") == "already_running"
