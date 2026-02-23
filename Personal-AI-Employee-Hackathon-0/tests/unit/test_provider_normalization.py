"""Unit tests for cross-provider interface normalization.

Tests validate (T022):
    - AnthropicAdapter and OpenAICompatibleAdapter both return identical (str, int, int) tuple
    - Both adapters produce output parseable into valid LLMDecision via Pydantic
    - provider_name() and model_name() do NOT contain API key text
    - Both adapters accept the same (system_prompt, user_message) input signature
    - Correct SDK methods called: Anthropic → messages.create(), OpenAI → chat.completions.create()
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from orchestrator.models import LLMDecision
from orchestrator.providers.anthropic_adapter import AnthropicAdapter
from orchestrator.providers.openai_compatible_adapter import OpenAICompatibleAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = "You are a test assistant."
_USER_MESSAGE = "Classify this email."

_VALID_DECISION_JSON = json.dumps({
    "decision": "archive",
    "confidence": 0.9,
    "reasoning": "Promotional newsletter.",
})


def _make_anthropic_mock_response(text: str, in_tok: int, out_tok: int) -> MagicMock:
    response = MagicMock()
    response.content = [MagicMock(text=text)]
    response.usage = MagicMock(input_tokens=in_tok, output_tokens=out_tok)
    return response


def _make_openai_mock_response(text: str, prompt_tok: int, completion_tok: int) -> MagicMock:
    response = MagicMock()
    response.choices = [MagicMock(message=MagicMock(content=text))]
    response.usage = MagicMock(prompt_tokens=prompt_tok, completion_tokens=completion_tok)
    return response


# ---------------------------------------------------------------------------
# T022: Both adapters return (str, int, int) tuple shape
# ---------------------------------------------------------------------------

class TestReturnTupleShape:

    @pytest.mark.asyncio
    async def test_anthropic_returns_str_int_int_tuple(self):
        mock_resp = _make_anthropic_mock_response(_VALID_DECISION_JSON, 100, 50)
        with patch("anthropic.AsyncAnthropic") as MockAnthropic:
            instance = AsyncMock()
            instance.messages.create = AsyncMock(return_value=mock_resp)
            MockAnthropic.return_value = instance

            adapter = AnthropicAdapter(api_key="sk-ant-test")
            result = await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        assert isinstance(result, tuple)
        assert len(result) == 3
        text, in_tok, out_tok = result
        assert isinstance(text, str)
        assert isinstance(in_tok, int)
        assert isinstance(out_tok, int)

    @pytest.mark.asyncio
    async def test_openai_compatible_returns_str_int_int_tuple(self):
        mock_resp = _make_openai_mock_response(_VALID_DECISION_JSON, 100, 50)
        with patch("openai.AsyncOpenAI") as MockOpenAI:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_resp)
            MockOpenAI.return_value = instance

            adapter = OpenAICompatibleAdapter(
                api_key="sk-test",
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                provider_key="openai",
            )
            result = await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        assert isinstance(result, tuple)
        assert len(result) == 3
        text, in_tok, out_tok = result
        assert isinstance(text, str)
        assert isinstance(in_tok, int)
        assert isinstance(out_tok, int)


# ---------------------------------------------------------------------------
# T022: Both adapters produce LLMDecision-parseable output
# ---------------------------------------------------------------------------

class TestOutputParsesIntoLLMDecision:

    @pytest.mark.asyncio
    async def test_anthropic_output_parses_to_llm_decision(self):
        mock_resp = _make_anthropic_mock_response(_VALID_DECISION_JSON, 100, 50)
        with patch("anthropic.AsyncAnthropic") as MockAnthropic:
            instance = AsyncMock()
            instance.messages.create = AsyncMock(return_value=mock_resp)
            MockAnthropic.return_value = instance

            adapter = AnthropicAdapter(api_key="sk-ant-test")
            text, _, _ = await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        decision = LLMDecision.from_json_string(text)
        assert decision.decision == "archive"

    @pytest.mark.asyncio
    async def test_openai_output_parses_to_llm_decision(self):
        mock_resp = _make_openai_mock_response(_VALID_DECISION_JSON, 100, 50)
        with patch("openai.AsyncOpenAI") as MockOpenAI:
            instance = AsyncMock()
            instance.chat.completions.create = AsyncMock(return_value=mock_resp)
            MockOpenAI.return_value = instance

            adapter = OpenAICompatibleAdapter(
                api_key="sk-test",
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                provider_key="openai",
            )
            text, _, _ = await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        decision = LLMDecision.from_json_string(text)
        assert decision.decision == "archive"


# ---------------------------------------------------------------------------
# T022: provider_name() and model_name() don't contain API key text
# ---------------------------------------------------------------------------

class TestProviderIdentityDoesNotLeakKeys:

    def test_anthropic_provider_name_has_no_api_key(self):
        adapter = AnthropicAdapter(api_key="sk-ant-supersecret123")
        name = adapter.provider_name()
        assert "sk-ant-supersecret123" not in name
        assert "sk-" not in name

    def test_anthropic_model_name_has_no_api_key(self):
        adapter = AnthropicAdapter(api_key="sk-ant-supersecret123")
        name = adapter.model_name()
        assert "sk-ant-supersecret123" not in name

    def test_openai_provider_name_has_no_api_key(self):
        adapter = OpenAICompatibleAdapter(
            api_key="sk-supersecret456",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            provider_key="openai",
        )
        name = adapter.provider_name()
        assert "sk-supersecret456" not in name

    def test_openai_model_name_has_no_api_key(self):
        adapter = OpenAICompatibleAdapter(
            api_key="sk-supersecret456",
            model="gpt-4o-mini",
            base_url="https://api.openai.com/v1",
            provider_key="openai",
        )
        name = adapter.model_name()
        assert "sk-supersecret456" not in name


# ---------------------------------------------------------------------------
# T022: Both adapters call their SDKs with the correct method/signature
# ---------------------------------------------------------------------------

class TestCorrectSdkMethodsCalled:

    @pytest.mark.asyncio
    async def test_anthropic_uses_messages_create_with_system_param(self):
        """Anthropic adapter must pass system_prompt as dedicated 'system' param."""
        mock_resp = _make_anthropic_mock_response(_VALID_DECISION_JSON, 80, 40)
        with patch("anthropic.AsyncAnthropic") as MockAnthropic:
            instance = AsyncMock()
            messages_create = AsyncMock(return_value=mock_resp)
            instance.messages.create = messages_create
            MockAnthropic.return_value = instance

            adapter = AnthropicAdapter(api_key="sk-ant-test")
            await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        _, kwargs = messages_create.call_args
        # Anthropic-specific: system is a separate top-level parameter
        assert "system" in kwargs or (messages_create.call_args[0] and False)
        call_args = messages_create.call_args
        all_kwargs = call_args.kwargs if hasattr(call_args, "kwargs") else call_args[1]
        assert all_kwargs.get("system") == _SYSTEM_PROMPT

    @pytest.mark.asyncio
    async def test_openai_uses_system_role_message(self):
        """OpenAI adapter must pass system_prompt as a messages-array system-role entry."""
        mock_resp = _make_openai_mock_response(_VALID_DECISION_JSON, 80, 40)
        with patch("openai.AsyncOpenAI") as MockOpenAI:
            instance = AsyncMock()
            chat_create = AsyncMock(return_value=mock_resp)
            instance.chat.completions.create = chat_create
            MockOpenAI.return_value = instance

            adapter = OpenAICompatibleAdapter(
                api_key="sk-test",
                model="gpt-4o-mini",
                base_url="https://api.openai.com/v1",
                provider_key="openai",
            )
            await adapter.complete(_SYSTEM_PROMPT, _USER_MESSAGE)

        call_args = chat_create.call_args
        all_kwargs = call_args.kwargs if hasattr(call_args, "kwargs") else call_args[1]
        messages = all_kwargs.get("messages", [])
        system_messages = [m for m in messages if m.get("role") == "system"]
        assert len(system_messages) == 1
        assert system_messages[0]["content"] == _SYSTEM_PROMPT
