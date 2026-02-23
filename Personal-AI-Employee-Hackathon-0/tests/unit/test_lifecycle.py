"""Unit tests for RalphWiggumOrchestrator lifecycle (T027 + T030).

Tests validate:
    T027 — validate_prerequisites() fast-fail scenarios (LLM_PROVIDER, vault dirs)
    T027 — File lock at vault/Logs/.orchestrator.lock acquired/released correctly
    T027 — Second instance raises RuntimeError (concurrent lock prevention)
    T027 — State loaded on startup, saved on stop
    T027 — start() sets _running=True; stop() clears it + saves state
    T030 — Orchestrator and GmailWatcher use SEPARATE lock files
    T030 — No circular imports between watchers/ and orchestrator/
    T030 — vault file written to Needs_Action/ is discoverable by scan_pending_emails()
"""

import asyncio
import json
from pathlib import Path

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from watchers.utils import PrerequisiteError


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------

class _MockProvider(LLMProviderBase):
    def __init__(self, response_json: str = "") -> None:
        if not response_json:
            response_json = json.dumps({
                "decision": "archive",
                "confidence": 0.9,
                "reasoning": "Test",
            })
        self._response = response_json

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        return (self._response, 50, 25)

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


# ---------------------------------------------------------------------------
# T027: validate_prerequisites() fast-fail scenarios
# ---------------------------------------------------------------------------

