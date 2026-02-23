"""Integration tests for orchestrator lifecycle (T028).

Tests validate:
    - start orchestrator with tmp vault + mocked LLM, place 2 emails, run one poll cycle,
      verify both processed + state saved
    - restart orchestrator (load saved state), place 1 new email, verify only new email
      processed (processed_ids loaded from prior run)
    - concurrent instance prevention (acquire lock, attempt second start)
    - watcher independence (orchestrator runs without GmailWatcher present)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------

class _MockProvider(LLMProviderBase):
    """Configurable mock — always returns the same archive JSON."""

    def __init__(self) -> None:
        self._call_count = 0

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        self._call_count += 1
        return (
            json.dumps({
                "decision": "archive",
                "confidence": 0.9,
                "reasoning": "Automated test mock.",
            }),
            50,
            25,
        )

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


def _make_orchestrator(provider, vault_path):
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
    )


def _write_email(vault_dir: Path, filename: str, message_id: str) -> Path:
    """Write a pending email to vault/Needs_Action/."""
    email_path = vault_dir / "Needs_Action" / filename
    email_path.write_text(
        f"---\n"
        f"type: email\n"
        f"status: pending\n"
        f"source: gmail\n"
        f"message_id: {message_id}\n"
        f"from: sender@example.com\n"
        f"subject: Test Email {message_id}\n"
        f"date_received: 2026-02-23\n"
        f"---\n"
        f"Integration test email body for {message_id}.\n",
        encoding="utf-8",
    )
    return email_path


# ---------------------------------------------------------------------------
# T028: Integration lifecycle tests
# ---------------------------------------------------------------------------

class TestLifecycleIntegration:

    @pytest.mark.asyncio
    async def test_two_emails_processed_in_one_cycle(self, tmp_vault_dir, monkeypatch):
        """One poll cycle must process both pending emails and persist state."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        _write_email(tmp_vault_dir, "email_001.md", "integ_msg_001")
        _write_email(tmp_vault_dir, "email_002.md", "integ_msg_002")

        provider = _MockProvider()
        orch = _make_orchestrator(provider, tmp_vault_dir)
        orch.validate_prerequisites()
        await orch._run_poll_cycle()

        assert "integ_msg_001" in orch.state.processed_ids, \
            "integ_msg_001 must appear in processed_ids after poll cycle"
        assert "integ_msg_002" in orch.state.processed_ids, \
            "integ_msg_002 must appear in processed_ids after poll cycle"
        assert provider._call_count == 2, "LLM must be called once per email"

        state_path = tmp_vault_dir / "Logs" / "orchestrator_state.json"
        assert state_path.exists(), "State file must be written after poll cycle"

    @pytest.mark.asyncio
    async def test_restart_skips_previously_processed_emails(self, tmp_vault_dir, monkeypatch):
        """After restart, processed_ids from prior run prevent re-processing old emails."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        _write_email(tmp_vault_dir, "email_001.md", "restart_msg_001")

        provider = _MockProvider()

        # First run: process email_001
        orch1 = _make_orchestrator(provider, tmp_vault_dir)
        orch1.validate_prerequisites()
        await orch1._run_poll_cycle()
        orch1._save_state()

        assert "restart_msg_001" in orch1.state.processed_ids
        calls_after_first_run = provider._call_count  # Should be 1

        # Simulate restart: new orchestrator, loads saved state
        _write_email(tmp_vault_dir, "email_002.md", "restart_msg_002")
        orch2 = _make_orchestrator(provider, tmp_vault_dir)
        orch2._load_state()

        # Loaded state must contain the previously processed ID
        assert "restart_msg_001" in orch2.state.processed_ids, \
            "Restarted orchestrator must restore processed_ids from prior run"

        await orch2._run_poll_cycle()

        # Only the new email (email_002) should have been processed
        assert "restart_msg_002" in orch2.state.processed_ids
        assert provider._call_count == calls_after_first_run + 1, \
            "LLM called only once more (for the new email), not for the already-processed one"

    def test_concurrent_instance_prevention(self, tmp_vault_dir):
        """The first lock holder must block the second instance from acquiring the lock."""
        orch1 = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch2 = _make_orchestrator(_MockProvider(), tmp_vault_dir)

        orch1._acquire_lock()
        try:
            with pytest.raises(RuntimeError):
                orch2._acquire_lock()
        finally:
            orch1._release_lock()

    @pytest.mark.asyncio
    async def test_watcher_independence_no_gmail_needed(self, tmp_vault_dir, monkeypatch):
        """Orchestrator must complete a poll cycle without GmailWatcher being present."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch.validate_prerequisites()

        # Empty vault — no emails. Should complete without error.
        await orch._run_poll_cycle()

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = tmp_vault_dir / "Logs" / f"orchestrator_{today}.log"
        assert log_file.exists(), "Log file must exist after poll cycle"

        lines = [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]
        events = [entry["event"] for entry in lines]
        assert "poll_cycle_complete" in events, \
            "Log must contain poll_cycle_complete event even with empty vault"
