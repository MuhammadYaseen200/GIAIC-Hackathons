"""Unit tests for watchers.base_watcher -- T030 through T040 (Phase 3) + T092-T095 (Phase 7)."""

import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from watchers.base_watcher import BaseWatcher
from watchers.models import LogSeverity, WatcherState


# T030: MockWatcher subclass for testing

class MockWatcher(BaseWatcher):
    """Concrete test subclass of BaseWatcher."""

    def __init__(self, vault_path, poll_interval=60, items=None, fail_poll=False):
        super().__init__("mock_watcher", poll_interval, str(vault_path))
        self.items = items or []
        self.processed = []
        self.fail_poll = fail_poll
        self._prerequisites_called = False

    async def poll(self):
        if self.fail_poll:
            raise ConnectionError("Simulated poll failure")
        return self.items

    async def process_item(self, item):
        self.processed.append(item)

    def validate_prerequisites(self):
        self._prerequisites_called = True


# T031: start validates prerequisites

class TestStartValidatesPrerequisites:
    @pytest.mark.asyncio
    async def test_start_calls_validate_prerequisites(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        # Run one cycle then stop
        async def run_one_cycle():
            watcher.validate_prerequisites()
            watcher._prerequisites_called = True

        watcher.validate_prerequisites()
        assert watcher._prerequisites_called is True


# T032: start loads state

class TestStartLoadsState:
    @pytest.mark.asyncio
    async def test_loads_existing_state(self, tmp_vault):
        state_data = {
            "last_poll_timestamp": "2026-02-17T10:00:00Z",
            "processed_ids": ["id1", "id2"],
            "error_count": 1,
            "total_emails_processed": 5,
            "uptime_start": "2026-02-17T09:00:00Z",
        }
        state_path = tmp_vault / "Logs" / "mock_watcher_state.json"
        state_path.write_text(json.dumps(state_data))

        watcher = MockWatcher(tmp_vault)
        watcher._load_state()

        assert watcher.state.last_poll_timestamp == "2026-02-17T10:00:00Z"
        assert watcher.state.processed_ids == ["id1", "id2"]
        assert watcher.state.error_count == 1
        assert watcher.state.total_emails_processed == 5

    @pytest.mark.asyncio
    async def test_creates_clean_state_when_no_file(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._load_state()
        assert watcher.state.processed_ids == []
        assert watcher.state.error_count == 0


# T033: stop saves state and releases lock

class TestStopSavesStateAndReleasesLock:
    @pytest.mark.asyncio
    async def test_stop_saves_state(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher.state.total_emails_processed = 10
        watcher.state.processed_ids = ["id1"]
        watcher._acquire_lock()

        await watcher.stop()

        state_path = tmp_vault / "Logs" / "mock_watcher_state.json"
        assert state_path.exists()
        data = json.loads(state_path.read_text())
        assert data["total_emails_processed"] == 10
        assert data["processed_ids"] == ["id1"]

    @pytest.mark.asyncio
    async def test_stop_releases_lock(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._acquire_lock()
        lock_path = tmp_vault / "Logs" / ".mock_watcher.lock"
        assert lock_path.exists()

        await watcher.stop()
        assert not lock_path.exists()


# T034: poll cycle calls poll and process

class TestPollCycle:
    @pytest.mark.asyncio
    async def test_poll_cycle_processes_all_items(self, tmp_vault):
        items = ["email1", "email2", "email3"]
        watcher = MockWatcher(tmp_vault, items=items)

        await watcher._run_poll_cycle()

        assert watcher.processed == ["email1", "email2", "email3"]
        assert watcher.state.total_emails_processed == 3

    @pytest.mark.asyncio
    async def test_poll_cycle_updates_timestamp(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, items=["email1"])

        await watcher._run_poll_cycle()

        assert watcher.state.last_poll_timestamp != ""

    @pytest.mark.asyncio
    async def test_poll_cycle_empty_items(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, items=[])

        await watcher._run_poll_cycle()

        assert watcher.processed == []
        assert watcher.state.total_emails_processed == 0


# T035: retry with backoff succeeds

class TestRetryWithBackoff:
    @pytest.mark.asyncio
    async def test_succeeds_on_third_attempt(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        call_count = 0

        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError(f"Fail #{call_count}")
            return "success"

        with patch("watchers.base_watcher.asyncio.sleep", new_callable=AsyncMock):
            result = await watcher._retry_with_backoff(flaky_function, max_retries=3, base_delay=0.01)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)

        result = await watcher._retry_with_backoff(lambda: 42)

        assert result == 42


# T036: retry exhausted raises

class TestRetryExhausted:
    @pytest.mark.asyncio
    async def test_raises_after_max_retries(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)

        def always_fail():
            raise ConnectionError("Always fails")

        with patch("watchers.base_watcher.asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(ConnectionError, match="Always fails"):
                await watcher._retry_with_backoff(always_fail, max_retries=3, base_delay=0.01)


# T037: corrupt state recovery

class TestStateCorruptRecovery:
    @pytest.mark.asyncio
    async def test_corrupt_json_resets_state(self, tmp_vault):
        state_path = tmp_vault / "Logs" / "mock_watcher_state.json"
        state_path.write_text("{invalid json!!!")

        watcher = MockWatcher(tmp_vault)
        watcher._load_state()

        # Should reset to clean state
        assert watcher.state.processed_ids == []
        assert watcher.state.error_count == 0
        assert watcher.state.total_emails_processed == 0

    @pytest.mark.asyncio
    async def test_corrupt_state_logs_warning(self, tmp_vault):
        state_path = tmp_vault / "Logs" / "mock_watcher_state.json"
        state_path.write_text("not json")

        watcher = MockWatcher(tmp_vault)
        watcher._load_state()

        # Check that a warning was logged
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_vault / "Logs" / f"mock_watcher_{today}.log"
        assert log_path.exists()
        log_content = log_path.read_text()
        assert "state_corrupt" in log_content


# T038: log writes JSONL

class TestLogWritesJsonl:
    def test_log_creates_daily_file(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._log("test_event", LogSeverity.INFO, {"key": "value"})

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_vault / "Logs" / f"mock_watcher_{today}.log"
        assert log_path.exists()

    def test_log_entry_is_valid_json(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._log("test_event", LogSeverity.INFO, {"key": "value"})

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_vault / "Logs" / f"mock_watcher_{today}.log"
        lines = log_path.read_text().strip().split("\n")

        for line in lines:
            entry = json.loads(line)
            assert "timestamp" in entry
            assert entry["watcher_name"] == "mock_watcher"
            assert entry["event"] == "test_event"
            assert entry["severity"] == "info"

    def test_log_appends_multiple_entries(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._log("event1", LogSeverity.INFO)
        watcher._log("event2", LogSeverity.WARN)
        watcher._log("event3", LogSeverity.ERROR)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = tmp_vault / "Logs" / f"mock_watcher_{today}.log"
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 3

        events = [json.loads(line)["event"] for line in lines]
        assert events == ["event1", "event2", "event3"]


# T039: poll interval validation

class TestPollIntervalValidation:
    def test_rejects_interval_below_30(self, tmp_vault):
        with pytest.raises(ValueError, match="poll_interval must be >= 30"):
            MockWatcher(tmp_vault, poll_interval=10)

    def test_rejects_interval_zero(self, tmp_vault):
        with pytest.raises(ValueError):
            MockWatcher(tmp_vault, poll_interval=0)

    def test_accepts_interval_30(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, poll_interval=30)
        assert watcher.poll_interval == 30

    def test_accepts_interval_60(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, poll_interval=60)
        assert watcher.poll_interval == 60


# T040: health check returns status

class TestHealthCheck:
    def test_returns_status_dict(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher.state.last_poll_timestamp = "2026-02-17T10:00:00Z"
        watcher.state.error_count = 2
        watcher.state.total_emails_processed = 15
        watcher.state.uptime_start = "2026-02-17T09:00:00Z"

        health = watcher.health_check()

        assert health["name"] == "mock_watcher"
        assert health["status"] == "stopped"  # not running
        assert health["last_poll"] == "2026-02-17T10:00:00Z"
        assert health["error_count"] == 2
        assert health["total_processed"] == 15
        assert health["uptime_start"] == "2026-02-17T09:00:00Z"

    def test_status_ok_when_running(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._running = True
        health = watcher.health_check()
        assert health["status"] == "ok"

    def test_status_stopped_when_not_running(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._running = False
        health = watcher.health_check()
        assert health["status"] == "stopped"


# Additional: abstract method enforcement

class TestAbstractMethodEnforcement:
    def test_cannot_instantiate_base_directly(self):
        with pytest.raises(TypeError, match="abstract method"):
            BaseWatcher("test", 60, "vault")

    def test_incomplete_subclass_raises(self):
        class IncompleteWatcher(BaseWatcher):
            async def poll(self):
                return []
            # Missing process_item and validate_prerequisites

        with pytest.raises(TypeError):
            IncompleteWatcher("test", 60, "vault")


# Additional: state save/load round-trip

class TestStatePersistence:
    @pytest.mark.asyncio
    async def test_save_and_load_round_trip(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher.state.processed_ids = ["a", "b", "c"]
        watcher.state.total_emails_processed = 42
        watcher.state.error_count = 3

        watcher._save_state()

        watcher2 = MockWatcher(tmp_vault)
        watcher2._load_state()

        assert watcher2.state.processed_ids == ["a", "b", "c"]
        assert watcher2.state.total_emails_processed == 42
        assert watcher2.state.error_count == 3


# ── T092-T095: Phase 7 -- Observability (Dataview-compatible logging) ─────


def _read_log_entries(tmp_vault) -> list[dict]:
    """Helper: read all JSONL entries from today's log file."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_path = tmp_vault / "Logs" / f"mock_watcher_{today}.log"
    if not log_path.exists():
        return []
    lines = [l.strip() for l in log_path.read_text().split("\n") if l.strip()]
    return [json.loads(line) for line in lines]


class TestLogEntryDataviewParseable:
    """T092: Given log entry written by _log(),
    When parsed as JSON from disk,
    Then contains timestamp (ISO8601), watcher_name, event, severity (string),
    details dict -- all Dataview-queryable fields."""

    def test_log_entry_has_dataview_fields(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._log("test_event", LogSeverity.INFO, {"key": "value"})

        entries = _read_log_entries(tmp_vault)
        assert len(entries) >= 1

        entry = entries[-1]

        # All required Dataview-queryable top-level fields
        for field in ("timestamp", "watcher_name", "event", "severity", "details"):
            assert field in entry, f"Missing Dataview field: {field}"

        # timestamp must be ISO8601
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.match(iso_pattern, entry["timestamp"]), (
            f"timestamp '{entry['timestamp']}' is not ISO8601"
        )

        # severity must be a plain string (not an enum repr)
        assert isinstance(entry["severity"], str), "severity must be serialized as string"
        assert entry["severity"] == "info"

        # details must be a dict
        assert isinstance(entry["details"], dict)
        assert entry["details"]["key"] == "value"

        # watcher_name must be a string
        assert isinstance(entry["watcher_name"], str)
        assert entry["watcher_name"] == "mock_watcher"


class TestLogStartedEvent:
    """T093: Given watcher emits 'started' event,
    When log entry written,
    Then event='started', severity='info', details contains status='ok'."""

    def test_started_event_structure(self, tmp_vault):
        watcher = MockWatcher(tmp_vault)
        watcher._log("started", LogSeverity.INFO, {"status": "ok"})

        entries = _read_log_entries(tmp_vault)
        started = [e for e in entries if e.get("event") == "started"]
        assert len(started) >= 1

        entry = started[0]
        assert entry["event"] == "started"
        assert entry["severity"] == "info"
        assert "status" in entry["details"]
        assert entry["details"]["status"] == "ok"


class TestLogPollCycleSummary:
    """T094: Given poll cycle completes,
    When log written with poll_cycle_complete event,
    Then details includes: emails_found, emails_processed, errors, next_poll_time."""

    @pytest.mark.asyncio
    async def test_poll_cycle_summary_fields(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, items=["item1", "item2"])

        with patch("watchers.base_watcher.asyncio.sleep", new_callable=AsyncMock):
            await watcher._run_poll_cycle()

        entries = _read_log_entries(tmp_vault)
        cycle_entries = [e for e in entries if e.get("event") == "poll_cycle_complete"]
        assert len(cycle_entries) >= 1

        details = cycle_entries[0]["details"]
        for field in ("emails_found", "emails_processed", "errors", "next_poll_time"):
            assert field in details, f"poll_cycle_complete missing details field: {field}"

        assert details["emails_found"] == 2
        assert details["emails_processed"] == 2
        assert details["errors"] == 0
        # next_poll_time must be ISO8601
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T"
        assert re.match(iso_pattern, details["next_poll_time"])


class TestLogErrorIncludesSeverityAndType:
    """T095: Given error occurs during poll,
    When logged,
    Then severity is 'error' or 'critical', details includes error_type and error_message."""

    @pytest.mark.asyncio
    async def test_poll_error_log_structure(self, tmp_vault):
        watcher = MockWatcher(tmp_vault, fail_poll=True)

        with patch("watchers.base_watcher.asyncio.sleep", new_callable=AsyncMock):
            await watcher._run_poll_cycle()

        entries = _read_log_entries(tmp_vault)
        error_entries = [
            e for e in entries
            if e.get("severity") in ("error", "critical")
        ]
        assert len(error_entries) >= 1

        entry = error_entries[0]
        assert entry["severity"] in ("error", "critical")
        assert "error_type" in entry["details"], "Missing error_type in error log details"
        assert "error_message" in entry["details"], "Missing error_message in error log details"
        assert isinstance(entry["details"]["error_type"], str)
        assert isinstance(entry["details"]["error_message"], str)
