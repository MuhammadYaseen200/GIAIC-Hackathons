"""Unit tests for RalphWiggumOrchestrator.process_item() — all 5 decision types.

Tests validate (T018):
    - draft_reply: draft created, status=pending_approval, draft_path in frontmatter
    - needs_info: status=needs_info, info note appended to body
    - archive: status=done, file moved to Done/
    - urgent: status=pending_approval, priority=urgent, draft created (when reply_body present)
    - delegate: status=pending_approval, delegation note appended to body
    - ALL decisions: decided_by, decided_at, decision fields written to frontmatter

Tests validate (T019):
    - validate_prerequisites() creates vault/Drafts/ if absent
    - validate_prerequisites() is idempotent (existing Drafts/ not destroyed)
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from orchestrator.vault_ops import read_email_context


# ---------------------------------------------------------------------------
# Mock LLM Provider
# ---------------------------------------------------------------------------

class _MockProvider(LLMProviderBase):
    """Test double for LLMProvider — returns canned JSON."""

    def __init__(self, response_json: str) -> None:
        self._response = response_json
        self.calls: list[tuple[str, str]] = []

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        self.calls.append((system_prompt, user_message))
        return (self._response, 200, 60)

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


def _mock_draft_reply() -> str:
    return json.dumps({
        "decision": "draft_reply",
        "confidence": 0.9,
        "reasoning": "Email requires a professional response.",
        "reply_body": "Hi Sarah, thank you for your message. We will review the timeline.",
    })


def _mock_needs_info() -> str:
    return json.dumps({
        "decision": "needs_info",
        "confidence": 0.6,
        "reasoning": "Cannot triage without knowing which product line.",
        "info_needed": "Which specific product line and milestone are you referring to?",
    })


def _mock_archive() -> str:
    return json.dumps({
        "decision": "archive",
        "confidence": 0.92,
        "reasoning": "Promotional newsletter — no action required.",
    })


def _mock_urgent() -> str:
    return json.dumps({
        "decision": "urgent",
        "confidence": 0.97,
        "reasoning": "Overdue payment — immediate attention needed.",
        "reply_body": "We acknowledge your payment notice and will act immediately.",
    })


def _mock_delegate() -> str:
    return json.dumps({
        "decision": "delegate",
        "confidence": 0.78,
        "reasoning": "Infrastructure decisions belong to Engineering.",
        "delegation_target": "Engineering Manager — infrastructure procurement is their domain.",
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(provider: _MockProvider, vault_path: Path) -> RalphWiggumOrchestrator:
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
    )


def _parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    fm_text = content.split("---\n")[1]
    return yaml.safe_load(fm_text) or {}


def _file_body(path: Path) -> str:
    content = path.read_text(encoding="utf-8")
    parts = content.split("---\n", 2)
    return parts[2] if len(parts) > 2 else ""


# ---------------------------------------------------------------------------
# T018: process_item — draft_reply
# ---------------------------------------------------------------------------

class TestDraftReplyDecision:

    @pytest.mark.asyncio
    async def test_draft_file_created(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_draft_reply())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        drafts = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert len(drafts) == 1, "Expected 1 draft file after draft_reply decision"

    @pytest.mark.asyncio
    async def test_status_set_to_pending_approval(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_draft_reply())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_draft_path_in_original_frontmatter(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_draft_reply())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert "draft_path" in fm
        assert "draft_" in str(fm["draft_path"])

    @pytest.mark.asyncio
    async def test_decision_fields_in_frontmatter(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_draft_reply())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["decision"] == "draft_reply"
        assert "decided_by" in fm
        assert "mock" in str(fm["decided_by"])
        assert "decided_at" in fm
        assert "iteration_count" in fm


# ---------------------------------------------------------------------------
# T018: process_item — needs_info
# ---------------------------------------------------------------------------

class TestNeedsInfoDecision:

    @pytest.mark.asyncio
    async def test_status_set_to_needs_info(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_needs_info())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["status"] == "needs_info"

    @pytest.mark.asyncio
    async def test_info_needed_appended_to_body(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_needs_info())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        body = _file_body(mock_email_file)
        assert "product line" in body  # from info_needed text

    @pytest.mark.asyncio
    async def test_no_draft_created(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_needs_info())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        drafts = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert drafts == []

    @pytest.mark.asyncio
    async def test_decision_fields_in_frontmatter(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_needs_info())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["decision"] == "needs_info"
        assert "decided_by" in fm
        assert "decided_at" in fm


# ---------------------------------------------------------------------------
# T018: process_item — archive
# ---------------------------------------------------------------------------

class TestArchiveDecision:

    @pytest.mark.asyncio
    async def test_file_moved_to_done(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_archive())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert not mock_email_file.exists(), "Original file should be moved out of Needs_Action"
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1

    @pytest.mark.asyncio
    async def test_done_file_has_status_done(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_archive())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        fm = _parse_frontmatter(done_files[0])
        assert fm["status"] == "done"

    @pytest.mark.asyncio
    async def test_decision_fields_in_done_file(self, tmp_vault_dir, mock_email_file):
        """Decision fields must be written before the file is moved (archive)."""
        provider = _MockProvider(_mock_archive())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        fm = _parse_frontmatter(done_files[0])
        assert fm["decision"] == "archive"
        assert "decided_by" in fm
        assert "decided_at" in fm

    @pytest.mark.asyncio
    async def test_no_draft_created(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_archive())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        drafts = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert drafts == []


# ---------------------------------------------------------------------------
# T018: process_item — urgent
# ---------------------------------------------------------------------------

class TestUrgentDecision:

    @pytest.mark.asyncio
    async def test_status_pending_approval(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_urgent())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_priority_set_to_urgent(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_urgent())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["priority"] == "urgent"

    @pytest.mark.asyncio
    async def test_draft_created_when_reply_body_present(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_urgent())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        drafts = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert len(drafts) == 1


# ---------------------------------------------------------------------------
# T018: process_item — delegate
# ---------------------------------------------------------------------------

class TestDelegateDecision:

    @pytest.mark.asyncio
    async def test_status_pending_approval(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_delegate())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["status"] == "pending_approval"

    @pytest.mark.asyncio
    async def test_delegation_note_appended_to_body(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_delegate())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        body = _file_body(mock_email_file)
        assert "Engineering Manager" in body  # from delegation_target

    @pytest.mark.asyncio
    async def test_no_draft_created(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_delegate())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        drafts = list((tmp_vault_dir / "Drafts").glob("*.md"))
        assert drafts == []

    @pytest.mark.asyncio
    async def test_decision_fields_in_frontmatter(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_delegate())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["decision"] == "delegate"
        assert "decided_by" in fm
        assert "decided_at" in fm


# ---------------------------------------------------------------------------
# T018: message_id added to processed_ids after any decision
# ---------------------------------------------------------------------------

class TestProcessedTracking:

    @pytest.mark.asyncio
    async def test_message_id_tracked_after_draft_reply(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_draft_reply())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert ctx.message_id in orch.state.processed_ids

    @pytest.mark.asyncio
    async def test_message_id_tracked_after_archive(self, tmp_vault_dir, mock_email_file):
        provider = _MockProvider(_mock_archive())
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert ctx.message_id in orch.state.processed_ids


# ---------------------------------------------------------------------------
# T019: vault/Drafts/ auto-creation by validate_prerequisites()
# ---------------------------------------------------------------------------

class TestDraftsDirectoryAutoCreation:

    def test_creates_drafts_dir_if_absent(self, tmp_vault_dir, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        # Remove Drafts/ so it doesn't exist
        drafts_dir = tmp_vault_dir / "Drafts"
        if drafts_dir.exists():
            drafts_dir.rmdir()
        assert not drafts_dir.exists()

        provider = _MockProvider("{}")
        orch = _make_orchestrator(provider, tmp_vault_dir)
        orch.validate_prerequisites()

        assert drafts_dir.exists()

    def test_validate_prerequisites_idempotent(self, tmp_vault_dir, monkeypatch):
        """Calling validate_prerequisites() twice should not fail."""
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        drafts_dir = tmp_vault_dir / "Drafts"
        drafts_dir.mkdir(exist_ok=True)

        provider = _MockProvider("{}")
        orch = _make_orchestrator(provider, tmp_vault_dir)
        orch.validate_prerequisites()
        orch.validate_prerequisites()  # second call should not raise

        assert drafts_dir.exists()

    def test_validate_prerequisites_fails_without_needs_action(self, tmp_path, monkeypatch):
        from watchers.utils import PrerequisiteError
        monkeypatch.setenv("LLM_PROVIDER", "mock")
        # Create vault WITHOUT Needs_Action
        vault = tmp_path / "vault"
        vault.mkdir()
        (vault / "Done").mkdir()

        provider = _MockProvider("{}")
        orch = _make_orchestrator(provider, vault)
        with pytest.raises(PrerequisiteError, match="Needs_Action"):
            orch.validate_prerequisites()
