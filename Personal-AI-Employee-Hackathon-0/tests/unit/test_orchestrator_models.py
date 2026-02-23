"""Unit tests for orchestrator/models.py — TDD spec for all Pydantic v2 models.

Tests validate:
    - LLMDecision: field constraints, decision-specific required fields, from_json_string
    - EmailContext: construction, message_id validation
    - DraftReply: Re: prefix enforcement, classmethod helpers
    - OrchestratorState: serialization round-trip, record_decision/error, prune
    - DecisionLogEntry: to_jsonl_line serialization
"""

import json

import pytest
from pydantic import ValidationError

from orchestrator.models import (
    DecisionLogEntry,
    DraftReply,
    EmailContext,
    LLMDecision,
    OrchestratorState,
)


# =============================================================================
# LLMDecision — core triage output model
# =============================================================================

class TestLLMDecision:

    def test_valid_archive_decision(self):
        d = LLMDecision(decision="archive", confidence=0.9, reasoning="Newsletter, no action.")
        assert d.decision == "archive"
        assert d.confidence == 0.9
        assert d.reasoning == "Newsletter, no action."

    def test_valid_draft_reply_with_body(self):
        d = LLMDecision(
            decision="draft_reply",
            confidence=0.8,
            reasoning="Needs a response.",
            reply_body="Hi Sarah, thanks for reaching out.",
        )
        assert d.decision == "draft_reply"
        assert d.reply_body == "Hi Sarah, thanks for reaching out."

    def test_valid_delegate_with_target(self):
        d = LLMDecision(
            decision="delegate",
            confidence=0.7,
            reasoning="Outside my scope.",
            delegation_target="Engineering Manager",
        )
        assert d.delegation_target == "Engineering Manager"

    def test_valid_needs_info_with_info_needed(self):
        d = LLMDecision(
            decision="needs_info",
            confidence=0.6,
            reasoning="Missing context.",
            info_needed="Which product line does this refer to?",
        )
        assert d.info_needed == "Which product line does this refer to?"

    def test_valid_urgent_decision(self):
        d = LLMDecision(decision="urgent", confidence=1.0, reasoning="Payment overdue alert.")
        assert d.decision == "urgent"

    def test_confidence_at_zero_boundary(self):
        d = LLMDecision(decision="archive", confidence=0.0, reasoning="Low confidence test.")
        assert d.confidence == 0.0

    def test_confidence_at_one_boundary(self):
        d = LLMDecision(decision="archive", confidence=1.0, reasoning="High confidence test.")
        assert d.confidence == 1.0

    def test_confidence_below_zero_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            LLMDecision(decision="archive", confidence=-0.01, reasoning="Test.")

    def test_confidence_above_one_raises(self):
        with pytest.raises(ValidationError, match="confidence"):
            LLMDecision(decision="archive", confidence=1.01, reasoning="Test.")

    def test_empty_reasoning_raises(self):
        with pytest.raises(ValidationError, match="reasoning"):
            LLMDecision(decision="archive", confidence=0.5, reasoning="")

    def test_whitespace_only_reasoning_raises(self):
        with pytest.raises(ValidationError, match="reasoning"):
            LLMDecision(decision="archive", confidence=0.5, reasoning="   ")

    def test_reasoning_is_stripped(self):
        d = LLMDecision(decision="archive", confidence=0.5, reasoning="  hello  ")
        assert d.reasoning == "hello"

    def test_delegate_without_target_raises(self):
        with pytest.raises(ValidationError, match="delegation_target"):
            LLMDecision(
                decision="delegate",
                confidence=0.7,
                reasoning="Outside scope.",
                delegation_target=None,
            )

    def test_needs_info_without_info_needed_raises(self):
        with pytest.raises(ValidationError, match="info_needed"):
            LLMDecision(
                decision="needs_info",
                confidence=0.5,
                reasoning="Missing context.",
                info_needed=None,
            )

    def test_invalid_decision_type_raises(self):
        with pytest.raises(ValidationError):
            LLMDecision(decision="forward", confidence=0.5, reasoning="Test.")

    def test_from_json_string_valid(self):
        raw = json.dumps({
            "decision": "archive",
            "confidence": 0.88,
            "reasoning": "Promotional email.",
        })
        d = LLMDecision.from_json_string(raw)
        assert d.decision == "archive"
        assert d.confidence == 0.88

    def test_from_json_string_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            LLMDecision.from_json_string("not valid json")

    def test_from_json_string_invalid_schema_raises(self):
        raw = json.dumps({"decision": "archive"})  # missing confidence + reasoning
        with pytest.raises(ValidationError):
            LLMDecision.from_json_string(raw)

    def test_model_is_frozen(self):
        d = LLMDecision(decision="archive", confidence=0.9, reasoning="Test.")
        with pytest.raises(Exception):
            d.decision = "urgent"  # type: ignore[misc]


