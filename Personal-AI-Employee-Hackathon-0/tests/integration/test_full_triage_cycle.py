"""End-to-end integration test: full triage cycle with 3 mock emails (T031).

Tests validate:
    - 3 mock emails placed in vault/Needs_Action/ (draft_reply, archive, needs_info)
    - One poll cycle with sequential mock LLM
    - draft_reply email → draft file created in vault/Drafts/
    - archive email → file moved to vault/Done/
    - needs_info email → frontmatter updated with status=needs_info
    - 3 llm_decision_audit log entries + 1 poll_cycle_complete in orchestrator YYYY-MM-DD.log
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase


# ---------------------------------------------------------------------------
# Sequential mock provider — returns a different response per call (in order)
# ---------------------------------------------------------------------------

class _SequentialMockProvider(LLMProviderBase):
    """Returns responses in the order they are provided."""

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._call_count = 0

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        idx = min(self._call_count, len(self._responses) - 1)
        response = self._responses[idx]
        self._call_count += 1
        return (response, 100, 50)

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _archive_json() -> str:
    return json.dumps({
        "decision": "archive",
        "confidence": 0.95,
        "reasoning": "Newsletter, no action required.",
        "reply_body": None,
        "delegation_target": None,
        "info_needed": None,
    })


def _needs_info_json() -> str:
    return json.dumps({
        "decision": "needs_info",
        "confidence": 0.70,
        "reasoning": "Need more context before deciding.",
        "reply_body": None,
        "delegation_target": None,
        "info_needed": "Which product line is this referring to?",
    })


def _draft_reply_json() -> str:
    return json.dumps({
        "decision": "draft_reply",
        "confidence": 0.90,
        "reasoning": "Requires a professional reply.",
        "reply_body": "Hi, thanks for reaching out. I will follow up by end of week.",
        "delegation_target": None,
        "info_needed": None,
    })


def _write_email(vault_dir: Path, filename: str, message_id: str, subject: str) -> Path:
    """Write a pending email markdown file to vault/Needs_Action/."""
    path = vault_dir / "Needs_Action" / filename
    path.write_text(
        f"---\n"
        f"type: email\n"
        f"status: pending\n"
        f"source: gmail\n"
        f"message_id: {message_id}\n"
        f"from: user@example.com\n"
        f"subject: {subject}\n"
        f"date_received: 2026-02-23\n"
        f"---\n"
        f"Email body for {message_id}.\n",
        encoding="utf-8",
    )
    return path


# ---------------------------------------------------------------------------
# T031: Full triage cycle — 3 emails, 3 decisions
# ---------------------------------------------------------------------------

class TestFullTriageCycle:

    @pytest.mark.asyncio
    async def test_full_cycle_three_decisions(self, tmp_vault_dir, monkeypatch):
        """One poll cycle handles all 3 decision types correctly.

        Files are named with alphabetical prefix to ensure deterministic scan order
        (scan_pending_emails uses sorted() on glob results):
            a_archive.md   → gets archive decision (1st call)
            b_info.md      → gets needs_info decision (2nd call)
            c_reply.md     → gets draft_reply decision (3rd call)
        """
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        # Write 3 emails with names that sort in the expected processing order
        path_archive = _write_email(
            tmp_vault_dir, "a_archive.md", "msg_archive", "Weekly Newsletter #42"
        )
        path_info = _write_email(
            tmp_vault_dir, "b_info.md", "msg_info", "Product Roadmap Question"
        )
        path_reply = _write_email(
            tmp_vault_dir, "c_reply.md", "msg_reply", "Meeting Follow-up Request"
        )

        # Provider returns decisions in alphabetical file order: archive, needs_info, draft_reply
        provider = _SequentialMockProvider([
            _archive_json(),     # a_archive.md
            _needs_info_json(),  # b_info.md
            _draft_reply_json(), # c_reply.md
        ])

        orch = RalphWiggumOrchestrator(
            provider=provider,
            poll_interval=30,
            vault_path=str(tmp_vault_dir),
        )
        orch.validate_prerequisites()
        await orch._run_poll_cycle()

        # --- Verify archive decision ---
        # File must have been moved to Done/
        assert not path_archive.exists(), \
            "Archive email must be moved out of Needs_Action/"
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1, \
            f"Expected 1 file in vault/Done/, found: {[f.name for f in done_files]}"

        # --- Verify needs_info decision ---
        # File must remain in Needs_Action/ with status=needs_info
        assert path_info.exists(), "needs_info email must stay in Needs_Action/"
        info_content = path_info.read_text(encoding="utf-8")
        assert "needs_info" in info_content, \
            "needs_info file must have updated status in frontmatter"

        # --- Verify draft_reply decision ---
        # A draft file must be created in vault/Drafts/
        draft_files = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert len(draft_files) == 1, \
            f"Expected 1 draft in vault/Drafts/, found: {[f.name for f in draft_files]}"

        # --- Verify audit log ---
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{today}.log"
        assert log_file.exists(), f"Log file must exist at {log_file}"

        raw_lines = log_file.read_text(encoding="utf-8").splitlines()
        entries = [json.loads(line) for line in raw_lines if line.strip()]

        audit_entries = [e for e in entries if e.get("event") == "llm_decision_audit"]
        poll_complete = [e for e in entries if e.get("event") == "poll_cycle_complete"]

        assert len(audit_entries) == 3, \
            f"Expected 3 llm_decision_audit entries, got {len(audit_entries)}"
        assert len(poll_complete) == 1, \
            f"Expected 1 poll_cycle_complete entry, got {len(poll_complete)}"

        # --- Verify all 3 message IDs processed ---
        for msg_id in ("msg_archive", "msg_info", "msg_reply"):
            assert msg_id in orch.state.processed_ids, \
                f"{msg_id} must be in processed_ids after the poll cycle"

        # --- Verify poll_cycle_complete payload ---
        cycle_entry = poll_complete[0]
        assert cycle_entry["details"]["emails_found"] == 3, \
            "poll_cycle_complete must report 3 emails found"
        assert cycle_entry["details"]["emails_processed"] == 3, \
            "poll_cycle_complete must report 3 emails processed"
