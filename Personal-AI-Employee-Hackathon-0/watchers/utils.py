"""Shared utilities for the watcher system.

Provides file operations, sanitization, environment loading,
YAML rendering, and file-based locking.
"""

from __future__ import annotations

import os
import re
import signal
import tempfile
from pathlib import Path

import yaml
from dotenv import load_dotenv


class PrerequisiteError(Exception):
    """Raised when a required prerequisite is not met.

    Attributes:
        ht_reference: Human Task reference (e.g., "HT-001").
    """

    def __init__(self, message: str, ht_reference: str = "") -> None:
        self.ht_reference = ht_reference
        full_message = message
        if ht_reference:
            full_message = f"{message} (see {ht_reference} in ai-control/HUMAN-TASKS.md)"
        super().__init__(full_message)


def sanitize_filename(text: str, max_length: int = 60) -> str:
    """Create a safe filename from arbitrary text.

    Lowercases, replaces non-alphanumeric chars with hyphens,
    collapses multiple hyphens, strips leading/trailing hyphens,
    and truncates to max_length.
    """
    if not text:
        return "untitled"
    result = text.lower()
    result = re.sub(r"[^a-z0-9]", "-", result)
    result = re.sub(r"-{2,}", "-", result)
    result = result.strip("-")
    if not result:
        return "untitled"
    if len(result) > max_length:
        result = result[:max_length].rstrip("-")
    return result


def atomic_write(filepath: str | Path, content: str) -> None:
    """Write content to file atomically via temp file + os.replace().

    Ensures parent directories exist. On crash, either the old file
    or the new file exists -- never a partial write (FR-017).
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        dir=str(filepath.parent),
        prefix=f".{filepath.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, str(filepath))
    except BaseException:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def sanitize_utf8(text: str) -> str:
    """Replace unmappable characters with U+FFFD replacement character."""
    if not text:
        return ""
    return text.encode("utf-8", errors="replace").decode("utf-8", errors="replace")


def truncate_subject(subject: str, max_length: int = 200) -> str:
    """Truncate subject at word boundary, append '...' if truncated."""
    if not subject:
        return ""
    if len(subject) <= max_length:
        return subject
    truncated = subject[:max_length]
    # Find last space for word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        truncated = truncated[:last_space]
    return truncated.rstrip() + "..."


def load_env() -> dict[str, str]:
    """Load .env and validate required Gmail keys.

    Returns:
        Dict with GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH.

    Raises:
        PrerequisiteError: If required keys are missing.
    """
    load_dotenv()
    required_keys = ["GMAIL_CREDENTIALS_PATH", "GMAIL_TOKEN_PATH"]
    result = {}
    missing = []
    for key in required_keys:
        value = os.environ.get(key)
        if not value:
            missing.append(key)
        else:
            result[key] = value
    if missing:
        raise PrerequisiteError(
            f"Missing required .env variables: {', '.join(missing)}. "
            f"Add them to .env file.",
            ht_reference="HT-002",
        )
    return result


def render_yaml_frontmatter(fields: dict) -> str:
    """Render a YAML frontmatter block between --- delimiters.

    Uses pyyaml safe dumper to avoid Python object tags.
    """
    if not fields:
        return "---\n---\n"
    yaml_content = yaml.dump(
        fields,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{yaml_content}---\n"


class FileLock:
    """PID-based file lock with stale recovery (FR-014).

    Usage:
        with FileLock("/path/to/.lock"):
            # critical section
    """

    def __init__(self, lock_path: str | Path) -> None:
        self.lock_path = Path(lock_path)
        self._acquired = False

    def acquire(self) -> None:
        """Acquire the lock. Raises RuntimeError if already locked by a live process."""
        if self.lock_path.exists():
            try:
                existing_pid = int(self.lock_path.read_text().strip())
            except (ValueError, OSError):
                # Corrupt lock file -- treat as stale
                self._remove_lock()
            else:
                if self._is_process_alive(existing_pid):
                    if existing_pid == os.getpid():
                        raise RuntimeError(
                            f"Lock already held by this process (PID {existing_pid})"
                        )
                    raise RuntimeError(
                        f"Lock held by active process (PID {existing_pid}). "
                        f"If this is stale, delete {self.lock_path}"
                    )
                else:
                    # Stale lock -- process no longer running
                    self._remove_lock()

        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.write_text(str(os.getpid()))
        self._acquired = True

    def release(self) -> None:
        """Release the lock by removing the lock file."""
        self._remove_lock()
        self._acquired = False

    def _remove_lock(self) -> None:
        try:
            self.lock_path.unlink()
        except FileNotFoundError:
            pass

    @staticmethod
    def _is_process_alive(pid: int) -> bool:
        """Check if a process is running via os.kill(pid, 0)."""
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(self, *args: object) -> None:
        self.release()
