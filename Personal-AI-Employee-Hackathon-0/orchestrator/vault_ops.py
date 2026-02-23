"""Atomic vault file operations for Ralph Wiggum Orchestrator.

All write operations use atomic_write() from watchers/utils.py to prevent
partial writes on crash.  Frontmatter is YAML, body is plain text separated
by --- delimiters.

File format (vault markdown files):
    ---
    type: email
    status: pending
    message_id: abc123
    from: Alice <alice@example.com>
    subject: Meeting Follow-up
    ...
    ---
    Email body text here.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Optional

import yaml

from watchers.utils import atomic_write, render_yaml_frontmatter

from orchestrator.models import DraftReply, EmailContext

# ---------------------------------------------------------------------------
# Frontmatter parsing helpers
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(
    r"^---\n(.*?)\n---\n?(.*)",
    re.DOTALL,
)


def _split_file(content: str) -> tuple[dict, str]:
    """Split a vault markdown file into (frontmatter_dict, body_text).

    Raises:
        ValueError: If the file has no valid frontmatter block.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise ValueError("File has no valid YAML frontmatter block (expected --- delimiters)")
    fm_text, body = match.group(1), match.group(2)
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML frontmatter: {exc}") from exc
    if not isinstance(fm, dict):
        raise ValueError(f"Frontmatter must be a YAML mapping, got {type(fm).__name__}")
    return fm, body


def _join_file(frontmatter: dict, body: str) -> str:
    """Reassemble a vault file from frontmatter dict and body text."""
    return render_yaml_frontmatter(frontmatter) + body


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ensure_directory(dir_path: Path) -> None:
    """Create directory if it does not exist (idempotent)."""
    dir_path.mkdir(parents=True, exist_ok=True)


def scan_pending_emails(needs_action_dir: Path) -> list[Path]:
    """Scan a directory for vault files with status: pending in frontmatter.

    Reads only the frontmatter block (not the full body) for performance.

    Args:
        needs_action_dir: Path to vault/Needs_Action/.

    Returns:
        Sorted list of Paths with status == 'pending'.
    """
    pending: list[Path] = []
    for path in sorted(needs_action_dir.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
            fm, _ = _split_file(content)
            if str(fm.get("status", "")).lower() == "pending":
                pending.append(path)
        except (ValueError, OSError, yaml.YAMLError):
            # Corrupt or unreadable file — skip silently (logged by caller)
            continue
    return pending


def read_email_context(file_path: Path) -> EmailContext:
    """Parse a vault markdown file into an EmailContext model.

    Args:
        file_path: Absolute path to the vault markdown file.

    Returns:
        EmailContext populated from frontmatter and body.

    Raises:
        ValueError: If frontmatter is missing, corrupt, or missing required fields.
    """
    content = file_path.read_text(encoding="utf-8")
    fm, body = _split_file(content)

    # Map YAML `from` key → EmailContext.sender (avoid Python keyword clash)
    sender = str(fm.get("from", fm.get("sender", "")))
    message_id = str(fm.get("message_id", "")).strip()
    if not message_id:
        raise ValueError(f"Frontmatter missing 'message_id' in {file_path}")

    return EmailContext(
        message_id=message_id,
        sender=sender,
        subject=str(fm.get("subject", "")),
        body=body.strip(),
        classification=str(fm.get("classification", "unknown")),
        priority=str(fm.get("priority", "standard")),
        date_received=str(fm.get("date_received", "")),
        has_attachments=bool(fm.get("has_attachments", False)),
        filepath=str(file_path),
    )


def update_frontmatter(file_path: Path, updates: dict) -> None:
    """Atomically update YAML frontmatter fields, preserving body content.

    Args:
        file_path: Path to the vault markdown file.
        updates: Dict of fields to set/overwrite in the frontmatter.
    """
    content = file_path.read_text(encoding="utf-8")
    fm, body = _split_file(content)
    fm.update(updates)
    atomic_write(file_path, _join_file(fm, body))


def append_to_body(file_path: Path, text: str) -> None:
    """Atomically append text to the body section of a vault file.

    Args:
        file_path: Path to the vault markdown file.
        text: Text to append (a blank line separator is added automatically).
    """
    content = file_path.read_text(encoding="utf-8")
    fm, body = _split_file(content)
    new_body = body.rstrip("\n") + "\n\n" + text + "\n"
    atomic_write(file_path, _join_file(fm, new_body))


def write_draft_reply(drafts_dir: Path, draft: DraftReply) -> Path:
    """Write a DraftReply as a vault markdown file in vault/Drafts/.

    Args:
        drafts_dir: Path to vault/Drafts/ directory.
        draft: The DraftReply model to persist.

    Returns:
        Path to the created draft file.
    """
    ensure_directory(drafts_dir)

    # Build YAML frontmatter
    fm = {
        "type": draft.type,
        "status": draft.status,
        "source_message_id": draft.source_message_id,
        "to": draft.to,
        "subject": draft.subject,
        "drafted_by": draft.drafted_by,
        "drafted_at": draft.drafted_at,
    }

    slug = draft.source_message_id.replace("/", "_").replace("\\", "_")[:60]
    file_path = drafts_dir / f"draft_{slug}.md"
    content = render_yaml_frontmatter(fm) + draft.reply_body + "\n"
    atomic_write(file_path, content)
    return file_path


def move_to_done(file_path: Path, done_dir: Path) -> Path:
    """Move a vault file from Needs_Action to Done/.

    Args:
        file_path: Current path of the file.
        done_dir: Destination vault/Done/ directory.

    Returns:
        New path of the moved file.
    """
    ensure_directory(done_dir)
    dest = done_dir / file_path.name
    shutil.move(str(file_path), str(dest))
    return dest
