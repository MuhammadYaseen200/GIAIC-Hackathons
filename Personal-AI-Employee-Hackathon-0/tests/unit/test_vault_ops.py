"""Unit tests for orchestrator/vault_ops.py — vault file operations.

Tests validate:
    - scan_pending_emails(): finds pending, skips non-pending, handles corrupt
    - read_email_context(): parses frontmatter + body; raises on missing fields
    - update_frontmatter(): applies updates, preserves body
    - append_to_body(): adds text, preserves frontmatter
    - write_draft_reply(): creates file with correct YAML frontmatter
    - move_to_done(): moves file to Done/ directory
    - ensure_directory(): creates dir (idempotent)
"""

from pathlib import Path

import pytest
import yaml

from orchestrator.models import DraftReply
from orchestrator.vault_ops import (
    append_to_body,
    ensure_directory,
    move_to_done,
    read_email_context,
    scan_pending_emails,
    update_frontmatter,
    write_draft_reply,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_email_file(directory: Path, filename: str, frontmatter: dict, body: str = "") -> Path:
    """Write a minimal vault markdown file for testing."""
    import yaml as _yaml
    fm_text = _yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_text}---\n{body}"
    path = directory / filename
    path.write_text(content, encoding="utf-8")
    return path


def _pending_fm(message_id: str = "msg_001") -> dict:
    return {
        "type": "email",
        "status": "pending",
        "message_id": message_id,
        "from": "alice@example.com",
        "subject": "Test Subject",
        "date_received": "Thu, 19 Feb 2026 21:00:00 +0000",
        "classification": "actionable",
        "priority": "standard",
        "has_attachments": False,
    }


# ---------------------------------------------------------------------------
# ensure_directory()
# ---------------------------------------------------------------------------

class TestEnsureDirectory:

    def test_creates_directory(self, tmp_path):
        new_dir = tmp_path / "vault" / "Drafts"
        assert not new_dir.exists()
        ensure_directory(new_dir)
        assert new_dir.exists()

    def test_idempotent_existing_directory(self, tmp_path):
        existing = tmp_path / "existing"
        existing.mkdir()
        ensure_directory(existing)  # must not raise
        assert existing.exists()


# ---------------------------------------------------------------------------
# scan_pending_emails()
# ---------------------------------------------------------------------------

class TestScanPendingEmails:

    def test_finds_pending_file(self, tmp_vault_dir):
        needs_action = tmp_vault_dir / "Needs_Action"
        _write_email_file(needs_action, "email1.md", _pending_fm("msg_001"))
        results = scan_pending_emails(needs_action)
        assert len(results) == 1
        assert results[0].name == "email1.md"

    def test_skips_done_status(self, tmp_vault_dir):
        needs_action = tmp_vault_dir / "Needs_Action"
        fm = _pending_fm()
        fm["status"] = "done"
        _write_email_file(needs_action, "done.md", fm)
        results = scan_pending_emails(needs_action)
        assert results == []

    def test_skips_failed_status(self, tmp_vault_dir):
        needs_action = tmp_vault_dir / "Needs_Action"
        fm = _pending_fm()
        fm["status"] = "failed"
        _write_email_file(needs_action, "failed.md", fm)
        results = scan_pending_emails(needs_action)
        assert results == []

    def test_skips_corrupt_file(self, tmp_vault_dir):
        needs_action = tmp_vault_dir / "Needs_Action"
        corrupt = needs_action / "corrupt.md"
        corrupt.write_text("NOT YAML FRONTMATTER AT ALL", encoding="utf-8")
        results = scan_pending_emails(needs_action)
        assert results == []

    def test_multiple_files_sorted(self, tmp_vault_dir):
        needs_action = tmp_vault_dir / "Needs_Action"
        _write_email_file(needs_action, "zzz.md", _pending_fm("msg_z"))
        _write_email_file(needs_action, "aaa.md", _pending_fm("msg_a"))
        results = scan_pending_emails(needs_action)
        assert len(results) == 2
        assert results[0].name < results[1].name  # sorted


# ---------------------------------------------------------------------------
# read_email_context()
# ---------------------------------------------------------------------------

class TestReadEmailContext:

    def test_parses_frontmatter_fields(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md",
            _pending_fm("test_msg_001"),
            body="Hello, please review.\n",
        )
        ctx = read_email_context(path)
        assert ctx.message_id == "test_msg_001"
        assert ctx.sender == "alice@example.com"
        assert ctx.subject == "Test Subject"
        assert ctx.classification == "actionable"
        assert ctx.priority == "standard"

    def test_parses_body(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md",
            _pending_fm("msg_b"),
            body="This is the email body.\n",
        )
        ctx = read_email_context(path)
        assert "This is the email body." in ctx.body

    def test_filepath_set(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm()
        )
        ctx = read_email_context(path)
        assert ctx.filepath == str(path)

    def test_has_attachments_default_false(self, tmp_vault_dir):
        fm = _pending_fm()
        fm.pop("has_attachments", None)
        path = _write_email_file(tmp_vault_dir / "Needs_Action", "msg.md", fm)
        ctx = read_email_context(path)
        assert ctx.has_attachments is False

    def test_missing_message_id_raises(self, tmp_vault_dir):
        fm = _pending_fm()
        del fm["message_id"]
        path = _write_email_file(tmp_vault_dir / "Needs_Action", "bad.md", fm)
        with pytest.raises(ValueError, match="message_id"):
            read_email_context(path)

    def test_no_frontmatter_raises(self, tmp_vault_dir):
        path = tmp_vault_dir / "Needs_Action" / "no_fm.md"
        path.write_text("Just body text with no frontmatter.\n", encoding="utf-8")
        with pytest.raises(ValueError, match="frontmatter"):
            read_email_context(path)


