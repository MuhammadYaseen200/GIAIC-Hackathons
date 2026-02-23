"""Unit tests for OrchestratorState persistence (T024).

Tests validate:
    - OrchestratorState serializes to valid JSON (to_json)
    - OrchestratorState deserializes from JSON (from_json)
    - processed_ids round-trip through WatcherState save/load (BaseWatcher._save_state)
    - decision_counts incremented per record_decision() call
    - error_counts incremented per record_error() call
    - extended state file written to correct path vault/Logs/orchestrator_extended_state.json
    - corrupt state file handled gracefully (reset to empty state)
    - OrchestratorState loaded on orchestrator restart via _load_orch_state()
"""

import json
from pathlib import Path

import pytest

from orchestrator.models import OrchestratorState
from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from orchestrator.vault_ops import read_email_context


# ---------------------------------------------------------------------------
# Mock Provider
# ---------------------------------------------------------------------------

class _MockProvider(LLMProviderBase):
    def __init__(self, response_json: str) -> None:
        self._response = response_json

    async def complete(self, system_prompt, user_message, temperature=0.3, max_tokens=1024):
        return (self._response, 100, 50)

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


def _archive_json() -> str:
    return json.dumps({
        "decision": "archive",
        "confidence": 0.9,
        "reasoning": "Newsletter.",
    })


def _needs_info_json() -> str:
    return json.dumps({
        "decision": "needs_info",
        "confidence": 0.7,
        "reasoning": "Need context.",
        "info_needed": "Which product line?",
    })


def _make_orchestrator(provider, vault_path, max_iterations=5):
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
        max_iterations=max_iterations,
    )


# ---------------------------------------------------------------------------
# T024: OrchestratorState model serialization
# ---------------------------------------------------------------------------

class TestOrchestratorStateSerialization:

    def test_to_json_returns_valid_json(self):
        state = OrchestratorState()
        raw = state.to_json()
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)

    def test_to_json_contains_all_fields(self):
        state = OrchestratorState()
        parsed = json.loads(state.to_json())
        assert "processed_ids" in parsed
        assert "error_counts" in parsed
        assert "decision_counts" in parsed
        assert "total_tokens_used" in parsed
        assert "total_emails_processed" in parsed

    def test_from_json_round_trip(self):
        state = OrchestratorState(
            processed_ids=["msg_001", "msg_002"],
            decision_counts={"archive": 2, "draft_reply": 1},
            error_counts={"MaxIterationsExceeded": 1},
            total_tokens_used=500,
            total_emails_processed=3,
        )
        raw = state.to_json()
        restored = OrchestratorState.from_json(raw)

        assert restored.processed_ids == ["msg_001", "msg_002"]
        assert restored.decision_counts == {"archive": 2, "draft_reply": 1}
        assert restored.error_counts == {"MaxIterationsExceeded": 1}
        assert restored.total_tokens_used == 500
        assert restored.total_emails_processed == 3

    def test_from_json_corrupt_returns_empty_state(self):
        """Corrupt/invalid JSON must reset to empty OrchestratorState (not raise)."""
        state = OrchestratorState.from_json("INVALID JSON !@#$")
        assert state.processed_ids == []
        assert state.decision_counts == {}
        assert state.total_tokens_used == 0

    def test_from_json_empty_string_returns_empty_state(self):
        state = OrchestratorState.from_json("")
        assert isinstance(state, OrchestratorState)
        assert state.decision_counts == {}

    def test_from_json_wrong_schema_returns_empty_state(self):
        """JSON that doesn't match OrchestratorState schema → empty state, no exception."""
        raw = json.dumps({"unknown_field": "bad_value", "another": 999})
        state = OrchestratorState.from_json(raw)
        # Should return a valid (possibly empty) OrchestratorState, not raise
        assert isinstance(state, OrchestratorState)


# ---------------------------------------------------------------------------
# T024: Decision and error counters
# ---------------------------------------------------------------------------

class TestStateCounters:

    def test_record_decision_increments_count(self):
        state = OrchestratorState()
        state.record_decision("archive")
        state.record_decision("archive")
        state.record_decision("draft_reply")
        assert state.decision_counts["archive"] == 2
        assert state.decision_counts["draft_reply"] == 1

    def test_record_error_increments_count(self):
        state = OrchestratorState()
        state.record_error("MaxIterationsExceeded")
        state.record_error("MaxIterationsExceeded")
        assert state.error_counts["MaxIterationsExceeded"] == 2

    def test_record_decision_initializes_from_zero(self):
        state = OrchestratorState()
        state.record_decision("urgent")
        assert state.decision_counts.get("urgent") == 1