class TestLifecyclePrerequisites:

    def test_validate_fails_if_llm_provider_not_set(self, tmp_vault_dir, monkeypatch):
        """validate_prerequisites() must raise PrerequisiteError when LLM_PROVIDER is unset."""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        with pytest.raises(PrerequisiteError, match="LLM_PROVIDER"):
            orch.validate_prerequisites()

    def test_validate_fails_if_needs_action_missing(self, tmp_vault_dir, monkeypatch):
        """validate_prerequisites() must raise PrerequisiteError when Needs_Action/ absent."""
        import shutil
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        shutil.rmtree(tmp_vault_dir / "Needs_Action")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        with pytest.raises(PrerequisiteError, match="Needs_Action"):
            orch.validate_prerequisites()

    def test_validate_fails_if_done_missing(self, tmp_vault_dir, monkeypatch):
        """validate_prerequisites() must raise PrerequisiteError when Done/ absent."""
        import shutil
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        shutil.rmtree(tmp_vault_dir / "Done")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        with pytest.raises(PrerequisiteError, match="Done"):
            orch.validate_prerequisites()

    def test_validate_creates_drafts_if_absent(self, tmp_vault_dir, monkeypatch):
        """validate_prerequisites() must auto-create vault/Drafts/ if it doesn't exist."""
        import shutil
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        shutil.rmtree(tmp_vault_dir / "Drafts")
        assert not (tmp_vault_dir / "Drafts").exists()
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch.validate_prerequisites()
        assert (tmp_vault_dir / "Drafts").exists()

    def test_validate_ok_with_all_dirs_and_provider_set(self, tmp_vault_dir, monkeypatch):
        """validate_prerequisites() must succeed when all vault dirs exist and LLM_PROVIDER is set."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch.validate_prerequisites()  # Must not raise


# ---------------------------------------------------------------------------
# T027: File lock at vault/Logs/.orchestrator.lock
# ---------------------------------------------------------------------------

class TestLifecycleLock:

    def test_lock_path_is_vault_logs_orchestrator_lock(self, tmp_vault_dir):
        """Lock file must reside at vault/Logs/.orchestrator.lock (BaseWatcher pattern)."""
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        expected = tmp_vault_dir / "Logs" / ".orchestrator.lock"
        assert orch._lock_path == expected

    def test_acquire_lock_creates_lock_file(self, tmp_vault_dir):
        """_acquire_lock() must create the lock file."""
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch._acquire_lock()
        try:
            assert orch._lock_path.exists(), "Lock file must exist after _acquire_lock()"
        finally:
            orch._release_lock()

    def test_second_instance_raises_runtime_error(self, tmp_vault_dir):
        """A second orchestrator instance must not acquire the lock while first holds it."""
        orch1 = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch2 = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch1._acquire_lock()
        try:
            with pytest.raises(RuntimeError):
                orch2._acquire_lock()
        finally:
            orch1._release_lock()

    def test_release_lock_removes_lock_file(self, tmp_vault_dir):
        """_release_lock() must remove the lock file and clear _lock attribute."""
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch._acquire_lock()
        assert orch._lock_path.exists()
        orch._release_lock()
        assert not orch._lock_path.exists()
        assert orch._lock is None


# ---------------------------------------------------------------------------
# T027: State load on startup, save on stop
# ---------------------------------------------------------------------------

class TestLifecycleStatePersistence:

    def test_load_state_restores_processed_ids(self, tmp_vault_dir):
        """_load_state() must restore processed_ids written by a previous run."""
        state_file = tmp_vault_dir / "Logs" / "orchestrator_state.json"
        state_file.write_text(json.dumps({
            "last_poll_timestamp": "",
            "processed_ids": ["pre_existing_msg_001", "pre_existing_msg_002"],
            "error_count": 0,
            "total_emails_processed": 2,
            "uptime_start": "",
        }), encoding="utf-8")

        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch._load_state()

        assert "pre_existing_msg_001" in orch.state.processed_ids
        assert "pre_existing_msg_002" in orch.state.processed_ids

    def test_save_state_writes_state_file(self, tmp_vault_dir):
        """_save_state() must write vault/Logs/orchestrator_state.json with processed_ids."""
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        orch.state.processed_ids.append("test_msg_save")
        orch._save_state()

        state_path = tmp_vault_dir / "Logs" / "orchestrator_state.json"
        assert state_path.exists(), "State file must be created by _save_state()"
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
        assert "processed_ids" in loaded
        assert "test_msg_save" in loaded["processed_ids"]


# ---------------------------------------------------------------------------
# T027: Full async start/stop
# ---------------------------------------------------------------------------

class TestLifecycleAsyncStartStop:

    @pytest.mark.asyncio
    async def test_start_sets_running_true_and_acquires_lock(self, tmp_vault_dir, monkeypatch):
        """start() must set _running=True and acquire lock before polling."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)

        task = asyncio.create_task(orch.start())
        await asyncio.sleep(0.1)  # Let start() complete sync setup + first poll cycle

        try:
            assert orch._running is True, "_running must be True after start()"
            assert orch._lock_path.exists(), "Lock file must exist after start()"
        finally:
            await orch.stop()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_stop_saves_state_and_releases_lock(self, tmp_vault_dir, monkeypatch):
        """stop() must set _running=False, save state file, and release lock."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)

        task = asyncio.create_task(orch.start())
        await asyncio.sleep(0.1)

        await orch.stop()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

        assert orch._running is False, "_running must be False after stop()"
        assert orch._lock is None, "Lock must be released after stop()"
        assert (tmp_vault_dir / "Logs" / "orchestrator_state.json").exists(), \
            "State file must be written by stop()"


# ---------------------------------------------------------------------------
# T030: GmailWatcher + Orchestrator co-existence
# ---------------------------------------------------------------------------

class TestWatcherCoExistence:

    def test_orchestrator_lock_path_differs_from_gmail_watcher_pattern(self, tmp_vault_dir):
        """Orchestrator lock file name must not conflict with GmailWatcher lock name.

        BaseWatcher uses .{name}.lock, so:
            orchestrator → vault/Logs/.orchestrator.lock
            gmail_watcher → vault/Logs/.gmail_watcher.lock
        """
        orch = _make_orchestrator(_MockProvider(), tmp_vault_dir)
        assert orch._lock_path.name == ".orchestrator.lock"
        # GmailWatcher lock would be .gmail_watcher.lock — different file
        assert orch._lock_path.name != ".gmail_watcher.lock"

    def test_no_circular_imports_between_watchers_and_orchestrator(self):
        """Importing orchestrator and watchers together must not cause circular import errors."""
        import importlib
        # These must both import cleanly (no ImportError from circular dependency)
        importlib.import_module("orchestrator.orchestrator")
        importlib.import_module("watchers.base_watcher")
        importlib.import_module("watchers.gmail_watcher")

    def test_vault_file_readable_by_scan_pending_emails(self, tmp_vault_dir):
        """A vault .md file with status: pending is discoverable by scan_pending_emails().

        Simulates the file format GmailWatcher writes to vault/Needs_Action/.
        """
        from orchestrator.vault_ops import scan_pending_emails

        email_file = tmp_vault_dir / "Needs_Action" / "watcher_produced_email.md"
        email_file.write_text(
            "---\n"
            "type: email\n"
            "status: pending\n"
            "source: gmail\n"
            "message_id: coex_msg_001\n"
            "from: sender@example.com\n"
            "subject: Co-existence Test\n"
            "date_received: 2026-02-23\n"
            "---\n"
            "Email body for co-existence test.\n",
            encoding="utf-8",
        )

        found = scan_pending_emails(tmp_vault_dir / "Needs_Action")
        assert len(found) == 1
        assert found[0] == email_file
