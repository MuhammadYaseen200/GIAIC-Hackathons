"""Unit tests for the Ralph Wiggum retry loop in RalphWiggumOrchestrator.

Tests validate (T020):
    - invalid JSON on first attempt → correction prompt sent on retry
    - invalid JSON on all max_iterations → email status=failed, processed_ids updated
    - valid JSON on 2nd attempt → success with iteration_count=2 in frontmatter
    - invalid decision value (e.g. "maybe") triggers retry (Pydantic validation)
    - valid JSON with out-of-range confidence triggers retry
    - correction prompt includes original bad response text
    - error count tracked in OrchestratorState.error_counts on exhaustion
"""

import json
from pathlib import Path

import pytest

from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider as LLMProviderBase
from orchestrator.vault_ops import read_email_context


# ---------------------------------------------------------------------------
# Sequential Mock Provider — different response per call
# ---------------------------------------------------------------------------

class _SequentialMockProvider(LLMProviderBase):
    """Returns a canned response for each successive call.

    Tracks every (system_prompt, user_message) pair for assertion.
    """

    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self._call_index = 0
        self.calls: list[tuple[str, str]] = []  # (system_prompt, user_message)

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        self.calls.append((system_prompt, user_message))
        # Cycle to last response if more calls than configured responses
        idx = min(self._call_index, len(self._responses) - 1)
        resp = self._responses[self._call_index] if self._call_index < len(self._responses) else self._responses[-1]
        self._call_index += 1
        return (resp, 50, 30)

    def provider_name(self) -> str:
        return "mock"

    def model_name(self) -> str:
        return "mock-model"


# ---------------------------------------------------------------------------
# Canned responses
# ---------------------------------------------------------------------------

def _valid_archive_json() -> str:
    return json.dumps({
        "decision": "archive",
        "confidence": 0.9,
        "reasoning": "Promotional newsletter — no action required.",
    })


def _valid_needs_info_json() -> str:
    """Valid decision that does NOT move the source file (stays in Needs_Action/)."""
    return json.dumps({
        "decision": "needs_info",
        "confidence": 0.7,
        "reasoning": "Need more context before deciding.",
        "info_needed": "Which product line does this refer to?",
    })


def _invalid_json() -> str:
    return "this is not json at all"


def _valid_json_bad_decision() -> str:
    """Valid JSON structure but decision field has an unsupported value."""
    return json.dumps({
        "decision": "maybe",
        "confidence": 0.5,
        "reasoning": "I am not sure.",
    })


