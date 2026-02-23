"""Unit tests for orchestrator/prompts.py — prompt engineering functions.

Tests validate:
    - build_system_prompt(): contains JSON schema, financial safety rule, decision types
    - build_user_message(): includes all email metadata fields and body
    - build_correction_prompt(): includes error and original response
    - estimate_tokens(): accurate within 20% of known counts
    - truncate_body(): appends notice when truncated; no-op when under budget
    - prepare_body_for_context(): applies full budget pipeline
"""

import pytest

from orchestrator.models import EmailContext
from orchestrator.prompts import (
    build_correction_prompt,
    build_system_prompt,
    build_user_message,
    estimate_tokens,
    prepare_body_for_context,
    truncate_body,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _make_context(**overrides) -> EmailContext:
    defaults = dict(
        message_id="msg_001",
        sender="alice@example.com",
        subject="Q1 Report Review",
        body="Hi, please review the attached Q1 report.",
        classification="actionable",
        priority="standard",
        date_received="Thu, 19 Feb 2026 21:02:14 +0000",
        has_attachments=False,
    )
    defaults.update(overrides)
    return EmailContext(**defaults)


# ---------------------------------------------------------------------------
# build_system_prompt()
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:

    def test_contains_all_five_decision_types(self):
        prompt = build_system_prompt()
        for decision in ("draft_reply", "needs_info", "archive", "urgent", "delegate"):
            assert decision in prompt, f"'{decision}' not found in system prompt"

    def test_contains_json_schema_fields(self):
        prompt = build_system_prompt()
        for field in ("decision", "confidence", "reasoning", "reply_body",
                      "delegation_target", "info_needed"):
            assert field in prompt, f"JSON field '{field}' not found in system prompt"

    def test_contains_financial_safety_rule(self):
        prompt = build_system_prompt()
        financial_keywords = ("payment", "invoice", "billing", "subscription", "charge", "refund")
        for kw in financial_keywords:
            assert kw in prompt, f"Financial keyword '{kw}' missing from system prompt"

    def test_financial_never_archive_constraint(self):
        prompt = build_system_prompt()
        assert "NEVER" in prompt or "never" in prompt
        assert "archive" in prompt

    def test_respond_only_json_instruction(self):
        prompt = build_system_prompt()
        # Prompt must instruct LLM to respond only with JSON
        assert "ONLY" in prompt or "only" in prompt
        assert "JSON" in prompt

    def test_confidence_range_specified(self):
        prompt = build_system_prompt()
        assert "0.0" in prompt and "1.0" in prompt

    def test_returns_non_empty_string(self):
        prompt = build_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_idempotent(self):
        """Multiple calls return identical prompt text."""
        assert build_system_prompt() == build_system_prompt()


# ---------------------------------------------------------------------------
# build_user_message()
# ---------------------------------------------------------------------------

class TestBuildUserMessage:

    def test_includes_sender(self):
        ctx = _make_context(sender="bob@example.com")
        msg = build_user_message(ctx)
        assert "bob@example.com" in msg

    def test_includes_subject(self):
        ctx = _make_context(subject="Important Update")
        msg = build_user_message(ctx)
        assert "Important Update" in msg

    def test_includes_date(self):
        ctx = _make_context(date_received="Mon, 20 Feb 2026 10:00:00 +0000")
        msg = build_user_message(ctx)
        assert "Mon, 20 Feb 2026" in msg

    def test_includes_body(self):
        ctx = _make_context(body="Please review by Friday.")
        msg = build_user_message(ctx)
        assert "Please review by Friday." in msg

    def test_truncated_body_override(self):
        ctx = _make_context(body="Original body that should not appear.")
        msg = build_user_message(ctx, truncated_body="Truncated version.")
        assert "Truncated version." in msg
        assert "Original body" not in msg

    def test_includes_classification(self):
        ctx = _make_context(classification="informational")
        msg = build_user_message(ctx)
        assert "informational" in msg

    def test_empty_body_handled(self):
        ctx = _make_context(body="")
        msg = build_user_message(ctx)
        assert "Email Body" in msg  # section header still present


# ---------------------------------------------------------------------------
# build_correction_prompt()
# ---------------------------------------------------------------------------

class TestBuildCorrectionPrompt:

    def test_includes_error_message(self):
        prompt = build_correction_prompt("JSONDecodeError: line 1")
        assert "JSONDecodeError: line 1" in prompt

    def test_includes_original_response(self):
        prompt = build_correction_prompt("Schema error", original_response="Sure, here you go!")
        assert "Sure, here you go!" in prompt

    def test_without_original_response(self):
        prompt = build_correction_prompt("Bad JSON")
        assert "Bad JSON" in prompt
        assert isinstance(prompt, str)

    def test_instructs_json_only(self):
        prompt = build_correction_prompt("error")
        assert "JSON" in prompt

    def test_long_original_response_capped(self):
        """Very long original response should be capped to avoid prompt bloat."""
        long_response = "x" * 10000
        prompt = build_correction_prompt("error", long_response)
        # The prompt should not include the full 10000 chars
        assert len(prompt) < 2000


# ---------------------------------------------------------------------------
# estimate_tokens()
# ---------------------------------------------------------------------------

class TestEstimateTokens:

    def test_empty_string_returns_zero(self):
        assert estimate_tokens("") == 0

    def test_known_length_within_20_percent(self):
        # 400 chars ÷ 4 = 100 tokens; real tokenizers typically give 80-120 for English text
        text = "a" * 400
        estimate = estimate_tokens(text)
        assert 80 <= estimate <= 120, f"estimate {estimate} outside 20% range for 400 chars"

    def test_proportional_scaling(self):
        short = estimate_tokens("hello world")
        long = estimate_tokens("hello world " * 100)
        assert long > short * 50, "long text should estimate much more tokens"

    def test_minimum_one_token_for_nonempty(self):
        assert estimate_tokens("a") >= 1


# ---------------------------------------------------------------------------
# truncate_body()
# ---------------------------------------------------------------------------

class TestTruncateBody:

    def test_no_truncation_under_budget(self):
        body = "Short body"
        result, was_truncated = truncate_body(body, remaining_budget_tokens=500)
        assert result == body
        assert was_truncated is False

    def test_truncation_when_over_budget(self):
        body = "word " * 2000  # ~2500 tokens
        result, was_truncated = truncate_body(body, remaining_budget_tokens=100)
        assert was_truncated is True
        assert len(result) < len(body)

    def test_truncation_notice_appended(self):
        body = "x " * 2000
        result, _ = truncate_body(body, remaining_budget_tokens=50)
        assert "TRUNCATED" in result

    def test_empty_body_not_truncated(self):
        result, was_truncated = truncate_body("", remaining_budget_tokens=100)
        assert result == ""
        assert was_truncated is False

    def test_exactly_at_budget_not_truncated(self):
        body = "a" * 400   # exactly 100 tokens
        result, was_truncated = truncate_body(body, remaining_budget_tokens=100)
        assert was_truncated is False


# ---------------------------------------------------------------------------
# prepare_body_for_context()
# ---------------------------------------------------------------------------

class TestPrepareBodyForContext:

    def test_short_body_not_truncated(self):
        system = build_system_prompt()
        ctx = _make_context(body="Short body.")
        meta_msg = build_user_message(ctx, truncated_body="")
        body, truncated = prepare_body_for_context(system, meta_msg, "Short body.")
        assert truncated is False
        assert "Short body." in body

    def test_huge_body_is_truncated(self):
        system = build_system_prompt()
        ctx = _make_context(body="x")
        meta_msg = build_user_message(ctx, truncated_body="")
        huge_body = "word " * 5000   # ~6250 tokens — well over 4000 budget
        body, truncated = prepare_body_for_context(system, meta_msg, huge_body)
        assert truncated is True
        assert "TRUNCATED" in body
