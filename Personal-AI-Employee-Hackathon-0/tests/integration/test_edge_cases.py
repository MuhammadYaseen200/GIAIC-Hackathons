"""Integration edge-case tests for RalphWiggumOrchestrator (T032).

Tests validate:
    - Ralph Wiggum retry exhaustion: all iterations return invalid JSON → status=failed + log
    - API/network error on every call → MaxIterationsExceeded → status=failed
    - API error on first call → retry → success on second call
    - Corrupt YAML frontmatter (missing message_id) → read_error log + email skipped
    - Already-processed message_id → skipped silently in poll()
    - Email body >token budget → truncated with [EMAIL TRUNCATED] notice in prompt
    - Financial email with archive decision → processed (financial safety is prompt-only, no post-hoc filter)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from unittest.mock import AsyncMock, patch

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from orchestrator.vault_ops import read_email_context


# ---------------------------------------------------------------------------
# Mock providers
# ---------------------------------------------------------------------------

class _SequentialMockProvider(LLMProviderBase):
    """Returns responses in the given order; repeats last response if exhausted."""

    def __init__(self, responses: list) -> None:
        self._responses = responses
        self._call_count = 0
        self._calls: list[tuple[str, str]] = []  # (system_prompt, user_message) per call

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        self._calls.append((system_prompt, user_message))
        response = self._responses[min(self._call_count, len(self._responses) - 1)]
        self._call_count += 1
        if isinstance(response, Exception):
            raise response
        return (response, 100, 50)

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


def _make_orchestrator(provider, vault_path, max_iterations=5):
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
        max_iterations=max_iterations,
    )


def _write_email(
    vault_dir: Path,
    filename: str,
    message_id: str,
    subject: str = "Test",
    body: str = "Test body.",
) -> Path:
    path = vault_dir / "Needs_Action" / filename
    path.write_text(
        f"---\n"
        f"type: email\n"
        f"status: pending\n"
        f"source: gmail\n"
        f"message_id: {message_id}\n"
        f"from: sender@example.com\n"
        f"subject: {subject}\n"
        f"date_received: 2026-02-23\n"
        f"---\n"
        f"{body}\n",
        encoding="utf-8",
    )
    return path


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_log_lines(vault_dir: Path) -> list[dict]:
    log_file = vault_dir / "Logs" / f"orchestrator_{_today_str()}.log"
    if not log_file.exists():
        return []
    return [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# T032: Retry exhaustion (5 invalid JSON → status=failed)
# ---------------------------------------------------------------------------

class TestRetryExhaustion:

    @pytest.mark.asyncio
    async def test_five_invalid_responses_set_status_failed(self, tmp_vault_dir, monkeypatch):
        """5 invalid JSON responses → status=failed in frontmatter."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "retry_msg_001")

        provider = _SequentialMockProvider(["NOT VALID JSON"] * 5)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=5)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        content = email_path.read_text(encoding="utf-8")
        assert "status: failed" in content, "Email must be marked failed after exhausting retries"

    @pytest.mark.asyncio
    async def test_five_invalid_responses_write_llm_failed_log(self, tmp_vault_dir, monkeypatch):
        """5 invalid JSON responses → llm_failed event logged with severity=error."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "retry_msg_002")

        provider = _SequentialMockProvider(["NOT VALID JSON"] * 5)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=5)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        failed = [l for l in lines if l.get("event") == "llm_failed"]
        assert len(failed) >= 1, "Expected llm_failed log entry after retry exhaustion"
        assert failed[0].get("severity") == "error"

    @pytest.mark.asyncio
    async def test_retry_exhaustion_increments_error_count(self, tmp_vault_dir, monkeypatch):
        """MaxIterationsExceeded must increment error_counts['MaxIterationsExceeded']."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "retry_msg_003")

        provider = _SequentialMockProvider(["NOT JSON"] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        assert orch._orch_state.error_counts.get("MaxIterationsExceeded", 0) == 1


# ---------------------------------------------------------------------------
# T032: API / network error handling
# ---------------------------------------------------------------------------

class TestApiErrorHandling:

    @pytest.mark.asyncio
    async def test_api_error_all_iterations_sets_status_failed(self, tmp_vault_dir, monkeypatch):
        """Provider raising RuntimeError on every call → MaxIterationsExceeded → status=failed."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "api_err_msg_001")

        # Use 3 exceptions
        responses = [RuntimeError("Connection refused")] * 3
        provider = _SequentialMockProvider(responses)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        content = email_path.read_text(encoding="utf-8")
        assert "status: failed" in content

    @pytest.mark.asyncio
    async def test_api_error_first_call_success_on_second(self, tmp_vault_dir, monkeypatch):
        """Provider raises on 1st call, returns valid JSON on 2nd → email processed."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "api_err_msg_002")

        valid_json = json.dumps({
            "decision": "archive",
            "confidence": 0.9,
            "reasoning": "Test recovery.",
        })
        responses = [RuntimeError("Simulated 429 rate limit"), valid_json]
        provider = _SequentialMockProvider(responses)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        assert provider._call_count == 2, "Provider must be called twice (1 error + 1 success)"
        assert "api_err_msg_002" in orch.state.processed_ids, \
            "Email must be in processed_ids after successful retry"

    @pytest.mark.asyncio
    async def test_api_error_logged_as_warn(self, tmp_vault_dir, monkeypatch):
        """API error in _call_llm_with_retry must produce llm_api_error warn log."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(tmp_vault_dir, "email.md", "api_err_msg_003")

        valid_json = json.dumps({"decision": "archive", "confidence": 0.8, "reasoning": "Test"})
        responses = [ConnectionError("Network timeout"), valid_json]
        provider = _SequentialMockProvider(responses)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        warn_entries = [l for l in lines if l.get("event") == "llm_api_error"]
        assert len(warn_entries) >= 1, "API error must generate llm_api_error log entry"


# ---------------------------------------------------------------------------
# T032: Corrupt frontmatter / missing required field
# ---------------------------------------------------------------------------

class TestCorruptFrontmatter:

    @pytest.mark.asyncio
    async def test_missing_message_id_logs_read_error_and_skips(self, tmp_vault_dir, monkeypatch):
        """A file with status:pending but no message_id → read_error log + not in processed_ids."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        # File passes scan_pending_emails (has status: pending) but fails read_email_context
        bad_file = tmp_vault_dir / "Needs_Action" / "bad_email.md"
        bad_file.write_text(
            "---\n"
            "type: email\n"
            "status: pending\n"
            "from: sender@example.com\n"
            "subject: Missing ID\n"
            "date_received: 2026-02-23\n"
            "---\n"
            "No message_id in this file.\n",
            encoding="utf-8",
        )

        provider = _SequentialMockProvider([
            json.dumps({"decision": "archive", "confidence": 0.9, "reasoning": "Test"}),
        ])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        await orch._run_poll_cycle()

        # Corrupt file must not appear in processed_ids (no message_id to track)
        assert len(orch.state.processed_ids) == 0, \
            "Corrupt email (missing message_id) must not be added to processed_ids"

        # read_error must be logged
        lines = _read_log_lines(tmp_vault_dir)
        errors = [l for l in lines if l.get("event") == "read_error"]
        assert len(errors) >= 1, "read_error must be logged for corrupt frontmatter"

    @pytest.mark.asyncio
    async def test_corrupt_file_skipped_valid_file_processed(self, tmp_vault_dir, monkeypatch):
        """One corrupt + one valid file: valid email processed, corrupt skipped."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        # Corrupt file (no message_id)
        bad_file = tmp_vault_dir / "Needs_Action" / "a_bad.md"
        bad_file.write_text(
            "---\ntype: email\nstatus: pending\nsubject: No ID\nfrom: x@x.com\n---\nBody.\n",
            encoding="utf-8",
        )
        # Valid file
        _write_email(tmp_vault_dir, "b_good.md", "good_msg_001")

        provider = _SequentialMockProvider([
            json.dumps({"decision": "archive", "confidence": 0.9, "reasoning": "Test"}),
        ])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        await orch._run_poll_cycle()

        assert "good_msg_001" in orch.state.processed_ids, \
            "Valid email must be processed despite preceding corrupt file"


# ---------------------------------------------------------------------------
# T032: Body > token budget → truncation
# ---------------------------------------------------------------------------

class TestBodyTruncation:

    @pytest.mark.asyncio
    async def test_large_body_triggers_truncation_notice_in_prompt(self, tmp_vault_dir, monkeypatch):
        """Email body exceeding token budget must be truncated with [EMAIL TRUNCATED] notice."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        # Create a body that is clearly over 4000 tokens (16000+ chars)
        huge_body = "This is a very long paragraph. " * 600  # ~18000 chars ≈ 4500 tokens

        email_path = _write_email(
            tmp_vault_dir, "email.md", "trunc_msg_001",
            subject="Long Email", body=huge_body,
        )

        received_messages: list[str] = []

        class _CapturingProvider(LLMProviderBase):
            async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
                received_messages.append(user_message)
                return (
                    json.dumps({"decision": "archive", "confidence": 0.9, "reasoning": "Done"}),
                    100, 50,
                )
            def provider_name(self): return "mock"
            def model_name(self): return "mock-model"

        orch = _make_orchestrator(_CapturingProvider(), tmp_vault_dir)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        assert len(received_messages) >= 1, "Provider must have been called at least once"
        user_msg = received_messages[0]
        assert "EMAIL TRUNCATED" in user_msg, \
            "User message must contain [EMAIL TRUNCATED] notice when body exceeds budget"

    @pytest.mark.asyncio
    async def test_small_body_not_truncated(self, tmp_vault_dir, monkeypatch):
        """Small email body must not trigger truncation."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        small_body = "Hi, quick question about your service."
        email_path = _write_email(
            tmp_vault_dir, "email.md", "trunc_msg_002",
            subject="Short Email", body=small_body,
        )

        received_messages: list[str] = []

        class _CapturingProvider(LLMProviderBase):
            async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
                received_messages.append(user_message)
                return (
                    json.dumps({"decision": "needs_info", "confidence": 0.7,
                                "reasoning": "Test", "info_needed": "What service?"}),
                    50, 25,
                )
            def provider_name(self): return "mock"
            def model_name(self): return "mock-model"

        orch = _make_orchestrator(_CapturingProvider(), tmp_vault_dir)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        user_msg = received_messages[0]
        assert "EMAIL TRUNCATED" not in user_msg, "Short body must not trigger truncation"
        assert small_body in user_msg, "Full body must appear verbatim in user message"


# ---------------------------------------------------------------------------
# T032: Financial email + archive response → processed (no post-hoc filter)
# ---------------------------------------------------------------------------

class TestFinancialEmailProcessing:

    @pytest.mark.asyncio
    async def test_financial_email_with_archive_response_is_processed(
        self, tmp_vault_dir, monkeypatch
    ):
        """Financial email where LLM returns archive → orchestrator processes without blocking.

        Financial safety is a PROMPT constraint (in system prompt), not a post-hoc filter.
        If the LLM ignores the constraint and returns archive anyway, the orchestrator
        still processes the email as archive — it does not override the LLM's decision.
        """
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        email_path = _write_email(
            tmp_vault_dir, "invoice.md", "fin_msg_001",
            subject="Invoice #1234 — Payment Required",
            body="Please remit payment of $500 for invoice #1234.",
        )

        archive_json = json.dumps({
            "decision": "archive",
            "confidence": 0.5,
            "reasoning": "Archived despite financial content (mock ignores safety rule).",
        })
        provider = _SequentialMockProvider([archive_json])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(email_path)
        await orch.process_item(ctx)

        # Email should be processed (moved to Done/) — no post-hoc override
        assert "fin_msg_001" in orch.state.processed_ids
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1, \
            "Archive decision on financial email must be honoured (safety is prompt-only)"

    def test_system_prompt_contains_financial_safety_rule(self):
        """Build system prompt must embed the financial safety constraint."""
        from orchestrator.prompts import build_system_prompt
        prompt = build_system_prompt()
        assert "payment" in prompt.lower() or "invoice" in prompt.lower() or \
               "billing" in prompt.lower(), \
            "System prompt must contain financial safety keywords"
        assert "never" in prompt.lower() or "must not" in prompt.lower() or \
               "never be classified" in prompt.lower(), \
            "System prompt must state financial emails must never be archived"


# ---------------------------------------------------------------------------
# T032: Already-processed IDs skipped in poll()
# ---------------------------------------------------------------------------

class TestAlreadyProcessedSkipped:

    @pytest.mark.asyncio
    async def test_poll_skips_already_processed_message_id(self, tmp_vault_dir, monkeypatch):
        """poll() must return empty list when the only pending email was already processed."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")

        _write_email(tmp_vault_dir, "email.md", "skip_msg_001")

        orch = _make_orchestrator(_SequentialMockProvider([]), tmp_vault_dir)
        # Manually mark as already processed
        orch.state.processed_ids.append("skip_msg_001")

        result = await orch.poll()
        assert result == [], \
            "poll() must skip emails whose message_id is already in processed_ids"
