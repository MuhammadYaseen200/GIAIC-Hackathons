"""Abstract base class for all watchers.

Provides lifecycle management (start/stop/poll), retry logic,
state persistence, structured logging, and file-based locking.
Per Constitution Principle VI and ADR-0001.
"""

from __future__ import annotations

import abc
import asyncio
import json
import signal
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from watchers.models import LogSeverity, WatcherLogEntry, WatcherState
from watchers.utils import FileLock, atomic_write


class BaseWatcher(abc.ABC):
    """Abstract base class for all watchers.

    Subclasses must implement:
        - poll() -> list: Fetch new items from the external source
        - process_item(item) -> None: Process a single item
        - validate_prerequisites() -> None: Check required resources exist
    """

    def __init__(
        self,
        name: str,
        poll_interval: int = 60,
        vault_path: str = "vault",
    ) -> None:
        if poll_interval < 30:
            raise ValueError(
                f"poll_interval must be >= 30 seconds, got {poll_interval}"
            )

        self.name = name
        self.poll_interval = poll_interval
        self.vault_path = Path(vault_path)

        # Derived paths
        self._log_dir = self.vault_path / "Logs"
        self._state_path = self._log_dir / f"{name}_state.json"
        self._lock_path = self._log_dir / f".{name}.lock"

        # Runtime state
        self.state = WatcherState()
        self._running = False
        self._lock: FileLock | None = None

    async def start(self) -> None:
        """Start the watcher: validate, load state, acquire lock, poll loop."""
        self.validate_prerequisites()
        self._load_state()
        self._acquire_lock()

        self.state.uptime_start = datetime.now(timezone.utc).isoformat()
        self._running = True

        self._log("started", LogSeverity.INFO, {"status": "ok"})

        # Register signal handlers for graceful shutdown
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                pass

        try:
            while self._running:
                await self._run_poll_cycle()
                if self._running:
                    await asyncio.sleep(self.poll_interval)
        except asyncio.CancelledError:
            pass
        finally:
            if self._running:
                await self.stop()

    async def stop(self) -> None:
        """Stop the watcher: save state, release lock, log shutdown."""
        self._running = False
        self._save_state()
        self._release_lock()
        self._log("stopped", LogSeverity.INFO, {"status": "shutdown"})

    async def _run_poll_cycle(self) -> None:
        """Execute one poll cycle: fetch items, process each, update state."""
        try:
            items = await self._retry_with_backoff(self.poll)
        except Exception as e:
            self.state.error_count += 1
            self._log("poll_error", LogSeverity.ERROR, {
                "error_type": type(e).__name__,
                "error_message": str(e),
            })
            self._save_state()
            return

        processed_count = 0
        errors_count = 0

        for item in items:
            try:
                await self._retry_with_backoff(lambda i=item: self.process_item(i))
                processed_count += 1
            except Exception as e:
                errors_count += 1
                self.state.error_count += 1
                self._log("process_error", LogSeverity.ERROR, {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                })

        self.state.total_emails_processed += processed_count
        self.state.last_poll_timestamp = datetime.now(timezone.utc).isoformat()
        self.state.prune_processed_ids()
        self._save_state()

        next_poll = datetime.now(timezone.utc).isoformat()
        self._log("poll_cycle_complete", LogSeverity.INFO, {
            "emails_found": len(items),
            "emails_processed": processed_count,
            "errors": errors_count,
            "next_poll_time": next_poll,
        })

    async def _retry_with_backoff(
        self,
        coro_factory: Any,
        max_retries: int = 3,
        base_delay: float = 2.0,
    ) -> Any:
        """Retry a callable with exponential backoff (2s, 4s, 8s).

        coro_factory: A callable that returns a result (sync or coroutine).
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                result = coro_factory()
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    self._log("retry", LogSeverity.WARN, {
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "delay_seconds": delay,
                        "error": str(e),
                    })
                    await asyncio.sleep(delay)
        raise last_exception  # type: ignore[misc]

    def _load_state(self) -> None:
        """Load persistent state from JSON file. Reset on corruption."""
        if not self._state_path.exists():
            self.state = WatcherState()
            return
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            self.state = WatcherState.from_dict(data)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self._log("state_corrupt", LogSeverity.WARN, {
                "error": str(e),
                "action": "reset_to_clean_state",
            })
            self.state = WatcherState()

    def _save_state(self) -> None:
        """Save persistent state to JSON file atomically."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self.state.to_dict(), indent=2)
        atomic_write(self._state_path, content)

    def _log(self, event: str, severity: LogSeverity, details: dict | None = None) -> None:
        """Append a structured JSONL log entry to the daily log file."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_path = self._log_dir / f"{self.name}_{today}.log"

        entry = WatcherLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            watcher_name=self.name,
            event=event,
            severity=severity,
            details=details or {},
        )

        line = json.dumps(entry.to_dict()) + "\n"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)

    def _acquire_lock(self) -> None:
        """Acquire the file-based lock to prevent concurrent instances."""
        self._lock = FileLock(self._lock_path)
        self._lock.acquire()

    def _release_lock(self) -> None:
        """Release the file-based lock."""
        if self._lock:
            self._lock.release()
            self._lock = None

    def health_check(self) -> dict[str, Any]:
        """Return current health status as a dict."""
        return {
            "name": self.name,
            "status": "ok" if self._running else "stopped",
            "last_poll": self.state.last_poll_timestamp,
            "error_count": self.state.error_count,
            "total_processed": self.state.total_emails_processed,
            "uptime_start": self.state.uptime_start,
        }

    @abc.abstractmethod
    async def poll(self) -> list:
        """Fetch new items from the external source. Must be overridden."""
        ...

    @abc.abstractmethod
    async def process_item(self, item: Any) -> None:
        """Process a single item. Must be overridden."""
        ...

    @abc.abstractmethod
    def validate_prerequisites(self) -> None:
        """Validate that all required resources exist. Must be overridden."""
        ...