def _valid_json_bad_confidence() -> str:
    """Valid JSON structure but confidence is out of range."""
    return json.dumps({
        "decision": "archive",
        "confidence": 2.5,  # must be 0.0–1.0
        "reasoning": "Out of range confidence.",
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_orchestrator(
    provider: _SequentialMockProvider,
    vault_path: Path,
    max_iterations: int = 5,
) -> RalphWiggumOrchestrator:
    return RalphWiggumOrchestrator(
        provider=provider,
        poll_interval=30,
        vault_path=str(vault_path),
        max_iterations=max_iterations,
    )


def _parse_frontmatter(path: Path) -> dict:
    import yaml
    content = path.read_text(encoding="utf-8")
    fm_text = content.split("---\n")[1]
    return yaml.safe_load(fm_text) or {}


# ---------------------------------------------------------------------------
# T020: correction prompt sent on invalid JSON
# ---------------------------------------------------------------------------

class TestCorrectionPromptOnRetry:

    @pytest.mark.asyncio
    async def test_provider_called_twice_on_first_invalid(self, tmp_vault_dir, mock_email_file):
        """First call returns invalid JSON; second call should happen (correction attempt)."""
        provider = _SequentialMockProvider([_invalid_json(), _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert provider._call_index == 2, "Expected exactly 2 LLM calls (1 failure + 1 success)"

    @pytest.mark.asyncio
    async def test_correction_prompt_sent_as_user_message(self, tmp_vault_dir, mock_email_file):
        """The second call's user_message must be a correction prompt, not the original."""
        provider = _SequentialMockProvider([_invalid_json(), _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        # The second call receives the correction prompt
        second_user_msg = provider.calls[1][1]
        assert "not valid JSON" in second_user_msg or "previous response" in second_user_msg.lower()

    @pytest.mark.asyncio
    async def test_correction_prompt_includes_original_bad_response(self, tmp_vault_dir, mock_email_file):
        """build_correction_prompt embeds up to 500 chars of the bad response."""
        bad_response = _invalid_json()
        provider = _SequentialMockProvider([bad_response, _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        second_user_msg = provider.calls[1][1]
        # The original bad response (or a prefix) must appear in the correction prompt
        assert bad_response[:100] in second_user_msg


# ---------------------------------------------------------------------------
# T020: all iterations exhausted → email marked failed
# ---------------------------------------------------------------------------

class TestAllIterationsExhausted:

    @pytest.mark.asyncio
    async def test_email_status_set_to_failed(self, tmp_vault_dir, mock_email_file):
        """After max_iterations bad responses, original email status must be 'failed'."""
        provider = _SequentialMockProvider([_invalid_json()] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["status"] == "failed"

    @pytest.mark.asyncio
    async def test_message_id_added_to_processed_ids_on_failure(self, tmp_vault_dir, mock_email_file):
        """Even on failure, message_id must be tracked to prevent re-processing."""
        provider = _SequentialMockProvider([_invalid_json()] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert ctx.message_id in orch.state.processed_ids

    @pytest.mark.asyncio
    async def test_error_count_tracked_in_orch_state(self, tmp_vault_dir, mock_email_file):
        """OrchestratorState.error_counts must record MaxIterationsExceeded."""
        provider = _SequentialMockProvider([_invalid_json()] * 3)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert orch._orch_state.error_counts.get("MaxIterationsExceeded", 0) == 1

    @pytest.mark.asyncio
    async def test_exact_max_iterations_calls_made(self, tmp_vault_dir, mock_email_file):
        """Provider must be called exactly max_iterations times, then stop."""
        provider = _SequentialMockProvider([_invalid_json()] * 10)
        orch = _make_orchestrator(provider, tmp_vault_dir, max_iterations=3)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert provider._call_index == 3


# ---------------------------------------------------------------------------
# T020: valid JSON on 2nd attempt → iteration_count=2
# ---------------------------------------------------------------------------

class TestSuccessOnRetry:

    @pytest.mark.asyncio
    async def test_iteration_count_2_on_second_attempt(self, tmp_vault_dir, mock_email_file):
        """Successful parse on iteration 2 must write iteration_count=2 to frontmatter.

        Uses needs_info (not archive) so the file stays in Needs_Action/ for reading.
        """
        provider = _SequentialMockProvider([_invalid_json(), _valid_needs_info_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        fm = _parse_frontmatter(mock_email_file)
        assert fm["iteration_count"] == 2

    @pytest.mark.asyncio
    async def test_decision_applied_after_retry(self, tmp_vault_dir, mock_email_file):
        """Even though 1st call failed, the decision from 2nd call must be applied correctly."""
        provider = _SequentialMockProvider([_invalid_json(), _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        # archive decision: file moved to Done/
        assert not mock_email_file.exists()
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1


# ---------------------------------------------------------------------------
# T020: Pydantic validation failure triggers retry
# ---------------------------------------------------------------------------

class TestPydanticValidationRetry:

    @pytest.mark.asyncio
    async def test_invalid_decision_value_triggers_retry(self, tmp_vault_dir, mock_email_file):
        """JSON with decision='maybe' fails Pydantic validation → retry triggered."""
        provider = _SequentialMockProvider([_valid_json_bad_decision(), _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        # Should have taken 2 attempts
        assert provider._call_index == 2
        # archive decision applied on 2nd call: file moved to Done/
        done_files = list((tmp_vault_dir / "Done").glob("*.md"))
        assert len(done_files) == 1

    @pytest.mark.asyncio
    async def test_out_of_range_confidence_triggers_retry(self, tmp_vault_dir, mock_email_file):
        """JSON with confidence=2.5 fails Pydantic field_validator → retry triggered."""
        provider = _SequentialMockProvider([_valid_json_bad_confidence(), _valid_archive_json()])
        orch = _make_orchestrator(provider, tmp_vault_dir)
        ctx = read_email_context(mock_email_file)

        await orch.process_item(ctx)

        assert provider._call_index == 2
