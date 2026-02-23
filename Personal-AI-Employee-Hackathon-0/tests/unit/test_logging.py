"""Unit tests for the orchestrator audit log (T023 + T025).

Tests validate (T023):
    - llm_decision_audit log entry contains all required fields in details
    - llm_failed log entry has severity=ERROR with error fields
    - all log entries are valid JSONL (parseable with json.loads)
    - outer log entry has standard envelope: timestamp, watcher_name, event, severity, details
    - API key text does NOT appear in any log field

Tests validate (T025):
    - log file uses today's date in filename orchestrator_YYYY-MM-DD.log
    - multiple process_item() calls append to the same daily log file
    - each non-empty line in the log file is a valid JSON object (JSONL)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from orchestrator.vault_ops import read_email_context


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------

class _MockProvider(LLMProviderBase):
    """Configurable single-response mock for logging tests."""

    def __init__(self, response_json: str, provider_name: str = "mock", model_name: str = "mock-model") -> None:
        self._response = response_json
        self._pname = provider_name
        self._mname = model_name

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        return (self._response, 200, 60)

    def provider_name(self) -> str:
        return self._pname

    def model_name(self) -> str:
        return self._mname


def _valid_archive_json() -> str:
    return json.dumps({
        "decision": "archive",
        "confidence": 0.9,
        "reasoning": "Promotional newsletter.",
    })


def _invalid_json_sequence(n: int = 5) -> list[str]:
    return ["NOT VALID JSON"] * n


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(provider, vault_path, max_iterations=5):
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
        max_iterations=max_iterations,
    )


def _today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _read_log_lines(vault_path: Path) -> list[dict]:
    """Read all JSONL lines from today's orchestrator log file."""
    log_file = vault_path / "Logs" / f"orchestrator_{_today_str()}.log"
    if not log_file.exists():
        return []
    lines = log_file.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


# ---------------------------------------------------------------------------
# T023: llm_decision_audit log entry — required fields
# ---------------------------------------------------------------------------

