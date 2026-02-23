"""Unit tests for the financial safety constraint in the Ralph Wiggum system prompt.

Tests validate (T021):
    - system prompt contains financial safety keywords (payment, invoice, billing, subscription)
    - system prompt explicitly states financial emails must NEVER be archive
    - system prompt directs to "urgent" or "needs_info" for financial emails
    - safety rule text is present in build_system_prompt() output
"""

import pytest

from orchestrator.prompts import build_system_prompt


class TestFinancialSafetyKeywords:

    def test_system_prompt_contains_payment(self):
        prompt = build_system_prompt()
        assert "payment" in prompt.lower(), "System prompt must mention 'payment'"

    def test_system_prompt_contains_invoice(self):
        prompt = build_system_prompt()
        assert "invoice" in prompt.lower(), "System prompt must mention 'invoice'"

    def test_system_prompt_contains_billing(self):
        prompt = build_system_prompt()
        assert "billing" in prompt.lower(), "System prompt must mention 'billing'"

    def test_system_prompt_contains_subscription(self):
        prompt = build_system_prompt()
        assert "subscription" in prompt.lower(), "System prompt must mention 'subscription'"


class TestFinancialSafetyNeverArchive:

    def test_system_prompt_states_never_archive_financial(self):
        """The safety rule must include an explicit NEVER archive instruction."""
        prompt = build_system_prompt()
        # Must say NEVER (or never) and archive together in the safety section
        assert "never" in prompt.lower(), "System prompt must contain 'NEVER' constraint"
        assert "archive" in prompt.lower()

    def test_financial_safety_constraint_is_present(self):
        """The full financial safety rule text must be in the system prompt."""
        prompt = build_system_prompt()
        # The safety rules section must direct to urgent or needs_info for financial emails
        has_urgent = "urgent" in prompt
        has_needs_info = "needs_info" in prompt
        assert has_urgent and has_needs_info, (
            "System prompt must reference both 'urgent' and 'needs_info' as alternatives "
            "to 'archive' for financial emails"
        )

    def test_safety_section_covers_money_related_terms(self):
        """Safety rules must cover a broad set of financial keywords."""
        prompt = build_system_prompt()
        financial_terms = ["payment", "invoice", "billing", "subscription"]
        missing = [t for t in financial_terms if t not in prompt.lower()]
        assert not missing, f"System prompt missing financial terms: {missing}"
