"""End-to-end integration test for briefing pipeline -- all MCPs mocked."""
import pytest
from unittest.mock import AsyncMock, patch
from pathlib import Path
import tempfile


@pytest.mark.integration
@pytest.mark.asyncio
async def test_daily_briefing_e2e_mocked():
    """Full daily briefing pipeline with all MCPs mocked."""
    import orchestrator.ceo_briefing as cb

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "CEO_Briefings").mkdir()
        (tmp_path / "Logs").mkdir()
        original_vault = cb.VAULT_PATH
        original_dir = cb.BRIEFING_DIR
        original_log = cb.LOG_DIR
        original_log_file = cb.BRIEFING_LOG
        cb.VAULT_PATH = tmp_path
        cb.BRIEFING_DIR = tmp_path / "CEO_Briefings"
        cb.LOG_DIR = tmp_path / "Logs"
        cb.BRIEFING_LOG = cb.LOG_DIR / "ceo_briefing.jsonl"

        with patch.object(cb, "collect_email_summary", return_value={"counts": {"high": 2, "medium": 5}}), \
             patch.object(cb, "collect_calendar_section", return_value={"events": []}), \
             patch.object(cb, "collect_odoo_section", return_value={"note": "No overdue invoices"}), \
             patch.object(cb, "collect_social_section", return_value={"posts": []}), \
             patch.object(cb, "_llm_draft", side_effect=Exception("LLM mocked off")), \
             patch.object(cb, "send_hitl_notification", return_value=None), \
             patch.object(cb, "check_approval_and_email", return_value={}):
            result = await cb.run_daily_briefing()

        cb.VAULT_PATH = original_vault
        cb.BRIEFING_DIR = original_dir
        cb.LOG_DIR = original_log
        cb.BRIEFING_LOG = original_log_file

        assert result["status"] == "complete"
        files = list((tmp_path / "CEO_Briefings").glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "---" in content  # YAML frontmatter
        assert "[TEMPLATE MODE]" in content  # fallback triggered
        assert "## " in content  # sections present


@pytest.mark.integration
@pytest.mark.asyncio
async def test_weekly_audit_e2e_mocked():
    """Full weekly audit pipeline with all MCPs mocked."""
    import orchestrator.weekly_audit as wa

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "CEO_Briefings").mkdir()
        (tmp_path / "Logs").mkdir()
        original_vault = wa.VAULT_PATH
        original_dir = wa.BRIEFING_DIR
        original_log = wa.LOG_DIR
        original_log_file = wa.BRIEFING_LOG
        wa.VAULT_PATH = tmp_path
        wa.BRIEFING_DIR = tmp_path / "CEO_Briefings"
        wa.LOG_DIR = tmp_path / "Logs"
        wa.BRIEFING_LOG = wa.LOG_DIR / "ceo_briefing.jsonl"

        with patch.object(wa, "collect_full_gl", return_value={"total_assets": 1000}), \
             patch.object(wa, "collect_full_ar", return_value={"total_receivable": 500}), \
             patch.object(wa, "collect_invoices_due", return_value={"overdue": [], "upcoming": []}), \
             patch.object(wa, "collect_7day_social_rollup", return_value={"total": 3}), \
             patch.object(wa, "collect_7day_email_rollup", return_value={"total": 10}), \
             patch.object(wa, "_llm_draft_weekly", side_effect=Exception("LLM mocked off")), \
             patch.object(wa, "send_hitl_notification", return_value=None):
            result = await wa.run_weekly_audit()

        wa.VAULT_PATH = original_vault
        wa.BRIEFING_DIR = original_dir
        wa.LOG_DIR = original_log
        wa.BRIEFING_LOG = original_log_file

        assert result["status"] == "complete"
        files = list((tmp_path / "CEO_Briefings").glob("week-*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "[TEMPLATE MODE]" in content
