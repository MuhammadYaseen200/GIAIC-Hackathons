"""Unit tests for watchers.utils -- T009 through T015."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from watchers.utils import (
    FileLock,
    PrerequisiteError,
    atomic_write,
    load_env,
    render_yaml_frontmatter,
    sanitize_filename,
    sanitize_utf8,
    truncate_subject,
)


# T009: sanitize_filename

class TestSanitizeFilename:
    def test_normal_text(self):
        assert sanitize_filename("Hello World") == "hello-world"

    def test_special_characters_stripped(self):
        assert sanitize_filename("Hello! @World# $2026") == "hello-world-2026"

    def test_max_length_truncation(self):
        long_text = "a" * 100
        result = sanitize_filename(long_text, max_length=60)
        assert len(result) <= 60

    def test_empty_input(self):
        assert sanitize_filename("") == "untitled"

    def test_only_special_chars(self):
        assert sanitize_filename("!@#$%") == "untitled"

    def test_unicode_handling(self):
        result = sanitize_filename("Ünïcödé Tëst")
        assert result  # Should produce a non-empty string
        assert all(c.isalnum() or c == "-" for c in result)

    def test_multiple_hyphens_collapsed(self):
        assert sanitize_filename("hello---world") == "hello-world"

    def test_leading_trailing_hyphens_stripped(self):
        assert sanitize_filename("-hello-world-") == "hello-world"

    def test_numeric_input(self):
        assert sanitize_filename("12345") == "12345"


# T010: atomic_write

class TestAtomicWrite:
    def test_successful_write(self, tmp_path):
        filepath = tmp_path / "test.txt"
        atomic_write(filepath, "hello world")
        assert filepath.read_text() == "hello world"

    def test_creates_parent_directories(self, tmp_path):
        filepath = tmp_path / "sub" / "dir" / "test.txt"
        atomic_write(filepath, "content")
        assert filepath.read_text() == "content"

    def test_overwrites_existing_file(self, tmp_path):
        filepath = tmp_path / "test.txt"
        filepath.write_text("old content")
        atomic_write(filepath, "new content")
        assert filepath.read_text() == "new content"

    def test_no_temp_file_left_on_success(self, tmp_path):
        filepath = tmp_path / "test.txt"
        atomic_write(filepath, "content")
        # Only the target file should exist
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "test.txt"

    def test_string_path_accepted(self, tmp_path):
        filepath = str(tmp_path / "test.txt")
        atomic_write(filepath, "content")
        assert Path(filepath).read_text() == "content"


# T011: sanitize_utf8

class TestSanitizeUtf8:
    def test_valid_utf8_passthrough(self):
        text = "Hello, World! 你好"
        assert sanitize_utf8(text) == text

    def test_empty_string(self):
        assert sanitize_utf8("") == ""

    def test_ascii_passthrough(self):
        text = "Simple ASCII text"
        assert sanitize_utf8(text) == text

    def test_emoji_passthrough(self):
        text = "Hello 🌍"
        assert sanitize_utf8(text) == text


# T012: truncate_subject

class TestTruncateSubject:
    def test_under_limit_passthrough(self):
        subject = "Short subject"
        assert truncate_subject(subject) == subject

    def test_over_limit_truncates(self):
        subject = "word " * 100  # 500 chars
        result = truncate_subject(subject, max_length=50)
        assert len(result) <= 53  # 50 + "..."
        assert result.endswith("...")

    def test_exactly_at_limit(self):
        subject = "x" * 200
        assert truncate_subject(subject, max_length=200) == subject

    def test_empty_string(self):
        assert truncate_subject("") == ""

    def test_word_boundary_truncation(self):
        subject = "Hello beautiful wonderful amazing world"
        result = truncate_subject(subject, max_length=25)
        assert result.endswith("...")
        # Should not cut mid-word
        assert "..." in result


# T013: render_yaml_frontmatter

class TestRenderYamlFrontmatter:
    def test_produces_delimiters(self):
        result = render_yaml_frontmatter({"key": "value"})
        assert result.startswith("---\n")
        assert result.endswith("---\n")

    def test_fields_present(self):
        result = render_yaml_frontmatter({
            "type": "email",
            "status": "pending",
            "from": "alice@example.com",
        })
        assert "type: email" in result
        assert "status: pending" in result
        assert "from: alice@example.com" in result

    def test_empty_dict(self):
        result = render_yaml_frontmatter({})
        assert result == "---\n---\n"

    def test_special_characters_safe(self):
        result = render_yaml_frontmatter({
            "subject": "Re: Hello & Goodbye <test>",
        })
        assert "---" in result
        # Should be valid YAML (no Python object tags)
        assert "!!python" not in result

    def test_boolean_values(self):
        result = render_yaml_frontmatter({"has_attachments": False})
        assert "has_attachments: false" in result


# T014: FileLock

class TestFileLock:
    def test_acquire_release_cycle(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock = FileLock(lock_path)
        lock.acquire()
        assert lock_path.exists()
        pid_content = lock_path.read_text().strip()
        assert pid_content == str(os.getpid())
        lock.release()
        assert not lock_path.exists()

    def test_double_acquire_same_process_raises(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock = FileLock(lock_path)
        lock.acquire()
        try:
            lock2 = FileLock(lock_path)
            with pytest.raises(RuntimeError, match="already held by this process"):
                lock2.acquire()
        finally:
            lock.release()

    def test_stale_lock_recovery(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        # Write a PID that doesn't exist (99999999)
        lock_path.write_text("99999999")
        lock = FileLock(lock_path)
        # Should recover from stale lock
        lock.acquire()
        assert lock_path.read_text().strip() == str(os.getpid())
        lock.release()

    def test_context_manager(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        with FileLock(lock_path) as lock:
            assert lock_path.exists()
        assert not lock_path.exists()

    def test_corrupt_lock_file_recovery(self, tmp_path):
        lock_path = tmp_path / ".test.lock"
        lock_path.write_text("not-a-number")
        lock = FileLock(lock_path)
        lock.acquire()  # Should recover
        lock.release()


# T015: load_env

class TestLoadEnv:
    def test_loads_from_env(self, mock_env):
        result = load_env()
        assert "GMAIL_CREDENTIALS_PATH" in result
        assert "GMAIL_TOKEN_PATH" in result

    def test_raises_on_missing_keys(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GMAIL_CREDENTIALS_PATH", raising=False)
        monkeypatch.delenv("GMAIL_TOKEN_PATH", raising=False)
        # Create empty .env
        env_file = tmp_path / ".env"
        env_file.write_text("")
        with patch("watchers.utils.load_dotenv"):
            with pytest.raises(PrerequisiteError, match="Missing required .env"):
                load_env()

    def test_prerequisite_error_has_ht_reference(self, tmp_path, monkeypatch):
        monkeypatch.delenv("GMAIL_CREDENTIALS_PATH", raising=False)
        monkeypatch.delenv("GMAIL_TOKEN_PATH", raising=False)
        with patch("watchers.utils.load_dotenv"):
            with pytest.raises(PrerequisiteError) as exc_info:
                load_env()
            assert exc_info.value.ht_reference == "HT-002"


class TestPrerequisiteError:
    def test_basic_message(self):
        err = PrerequisiteError("Something missing")
        assert str(err) == "Something missing"
        assert err.ht_reference == ""

    def test_with_ht_reference(self):
        err = PrerequisiteError("Vault missing", ht_reference="HT-001")
        assert "HT-001" in str(err)
        assert err.ht_reference == "HT-001"