# ---------------------------------------------------------------------------
# T024: prune_processed_ids
# ---------------------------------------------------------------------------

class TestPruneProcessedIds:

    def test_prune_keeps_newest_ids(self):
        state = OrchestratorState()
        state.processed_ids = [f"msg_{i:04d}" for i in range(200)]
        state.prune_processed_ids(max_ids=100)
        assert len(state.processed_ids) == 100
        assert state.processed_ids[0] == "msg_0100"  # FIFO — oldest pruned

    def test_prune_no_op_when_under_limit(self):
        state = OrchestratorState()
        state.processed_ids = ["msg_001", "msg_002"]
        state.prune_processed_ids(max_ids=100)
        assert len(state.processed_ids) == 2


# ---------------------------------------------------------------------------
# T024: Extended state file written to correct path
# ---------------------------------------------------------------------------

class TestExtendedStateFileLocation:

    @pytest.mark.asyncio
    async def test_extended_state_file_written_to_correct_path(self, tmp_vault_dir, mock_email_file):
        """After process_item(), extended state must exist at vault/Logs/orchestrator_extended_state.json."""
        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        expected_path = tmp_vault_dir / "Logs" / "orchestrator_extended_state.json"
        assert expected_path.exists(), f"Extended state file not found at {expected_path}"

    @pytest.mark.asyncio
    async def test_extended_state_file_is_valid_json(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        state_path = tmp_vault_dir / "Logs" / "orchestrator_extended_state.json"
        raw = state_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert "decision_counts" in parsed
        assert "total_emails_processed" in parsed

    @pytest.mark.asyncio
    async def test_decision_count_incremented_in_saved_state(self, tmp_vault_dir, mock_email_file):
        """After processing an archive email, decision_counts.archive must be 1 in saved state."""
        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        state_path = tmp_vault_dir / "Logs" / "orchestrator_extended_state.json"
        saved = json.loads(state_path.read_text(encoding="utf-8"))
        assert saved["decision_counts"].get("archive", 0) == 1


# ---------------------------------------------------------------------------
# T024: State loaded on orchestrator restart (_load_orch_state)
# ---------------------------------------------------------------------------

class TestExtendedStateLoadOnRestart:

    @pytest.mark.asyncio
    async def test_decision_counts_survive_orchestrator_restart(self, tmp_vault_dir, mock_email_file):
        """State from first run must be available after creating a new orchestrator instance."""
        import shutil

        # First orchestrator: process one email
        provider = _MockProvider(_needs_info_json())
        orch1 = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)
        await orch1.process_item(ctx)

        # Verify state was saved
        assert orch1._orch_state.decision_counts.get("needs_info", 0) == 1

        # Second orchestrator: load state from file
        orch2 = _make_orchestrator(provider, tmp_vault_dir)
        orch2._load_orch_state()

        assert orch2._orch_state.decision_counts.get("needs_info", 0) == 1

    @pytest.mark.asyncio
    async def test_corrupt_extended_state_file_resets_to_empty(self, tmp_vault_dir, mock_email_file):
        """A corrupt extended state file must not crash — reset to empty state instead."""
        from watchers.utils import atomic_write

        # Write corrupt state file
        state_path = tmp_vault_dir / "Logs" / "orchestrator_extended_state.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(state_path, "THIS IS NOT JSON {{{")

        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        orch._load_orch_state()  # should not raise

        assert orch._orch_state.decision_counts == {}
        assert orch._orch_state.total_tokens_used == 0


# ---------------------------------------------------------------------------
# T024: WatcherState processed_ids persisted via BaseWatcher._save_state
# ---------------------------------------------------------------------------

class TestWatcherStateProcessedIdsPersistence:

    @pytest.mark.asyncio
    async def test_processed_ids_in_watcher_state_after_process_item(self, tmp_vault_dir, mock_email_file):
        """message_id must be in orch.state.processed_ids (WatcherState) after processing."""
        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert ctx.message_id in orch.state.processed_ids

    @pytest.mark.asyncio
    async def test_watcher_state_file_written_to_logs_dir(self, tmp_vault_dir, mock_email_file):
        """BaseWatcher._save_state writes orchestrator_state.json to vault/Logs/."""
        provider = _MockProvider(_archive_json())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        # _save_state is called by _run_poll_cycle but not process_item directly.
        # Call it manually to verify the path.
        orch._save_state()

        state_path = tmp_vault_dir / "Logs" / "orchestrator_state.json"
        assert state_path.exists(), f"WatcherState file not found at {state_path}"