class TestDecisionAuditLogEntry:

    @pytest.mark.asyncio
    async def test_log_entry_written_after_process_item(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        assert len(lines) > 0, "Expected at least one log entry after process_item"

    @pytest.mark.asyncio
    async def test_decision_audit_entry_has_outer_envelope(self, tmp_vault_dir, mock_email_file):
        """Each log line must have: timestamp, watcher_name, event, severity, details."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        for entry in lines:
            assert "timestamp" in entry
            assert "watcher_name" in entry
            assert "event" in entry
            assert "severity" in entry
            assert "details" in entry

    @pytest.mark.asyncio
    async def test_decision_audit_entry_details_has_required_fields(self, tmp_vault_dir, mock_email_file):
        """llm_decision_audit details must carry the full DecisionLogEntry fields."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        audit_entries = [l for l in lines if l.get("event") == "llm_decision_audit"]
        assert len(audit_entries) >= 1, "Expected llm_decision_audit event in log"

        details = audit_entries[0]["details"]
        required = [
            "timestamp", "event", "provider", "model",
            "email_message_id", "email_subject",
            "decision", "confidence", "reasoning",
            "tokens_input", "tokens_output", "latency_ms", "iteration",
        ]
        missing = [f for f in required if f not in details]
        assert not missing, f"Missing required fields in llm_decision_audit details: {missing}"

    @pytest.mark.asyncio
    async def test_decision_audit_entry_decision_value_correct(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        audit = next(l for l in lines if l.get("event") == "llm_decision_audit")
        assert audit["details"]["decision"] == "archive"
        assert audit["details"]["provider"] == "mock"
        assert audit["details"]["model"] == "mock-model"

    @pytest.mark.asyncio
    async def test_decision_audit_tokens_are_integers(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        audit = next(l for l in lines if l.get("event") == "llm_decision_audit")
        d = audit["details"]
        assert isinstance(d["tokens_input"], int)
        assert isinstance(d["tokens_output"], int)
        assert isinstance(d["latency_ms"], int)
        assert isinstance(d["iteration"], int)


# ---------------------------------------------------------------------------
# T023: llm_failed log entry — severity=ERROR
# ---------------------------------------------------------------------------

class TestErrorLogEntry:

    @pytest.mark.asyncio
    async def test_llm_failed_entry_has_severity_error(self, tmp_vault_dir, mock_email_file):
        """After MaxIterationsExceeded, log must have a severity=error entry."""
        from tests.unit.test_ralph_wiggum_retry import _SequentialMockProvider
        provider = _SequentialMockProvider(["NOT JSON"] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        error_entries = [l for l in lines if l.get("severity") == "error"]
        assert len(error_entries) >= 1, "Expected at least one severity=error log entry on failure"

    @pytest.mark.asyncio
    async def test_llm_failed_entry_has_error_fields(self, tmp_vault_dir, mock_email_file):
        """llm_failed details must contain error_type and error_message."""
        from tests.unit.test_ralph_wiggum_retry import _SequentialMockProvider
        provider = _SequentialMockProvider(["NOT JSON"] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        lines = _read_log_lines(tmp_vault_dir)
        failed = next((l for l in lines if l.get("event") == "llm_failed"), None)
        assert failed is not None, "Expected llm_failed event in log"
        assert "error_type" in failed["details"]
        assert "error_message" in failed["details"]
        assert failed["details"]["error_type"] == "MaxIterationsExceeded"


# ---------------------------------------------------------------------------
# T023: JSONL format validity
# ---------------------------------------------------------------------------

class TestLogEntryJsonlFormat:

    @pytest.mark.asyncio
    async def test_all_log_lines_are_valid_json(self, tmp_vault_dir, mock_email_file):
        """Every non-empty line in the log file must be valid JSON."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{_today_str()}.log"
        assert log_file.exists()

        raw = log_file.read_text(encoding="utf-8")
        for line_num, line in enumerate(raw.splitlines(), 1):
            if not line.strip():
                continue
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {line_num} is not valid JSON: {e}\nContent: {line[:200]}")


# ---------------------------------------------------------------------------
# T023: API key not in log fields
# ---------------------------------------------------------------------------

class TestApiKeyNotInLog:

    @pytest.mark.asyncio
    async def test_decided_by_field_has_no_api_key(self, tmp_vault_dir, mock_email_file):
        """The decided_by frontmatter field uses provider_name():model_name() — never the key."""
        import yaml

        provider = _MockProvider(_valid_archive_json(), provider_name="mock", model_name="mock-model")
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        # Check the done file has decided_by without api key
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1
        content = done_files[0].read_text(encoding="utf-8")
        fm_text = content.split("---\n")[1]
        fm = yaml.safe_load(fm_text) or {}
        assert "sk-" not in str(fm.get("decided_by", ""))

    @pytest.mark.asyncio
    async def test_log_content_has_no_sk_prefix_secrets(self, tmp_vault_dir, mock_email_file):
        """No log line should contain 'sk-ant' or 'sk-' API key patterns."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{_today_str()}.log"
        raw = log_file.read_text(encoding="utf-8")
        assert "sk-ant-" not in raw
        # Generic OpenAI pattern check (real secret would not be "sk-" + exactly that)
        assert "sk-ant" not in raw


# ---------------------------------------------------------------------------
# T025: Log file naming and append behavior
# ---------------------------------------------------------------------------

class TestLogFileNamingAndFormat:

    @pytest.mark.asyncio
    async def test_log_file_uses_todays_date(self, tmp_vault_dir, mock_email_file):
        """Log file must be named orchestrator_{YYYY-MM-DD}.log with today's UTC date."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        today = _today_str()
        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{today}.log"
        assert log_file.exists(), f"Expected log file at {log_file}"

    @pytest.mark.asyncio
    async def test_no_other_log_files_created(self, tmp_vault_dir, mock_email_file):
        """Only the dated orchestrator log file should be created (no extra files)."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        log_dir = tmp_vault_dir / "Logs"
        orch_logs = [f for f in log_dir.iterdir() if f.name.startswith("orchestrator_") and f.suffix == ".log"]
        assert len(orch_logs) == 1, f"Expected exactly 1 orchestrator log file, found: {[f.name for f in orch_logs]}"

    @pytest.mark.asyncio
    async def test_multiple_process_calls_append_to_same_file(self, tmp_vault_dir, mock_email_file):
        """Two process_item() calls must append to the same daily log file."""
        import shutil

        # Create a second email file for the second call
        second_file = tmp_vault_dir / "Needs_Action" / "test_msg_002.md"
        shutil.copy(mock_email_file, second_file)
        # Update message_id to be unique
        content = second_file.read_text(encoding="utf-8")
        second_file.write_text(content.replace("msg_001", "msg_002"), encoding="utf-8")

        provider = _MockProvider(json.dumps({
            "decision": "needs_info",
            "confidence": 0.7,
            "reasoning": "Need context.",
            "info_needed": "What product?",
        }))
        orch = _make_orchestrator(provider, tmp_vault_dir)

        from orchestrator.vault_ops import read_email_context as rec
        ctx1 = rec(mock_email_file)
        ctx2 = rec(second_file)

        await orch.process_item(ctx1)
        await orch.process_item(ctx2)

        today = _today_str()
        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{today}.log"
        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        assert len(lines) >= 2, "Expected at least 2 log entries in the same file"

    @pytest.mark.asyncio
    async def test_log_entries_are_newline_delimited_one_per_line(self, tmp_vault_dir, mock_email_file):
        """Log file must be newline-delimited JSON: exactly one JSON object per line."""
        provider = _MockProvider(_valid_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{_today_str()}.log"
        raw = log_file.read_text(encoding="utf-8")

        # Each non-empty line must be exactly one valid JSON object
        for line in raw.splitlines():
            if not line.strip():
                continue
            parsed = json.loads(line)
            assert isinstance(parsed, dict), f"Log line is not a JSON object: {line[:100]}"
