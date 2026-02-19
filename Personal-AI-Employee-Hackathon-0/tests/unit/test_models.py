"""Unit tests for watchers.models -- T006, T007, T008."""

import pytest

from watchers.models import (
    Classification,
    EmailItem,
    LogSeverity,
    WatcherLogEntry,
    WatcherState,
)


# T006: Enum values and EmailItem basics

class TestClassificationEnum:
    def test_actionable_value(self):
        assert Classification.ACTIONABLE.value == "actionable"

    def test_informational_value(self):
        assert Classification.INFORMATIONAL.value == "informational"

    def test_enum_members(self):
        assert set(Classification) == {Classification.ACTIONABLE, Classification.INFORMATIONAL}


class TestLogSeverityEnum:
    def test_all_values(self):
        expected = {"debug", "info", "warn", "error", "critical"}
        assert {s.value for s in LogSeverity} == expected

    def test_ordering(self):
        members = list(LogSeverity)
        assert members == [
            LogSeverity.DEBUG,
            LogSeverity.INFO,
            LogSeverity.WARN,
            LogSeverity.ERROR,
            LogSeverity.CRITICAL,
        ]


class TestEmailItem:
    def test_field_access(self, sample_email_item):
        assert sample_email_item.message_id == "msg_abc123"
        assert sample_email_item.sender == "alice@example.com"
        assert sample_email_item.subject == "Meeting Follow-up: Q1 Review"
        assert sample_email_item.classification == Classification.ACTIONABLE
        assert sample_email_item.has_attachments is True
        assert sample_email_item.raw_size == 4096

    def test_immutability(self, sample_email_item):
        with pytest.raises(AttributeError):
            sample_email_item.subject = "modified"

    def test_recipients_list(self, sample_email_item):
        assert sample_email_item.recipients == ["bob@example.com"]

    def test_defaults(self):
        email = EmailItem(
            message_id="id1",
            sender="a@b.com",
            recipients=[],
            subject="Test",
            body="Body",
            date="2026-01-01T00:00:00Z",
            labels=[],
            classification=Classification.INFORMATIONAL,
        )
        assert email.has_attachments is False
        assert email.raw_size == 0


# T007: WatcherState round-trip and pruning

class TestWatcherState:
    def test_to_dict_round_trip(self):
        state = WatcherState(
            last_poll_timestamp="2026-02-17T10:00:00Z",
            processed_ids=["id1", "id2", "id3"],
            error_count=2,
            total_emails_processed=15,
            uptime_start="2026-02-17T09:00:00Z",
        )
        d = state.to_dict()
        restored = WatcherState.from_dict(d)
        assert restored.last_poll_timestamp == state.last_poll_timestamp
        assert restored.processed_ids == state.processed_ids
        assert restored.error_count == state.error_count
        assert restored.total_emails_processed == state.total_emails_processed
        assert restored.uptime_start == state.uptime_start

    def test_from_dict_missing_keys(self):
        state = WatcherState.from_dict({})
        assert state.last_poll_timestamp == ""
        assert state.processed_ids == []
        assert state.error_count == 0
        assert state.total_emails_processed == 0
        assert state.uptime_start == ""

    def test_from_dict_partial_keys(self):
        state = WatcherState.from_dict({"error_count": 5})
        assert state.error_count == 5
        assert state.processed_ids == []

    def test_prune_at_boundary(self):
        ids = [f"id_{i}" for i in range(100_005)]
        state = WatcherState(processed_ids=ids)
        state.prune_processed_ids(max_ids=100_000)
        assert len(state.processed_ids) == 100_000
        # Should keep the newest (last) IDs
        assert state.processed_ids[0] == "id_5"
        assert state.processed_ids[-1] == "id_100004"

    def test_prune_under_limit_noop(self):
        ids = ["id_1", "id_2", "id_3"]
        state = WatcherState(processed_ids=ids)
        state.prune_processed_ids(max_ids=100_000)
        assert len(state.processed_ids) == 3

    def test_defaults(self):
        state = WatcherState()
        assert state.last_poll_timestamp == ""
        assert state.processed_ids == []
        assert state.error_count == 0


# T008: WatcherLogEntry

class TestWatcherLogEntry:
    def test_to_dict_keys(self):
        entry = WatcherLogEntry(
            timestamp="2026-02-17T10:00:00Z",
            watcher_name="gmail_watcher",
            event="started",
            severity=LogSeverity.INFO,
            details={"status": "ok"},
        )
        d = entry.to_dict()
        assert set(d.keys()) == {"timestamp", "watcher_name", "event", "severity", "details"}

    def test_severity_serialized_as_string(self):
        entry = WatcherLogEntry(
            timestamp="2026-02-17T10:00:00Z",
            watcher_name="gmail_watcher",
            event="error",
            severity=LogSeverity.ERROR,
            details={},
        )
        d = entry.to_dict()
        assert d["severity"] == "error"
        assert isinstance(d["severity"], str)

    def test_immutability(self):
        entry = WatcherLogEntry(
            timestamp="2026-02-17T10:00:00Z",
            watcher_name="test",
            event="test",
            severity=LogSeverity.DEBUG,
        )
        with pytest.raises(AttributeError):
            entry.event = "modified"

    def test_default_details(self):
        entry = WatcherLogEntry(
            timestamp="2026-02-17T10:00:00Z",
            watcher_name="test",
            event="test",
            severity=LogSeverity.INFO,
        )
        assert entry.details == {}
