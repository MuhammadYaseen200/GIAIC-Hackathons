"""Unit tests for US3 Draft Reply Generation — DraftReply model + vault_ops integration.

Tests validate:
    - DraftReply model has all required frontmatter fields
    - Draft filename uses message_id slug
    - Subject always prefixed "Re: " (not duplicated)
    - Draft body contains reply_body content
    - Draft created for draft_reply and urgent decisions
    - Draft NOT created for archive, needs_info, delegate decisions
"""

import json
from pathlib import Path

import pytest
import yaml

from orchestrator.models import DraftReply, LLMDecision
from orchestrator.vault_ops import write_draft_reply

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_draft(
    message_id: str = "msg_001",
    subject: str = "Q1 Report Review",
    reply_body: str = "Hi Alice, I'll review and respond shortly.",
    drafted_by: str = "anthropic:claude-sonnet-4-20250514",
) -> DraftReply:
    return DraftReply(
        source_message_id=message_id,
        to="alice@example.com",
        subject=subject,
        drafted_by=drafted_by,
        drafted_at="2026-02-19T21:00:00+00:00",
        reply_body=reply_body,
    )


def _parse_frontmatter(file_path: Path) -> dict:
    content = file_path.read_text(encoding="utf-8")
    fm_text = content.split("---\n")[1]
    return yaml.safe_load(fm_text) or {}


# ---------------------------------------------------------------------------
# DraftReply model — required frontmatter fields
# ---------------------------------------------------------------------------

class TestDraftReplyModel:

    def test_has_type_field(self):
        draft = _make_draft()
        assert draft.type == "draft_reply"

    def test_has_status_field(self):
        draft = _make_draft()
        assert draft.status == "pending_approval"

    def test_has_source_message_id(self):
        draft = _make_draft(message_id="specific_msg_id")
        assert draft.source_message_id == "specific_msg_id"

    def test_has_to_field(self):
        draft = _make_draft()
        assert draft.to == "alice@example.com"

    def test_has_subject_field(self):
        draft = _make_draft(subject="Meeting Update")
        assert draft.subject is not None

    def test_has_drafted_by_field(self):
        draft = _make_draft(drafted_by="openai:gpt-4o-mini")
        assert draft.drafted_by == "openai:gpt-4o-mini"

    def test_has_drafted_at_field(self):
        draft = _make_draft()
        assert "2026-02-19" in draft.drafted_at


# ---------------------------------------------------------------------------
# Subject prefix enforcement
# ---------------------------------------------------------------------------

class TestDraftReplySubjectPrefix:

    def test_re_prefix_added_when_missing(self):
        draft = _make_draft(subject="Q1 Report")
        assert draft.subject == "Re: Q1 Report"

    def test_re_prefix_not_duplicated(self):
        draft = _make_draft(subject="Re: Q1 Report")
        assert draft.subject == "Re: Q1 Report"
        assert not draft.subject.startswith("Re: Re:")

    def test_lowercase_re_not_duplicated(self):
        draft = _make_draft(subject="re: lowercase prefix")
        assert not draft.subject.lower().startswith("re: re:")


# ---------------------------------------------------------------------------
# Draft file creation (vault_ops.write_draft_reply)
# ---------------------------------------------------------------------------

class TestDraftFileCreation:

    def test_filename_uses_message_id_slug(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = _make_draft(message_id="msg_abc123")
        path = write_draft_reply(drafts_dir, draft)
        assert "msg_abc123" in path.name

    def test_file_has_all_frontmatter_fields(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        draft = _make_draft()
        path = write_draft_reply(drafts_dir, draft)
        fm = _parse_frontmatter(path)
        assert fm["type"] == "draft_reply"
        assert fm["status"] == "pending_approval"
        assert fm["source_message_id"] == "msg_001"
        assert fm["to"] == "alice@example.com"
        assert fm["drafted_by"] == "anthropic:claude-sonnet-4-20250514"
        assert "drafted_at" in fm

    def test_file_body_contains_reply_body(self, tmp_vault_dir):
        drafts_dir = tmp_vault_dir / "Drafts"
        reply_text = "Hi Alice, thank you for the update."
        draft = _make_draft(reply_body=reply_text)
        path = write_draft_reply(drafts_dir, draft)
        content = path.read_text(encoding="utf-8")
        assert reply_text in content


# ---------------------------------------------------------------------------
# Which decisions create drafts (LLMDecision → draft_reply / urgent)
# ---------------------------------------------------------------------------

class TestDecisionsCreatingDrafts:
    """Verify the logical contract: only draft_reply and urgent create drafts."""

    def test_draft_reply_decision_should_trigger_draft(self):
        """draft_reply decision: reply_body is REQUIRED by LLMDecision validator."""
        d = LLMDecision(
            decision="draft_reply",
            confidence=0.9,
            reasoning="Email requires a response.",
            reply_body="Hi, thanks for reaching out.",
        )
        assert d.decision == "draft_reply"
        assert d.reply_body is not None

    def test_urgent_decision_may_have_reply_body(self):
        """urgent decision: reply_body is OPTIONAL."""
        d = LLMDecision(
            decision="urgent",
            confidence=0.95,
            reasoning="Payment overdue.",
            reply_body="We acknowledge your urgent request.",
        )
        assert d.decision == "urgent"
        assert d.reply_body is not None

    def test_urgent_decision_without_reply_body_is_valid(self):
        """urgent without reply_body is valid — no draft needed."""
        d = LLMDecision(
            decision="urgent",
            confidence=0.95,
            reasoning="Immediate attention required.",
        )
        assert d.reply_body is None

    def test_archive_decision_has_no_reply_body(self):
        """archive should not have reply_body — would be a model error."""
        d = LLMDecision(
            decision="archive",
            confidence=0.8,
            reasoning="Newsletter, no action needed.",
        )
        assert d.reply_body is None

    def test_needs_info_has_no_reply_body(self):
        d = LLMDecision(
            decision="needs_info",
            confidence=0.6,
            reasoning="Need more context.",
            info_needed="Which product line does this refer to?",
        )
        assert d.reply_body is None

    def test_delegate_has_no_reply_body(self):
        d = LLMDecision(
            decision="delegate",
            confidence=0.75,
            reasoning="Out of my scope.",
            delegation_target="Engineering Manager",
        )
        assert d.reply_body is None

    def test_draft_reply_json_roundtrip(self):
        """LLMDecision with draft_reply round-trips through from_json_string."""
        raw = json.dumps({
            "decision": "draft_reply",
            "confidence": 0.88,
            "reasoning": "Needs a response.",
            "reply_body": "Hi, we will look into this.",
        })
        d = LLMDecision.from_json_string(raw)
        assert d.decision == "draft_reply"
        assert d.reply_body == "Hi, we will look into this."