# =============================================================================
# EmailContext — input parsed from vault markdown files
# =============================================================================

class TestEmailContext:

    def test_minimal_valid_context(self):
        ctx = EmailContext(
            message_id="msg_001",
            sender="alice@example.com",
            subject="Test",
            body="Hello world.",
            classification="actionable",
            priority="standard",
            date_received="Thu, 19 Feb 2026 21:02:14 +0000",
        )
        assert ctx.message_id == "msg_001"
        assert ctx.has_attachments is False
        assert ctx.filepath is None

    def test_empty_message_id_raises(self):
        with pytest.raises(ValidationError, match="message_id"):
            EmailContext(
                message_id="",
                sender="alice@example.com",
                subject="Test",
                body="Hello.",
                classification="actionable",
                priority="standard",
                date_received="Thu, 19 Feb 2026 21:02:14 +0000",
            )

    def test_whitespace_message_id_raises(self):
        with pytest.raises(ValidationError, match="message_id"):
            EmailContext(
                message_id="   ",
                sender="alice@example.com",
                subject="Test",
                body="Hello.",
                classification="actionable",
                priority="standard",
                date_received="Thu, 19 Feb 2026 21:02:14 +0000",
            )

    def test_message_id_is_stripped(self):
        ctx = EmailContext(
            message_id="  msg_001  ",
            sender="alice@example.com",
            subject="Test",
            body="Hello.",
            classification="actionable",
            priority="standard",
            date_received="Thu, 19 Feb 2026 21:02:14 +0000",
        )
        assert ctx.message_id == "msg_001"

    def test_has_attachments_defaults_false(self):
        ctx = EmailContext(
            message_id="msg_002",
            sender="bob@example.com",
            subject="No attachments",
            body="Body here.",
            classification="informational",
            priority="standard",
            date_received="Fri, 20 Feb 2026 10:00:00 +0000",
        )
        assert ctx.has_attachments is False

    def test_filepath_optional(self):
        ctx = EmailContext(
            message_id="msg_003",
            sender="carol@example.com",
            subject="With path",
            body="Body.",
            classification="actionable",
            priority="urgent",
            date_received="Sat, 21 Feb 2026 12:00:00 +0000",
            filepath="/vault/Needs_Action/msg_003.md",
        )
        assert ctx.filepath == "/vault/Needs_Action/msg_003.md"


# =============================================================================
# DraftReply — reply draft written to vault/Drafts/
# =============================================================================

class TestDraftReply:

    def test_re_prefix_added_when_missing(self):
        dr = DraftReply(
            source_message_id="msg_001",
            to="alice@example.com",
            subject="Product Updates",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-19T21:00:00+00:00",
            reply_body="Hi Alice, thanks for the update.",
        )
        assert dr.subject == "Re: Product Updates"

    def test_re_prefix_not_duplicated(self):
        dr = DraftReply(
            source_message_id="msg_001",
            to="alice@example.com",
            subject="Re: Product Updates",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-19T21:00:00+00:00",
            reply_body="Already has Re: prefix.",
        )
        assert dr.subject == "Re: Product Updates"
        assert not dr.subject.startswith("Re: Re:")

    def test_re_case_insensitive_check(self):
        dr = DraftReply(
            source_message_id="msg_002",
            to="bob@example.com",
            subject="re: Lowercase prefix",
            drafted_by="anthropic:claude-sonnet-4-20250514",
            drafted_at="2026-02-19T21:00:00+00:00",
            reply_body="Lowercase re: should not get doubled.",
        )
        assert not dr.subject.lower().startswith("re: re:")

    def test_defaults(self):
        dr = DraftReply(
            source_message_id="msg_003",
            to="carol@example.com",
            subject="Test",
            drafted_by="openai:gpt-4o-mini",
            drafted_at="2026-02-20T10:00:00+00:00",
            reply_body="Default check.",
        )
        assert dr.type == "draft_reply"
        assert dr.status == "pending_approval"

    def test_now_iso_returns_string(self):
        ts = DraftReply.now_iso()
        assert isinstance(ts, str)
        assert "T" in ts  # ISO 8601 format


