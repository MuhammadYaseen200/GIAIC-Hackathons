"""Data models for the watcher system.

Defines enums and dataclasses used across all watchers.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any


class Classification(enum.Enum):
    """Email classification categories."""

    ACTIONABLE = "actionable"
    INFORMATIONAL = "informational"


class LogSeverity(enum.Enum):
    """Log severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass(frozen=True)
class EmailItem:
    """Represents a single parsed email.

    Frozen dataclass -- immutable after creation.
    """

    message_id: str
    sender: str
    recipients: list[str]
    subject: str
    body: str
    date: str  # ISO 8601
    labels: list[str]
    classification: Classification
    has_attachments: bool = False
    raw_size: int = 0


@dataclass
class WatcherState:
    """Persistent watcher state across restarts.

    Serialized to vault/Logs/<name>_state.json.
    """

    last_poll_timestamp: str = ""
    processed_ids: list[str] = field(default_factory=list)
    error_count: int = 0
    total_emails_processed: int = 0
    uptime_start: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_poll_timestamp": self.last_poll_timestamp,
            "processed_ids": self.processed_ids,
            "error_count": self.error_count,
            "total_emails_processed": self.total_emails_processed,
            "uptime_start": self.uptime_start,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WatcherState:
        return cls(
            last_poll_timestamp=data.get("last_poll_timestamp", ""),
            processed_ids=data.get("processed_ids", []),
            error_count=data.get("error_count", 0),
            total_emails_processed=data.get("total_emails_processed", 0),
            uptime_start=data.get("uptime_start", ""),
        )

    def prune_processed_ids(self, max_ids: int = 100_000) -> None:
        """FIFO pruning to keep state file manageable (<10MB)."""
        if len(self.processed_ids) > max_ids:
            self.processed_ids = self.processed_ids[-max_ids:]


@dataclass(frozen=True)
class WatcherLogEntry:
    """Structured log entry for vault/Logs/ JSONL files."""

    timestamp: str
    watcher_name: str
    event: str
    severity: LogSeverity
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "watcher_name": self.watcher_name,
            "event": self.event,
            "severity": self.severity.value,
            "details": self.details,
        }