# ---------------------------------------------------------------------------
# update_frontmatter()
# ---------------------------------------------------------------------------

class TestUpdateFrontmatter:

    def test_updates_status_field(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm(),
            body="Body stays intact.\n",
        )
        update_frontmatter(path, {"status": "done"})
        content = path.read_text(encoding="utf-8")
        fm, body = content.split("---\n", 2)[1], content.split("---\n", 2)[2]
        data = yaml.safe_load(fm)
        assert data["status"] == "done"

    def test_preserves_body_after_update(self, tmp_vault_dir):
        original_body = "Body that must survive.\n"
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm(),
            body=original_body,
        )
        update_frontmatter(path, {"decision": "archive"})
        content = path.read_text(encoding="utf-8")
        assert "Body that must survive." in content

    def test_adds_new_field(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm()
        )
        update_frontmatter(path, {"draft_path": "/vault/Drafts/draft_001.md"})
        content = path.read_text(encoding="utf-8")
        assert "draft_path" in content

    def test_overwrites_existing_field(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm()
        )
        update_frontmatter(path, {"status": "needs_info"})
        update_frontmatter(path, {"status": "pending_approval"})
        content = path.read_text(encoding="utf-8")
        # Should not contain both values
        parsed = yaml.safe_load(content.split("---\n")[1])
        assert parsed["status"] == "pending_approval"


# ---------------------------------------------------------------------------
# append_to_body()
# ---------------------------------------------------------------------------

class TestAppendToBody:

    def test_appends_text(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm(),
            body="Original body.\n",
        )
        append_to_body(path, "AI note: needs more info.")
        content = path.read_text(encoding="utf-8")
        assert "AI note: needs more info." in content
        assert "Original body." in content

    def test_frontmatter_preserved(self, tmp_vault_dir):
        path = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm(), body="Body.\n"
        )
        append_to_body(path, "Extra line.")
        content = path.read_text(encoding="utf-8")
        # Frontmatter delimiters still present
        assert content.startswith("---")
        # message_id still parseable
        fm = yaml.safe_load(content.split("---\n")[1])
        assert fm["message_id"] == "msg_001"


# ---------------------------------------------------------------------------
# write_draft_reply()
# ---------------------------------------------------------------------------

class TestWriteDraftReply:

    def test_creates_file_in_drafts_dir(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = DraftReply(
            source_message_id="msg_001",
            to="alice@example.com",
            subject="Q1 Report Review",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-19T21:00:00+00:00",
            reply_body="Hi Alice, thank you for the report.",
        )
        path = write_draft_reply(drafts_dir, draft)
        assert path.exists()
        assert path.parent == drafts_dir

    def test_frontmatter_has_required_fields(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = DraftReply(
            source_message_id="msg_002",
            to="bob@example.com",
            subject="Meeting",
            drafted_by="openai:gpt-4o-mini",
            drafted_at="2026-02-20T10:00:00+00:00",
            reply_body="Hi Bob.",
        )
        path = write_draft_reply(drafts_dir, draft)
        content = path.read_text(encoding="utf-8")
        fm = yaml.safe_load(content.split("---\n")[1])
        assert fm["type"] == "draft_reply"
        assert fm["status"] == "pending_approval"
        assert fm["source_message_id"] == "msg_002"
        assert fm["to"] == "bob@example.com"

    def test_subject_has_re_prefix(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = DraftReply(
            source_message_id="msg_003",
            to="carol@example.com",
            subject="No prefix yet",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-20T11:00:00+00:00",
            reply_body="Hi Carol.",
        )
        path = write_draft_reply(drafts_dir, draft)
        content = path.read_text(encoding="utf-8")
        fm = yaml.safe_load(content.split("---\n")[1])
        assert fm["subject"].startswith("Re: ")

    def test_body_present_in_file(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = DraftReply(
            source_message_id="msg_004",
            to="dave@example.com",
            subject="Test",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-20T12:00:00+00:00",
            reply_body="This is the reply content.",
        )
        path = write_draft_reply(drafts_dir, draft)
        content = path.read_text(encoding="utf-8")
        assert "This is the reply content." in content

    def test_creates_drafts_dir_if_absent(self, tmp_path):
        drafts_dir = tmp_path / "vault" / "Drafts"
        assert not drafts_dir.exists()
        draft = DraftReply(
            source_message_id="msg_005",
            to="eve@example.com",
            subject="Test",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-20T12:00:00+00:00",
            reply_body="Content.",
        )
        write_draft_reply(drafts_dir, draft)
        assert drafts_dir.exists()


# ---------------------------------------------------------------------------
# move_to_done()
# ---------------------------------------------------------------------------

class TestMoveToDone:

    def test_moves_file_to_done(self, tmp_vault_dir):
        src = _write_email_file(
            tmp_vault_dir / "Needs_Action", "msg.md", _pending_fm()
        )
        done_dir = tmp_vault_dir / "Done"
        dest = move_to_done(src, done_dir)
        assert dest.exists()
        assert not src.exists()
        assert dest.parent == done_dir

    def test_creates_done_dir_if_absent(self, tmp_path):
        src_dir = tmp_path / "Needs_Action"
        src_dir.mkdir()
        src = _write_email_file(src_dir, "msg.md", _pending_fm())
        done_dir = tmp_path / "Done"
        assert not done_dir.exists()
        move_to_done(src, done_dir)
        assert done_dir.exists()

    def test_destination_filename_preserved(self, tmp_vault_dir):
        src = _write_email_file(
            tmp_vault_dir / "Needs_Action", "specific_name.md", _pending_fm()
        )
        done_dir = tmp_vault_dir / "Done"
        dest = move_to_done(src, done_dir)
        assert dest.name == "specific_name.md"