# =============================================================================
# OrchestratorState — persistent run state
# =============================================================================

class TestOrchestratorState:

    def test_empty_defaults(self):
        s = OrchestratorState()
        assert s.processed_ids == []
        assert s.error_counts == {}
        assert s.decision_counts == {}
        assert s.last_run is None
        assert s.total_tokens_used == 0
        assert s.total_emails_processed == 0

    def test_record_decision(self):
        s = OrchestratorState()
        s.record_decision("archive")
        s.record_decision("archive")
        s.record_decision("draft_reply")
        assert s.decision_counts["archive"] == 2
        assert s.decision_counts["draft_reply"] == 1

    def test_record_error(self):
        s = OrchestratorState()
        s.record_error("json_decode_error")
        s.record_error("json_decode_error")
        assert s.error_counts["json_decode_error"] == 2

    def test_prune_processed_ids(self):
        s = OrchestratorState()
        s.processed_ids = [f"id_{i}" for i in range(200)]
        s.prune_processed_ids(max_ids=100)
        assert len(s.processed_ids) == 100
        assert s.processed_ids[0] == "id_100"  # FIFO — oldest pruned

    def test_prune_no_op_under_limit(self):
        s = OrchestratorState()
        s.processed_ids = ["a", "b", "c"]
        s.prune_processed_ids(max_ids=100)
        assert len(s.processed_ids) == 3

    def test_to_json_round_trip(self):
        s = OrchestratorState()
        s.processed_ids = ["msg_001", "msg_002"]
        s.record_decision("archive")
        s.total_tokens_used = 1234
        json_str = s.to_json()
        s2 = OrchestratorState.from_json(json_str)
        assert s2.processed_ids == ["msg_001", "msg_002"]
        assert s2.decision_counts == {"archive": 1}
        assert s2.total_tokens_used == 1234

    def test_from_json_invalid_returns_empty(self):
        s = OrchestratorState.from_json("not valid json")
        assert s.processed_ids == []
        assert s.total_tokens_used == 0


# =============================================================================
# DecisionLogEntry — JSONL audit log entries
# =============================================================================

class TestDecisionLogEntry:

    def test_to_jsonl_line(self):
        entry = DecisionLogEntry(
            timestamp="2026-02-19T21:00:00+00:00",
            event="llm_decision",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            email_message_id="msg_001",
            email_subject="Test Subject",
            decision="archive",
            confidence=0.9,
            reasoning="Newsletter.",
            tokens_input=500,
            tokens_output=120,
            latency_ms=1200,
        )
        line = entry.to_jsonl_line()
        assert isinstance(line, str)
        parsed = json.loads(line)
        assert parsed["event"] == "llm_decision"
        assert parsed["provider"] == "anthropic"
        assert parsed["decision"] == "archive"
        assert "\n" not in line  # must be a single line

    def test_defaults(self):
        entry = DecisionLogEntry(
            timestamp="2026-02-19T21:00:00+00:00",
            event="poll_cycle_complete",
            provider="anthropic",
            model="claude-sonnet-4-20250514",
        )
        assert entry.email_message_id == ""
        assert entry.iteration == 1
        assert entry.severity == "info"
        assert entry.retry_count == 0
        assert entry.error_type is None

    def test_now_iso_format(self):
        ts = DecisionLogEntry.now_iso()
        assert isinstance(ts, str)
        assert "T" in ts
