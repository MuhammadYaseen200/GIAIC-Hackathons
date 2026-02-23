"""Unit tests for orchestrator/providers/ — adapters, registry, factory.

Tests:
    - AnthropicAdapter.complete() returns correct (text, in_tok, out_tok) tuple
    - OpenAICompatibleAdapter.complete() returns correct (text, prompt_tok, completion_tok) tuple
    - provider_name() and model_name() accessors (no API key leakage)
    - create_provider() factory: valid config, unsupported provider, missing key, model override
    - Goose provider: requires GOOSE_BASE_URL
    - OpenRouter/Goose: requires LLM_MODEL (no default)
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from watchers.utils import PrerequisiteError

from orchestrator.providers.anthropic_adapter import AnthropicAdapter
from orchestrator.providers.base import LLMProvider
from orchestrator.providers.openai_compatible_adapter import OpenAICompatibleAdapter
from orchestrator.providers.registry import PROVIDER_REGISTRY, create_provider


# =============================================================================
# AnthropicAdapter
# =============================================================================

class TestAnthropicAdapter:

    @pytest.mark.asyncio
    async def test_complete_returns_correct_tuple(self):
        """complete() returns (text, input_tokens, output_tokens) from Anthropic SDK."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="archive decision JSON")]
        mock_response.usage.input_tokens = 512
        mock_response.usage.output_tokens = 128

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic") as MockClass:
            MockClass.return_value = mock_client
            adapter = AnthropicAdapter(api_key="test-key", model="claude-sonnet-4-20250514")
            result = await adapter.complete("System prompt", "User message")

        assert result == ("archive decision JSON", 512, 128)

    @pytest.mark.asyncio
    async def test_complete_passes_system_as_dedicated_param(self):
        """complete() uses dedicated `system=` param, not a system role message."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="{}")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 10

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic") as MockClass:
            MockClass.return_value = mock_client
            adapter = AnthropicAdapter(api_key="test-key")
            await adapter.complete("My system prompt", "My user message")

        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "My system prompt"
        assert call_kwargs["messages"] == [{"role": "user", "content": "My user message"}]

    def test_provider_name(self):
        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            adapter = AnthropicAdapter(api_key="test-key")
        assert adapter.provider_name() == "anthropic"

    def test_model_name_default(self):
        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            adapter = AnthropicAdapter(api_key="test-key")
        assert adapter.model_name() == "claude-sonnet-4-20250514"

    def test_model_name_custom(self):
        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            adapter = AnthropicAdapter(api_key="test-key", model="claude-opus-4-6")
        assert adapter.model_name() == "claude-opus-4-6"

    def test_provider_name_does_not_contain_api_key(self):
        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            adapter = AnthropicAdapter(api_key="sk-ant-super-secret-key")
        assert "sk-ant-super-secret-key" not in adapter.provider_name()
        assert "sk-ant-super-secret-key" not in adapter.model_name()

    def test_is_llm_provider(self):
        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            adapter = AnthropicAdapter(api_key="test-key")
        assert isinstance(adapter, LLMProvider)


# =============================================================================
# OpenAICompatibleAdapter
# =============================================================================

class TestOpenAICompatibleAdapter:

    @pytest.mark.asyncio
    async def test_complete_returns_correct_tuple(self):
        """complete() returns (text, prompt_tokens, completion_tokens)."""
        mock_choice = MagicMock()
        mock_choice.message.content = '{"decision": "archive"}'
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 300
        mock_response.usage.completion_tokens = 80

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI") as MockClass:
            MockClass.return_value = mock_client
            adapter = OpenAICompatibleAdapter(
                api_key="test-key",
                model="gemini-2.0-flash",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                provider_key="gemini",
            )
            result = await adapter.complete("System prompt", "User message")

        assert result == ('{"decision": "archive"}', 300, 80)

    @pytest.mark.asyncio
    async def test_complete_uses_system_role_message(self):
        """OpenAI-compatible adapter puts system prompt in messages array."""
        mock_choice = MagicMock()
        mock_choice.message.content = "{}"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 5

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI") as MockClass:
            MockClass.return_value = mock_client
            adapter = OpenAICompatibleAdapter(
                api_key="test-key", model="gpt-4o-mini",
                base_url="https://api.openai.com/v1", provider_key="openai",
            )
            await adapter.complete("System text", "User text")

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "System text"}
        assert messages[1] == {"role": "user", "content": "User text"}

    def test_provider_name_is_provider_key(self):
        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI"):
            adapter = OpenAICompatibleAdapter(
                api_key="key", model="gemini-2.0-flash",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                provider_key="gemini",
            )
        assert adapter.provider_name() == "gemini"

    def test_model_name(self):
        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI"):
            adapter = OpenAICompatibleAdapter(
                api_key="key", model="qwen-turbo",
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                provider_key="qwen",
            )
        assert adapter.model_name() == "qwen-turbo"

    def test_api_key_not_in_names(self):
        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI"):
            adapter = OpenAICompatibleAdapter(
                api_key="super-secret-openrouter-key",
                model="openai/gpt-4o",
                base_url="https://openrouter.ai/api/v1",
                provider_key="openrouter",
            )
        assert "super-secret-openrouter-key" not in adapter.provider_name()
        assert "super-secret-openrouter-key" not in adapter.model_name()

    def test_is_llm_provider(self):
        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI"):
            adapter = OpenAICompatibleAdapter(
                api_key="key", model="glm-4-flash",
                base_url="https://open.bigmodel.cn/api/paas/v4", provider_key="glm",
            )
        assert isinstance(adapter, LLMProvider)


# =============================================================================
# create_provider() factory
# =============================================================================

class TestCreateProvider:

    def test_anthropic_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-key")
        monkeypatch.delenv("LLM_MODEL", raising=False)

        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            provider = create_provider()

        assert isinstance(provider, AnthropicAdapter)
        assert provider.provider_name() == "anthropic"
        assert provider.model_name() == "claude-sonnet-4-20250514"

    def test_gemini_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "AIza-real-gemini-key")
        monkeypatch.delenv("LLM_MODEL", raising=False)

        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI") as MockOpenAI:
            provider = create_provider()
            init_kwargs = MockOpenAI.call_args.kwargs

        assert isinstance(provider, OpenAICompatibleAdapter)
        assert provider.provider_name() == "gemini"
        assert "generativelanguage.googleapis.com" in init_kwargs["base_url"]

    def test_model_override_via_llm_model(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-real-key")
        monkeypatch.setenv("LLM_MODEL", "claude-opus-4-6")

        with patch("orchestrator.providers.anthropic_adapter.anthropic.AsyncAnthropic"):
            provider = create_provider()

        assert provider.model_name() == "claude-opus-4-6"

    def test_default_model_fallback(self, monkeypatch):
        """Without LLM_MODEL env var, uses PROVIDER_REGISTRY default."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-real-openai-key")
        monkeypatch.delenv("LLM_MODEL", raising=False)

        with patch("orchestrator.providers.openai_compatible_adapter.openai.AsyncOpenAI"):
            provider = create_provider()

        assert provider.model_name() == "gpt-4o-mini"

    def test_missing_llm_provider_raises(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        with pytest.raises(PrerequisiteError, match="LLM_PROVIDER is not set"):
            create_provider()

    def test_unsupported_provider_raises(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "cohere")
        with pytest.raises(PrerequisiteError, match="not supported"):
            create_provider()

    def test_unsupported_provider_lists_supported(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "mystery-llm")
        with pytest.raises(PrerequisiteError) as exc_info:
            create_provider()
        error_text = str(exc_info.value)
        assert "anthropic" in error_text

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(PrerequisiteError, match="ANTHROPIC_API_KEY"):
            create_provider()

    def test_placeholder_api_key_raises(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "your-openai-api-key-here")
        with pytest.raises(PrerequisiteError, match="OPENAI_API_KEY"):
            create_provider()

    def test_goose_requires_goose_base_url(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "goose")
        monkeypatch.setenv("GOOSE_API_KEY", "goose-real-key")
        monkeypatch.setenv("LLM_MODEL", "goose-v1")
        monkeypatch.delenv("GOOSE_BASE_URL", raising=False)
        with pytest.raises(PrerequisiteError, match="GOOSE_BASE_URL"):
            create_provider()

    def test_openrouter_requires_llm_model(self, monkeypatch):
        """OpenRouter has no default model — LLM_MODEL must be set."""
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-real-key")
        monkeypatch.delenv("LLM_MODEL", raising=False)
        with pytest.raises(PrerequisiteError, match="LLM_MODEL"):
            create_provider()

    def test_errors_reference_ht_009(self, monkeypatch):
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        with pytest.raises(PrerequisiteError, match="HT-009"):
            create_provider()


# =============================================================================
# PROVIDER_REGISTRY structure
# =============================================================================

class TestProviderRegistry:

    def test_all_seven_providers_present(self):
        expected = {"anthropic", "openai", "gemini", "openrouter", "qwen", "glm", "goose"}
        assert set(PROVIDER_REGISTRY.keys()) == expected

    def test_all_entries_have_required_keys(self):
        required_fields = {"adapter", "api_key_env", "default_model", "base_url"}
        for provider_key, config in PROVIDER_REGISTRY.items():
            assert required_fields <= set(config.keys()), (
                f"Provider '{provider_key}' missing fields: {required_fields - set(config.keys())}"
            )

    def test_anthropic_uses_anthropic_adapter(self):
        assert PROVIDER_REGISTRY["anthropic"]["adapter"] == "anthropic"

    def test_all_others_use_openai_compatible(self):
        for key in ("openai", "gemini", "openrouter", "qwen", "glm", "goose"):
            assert PROVIDER_REGISTRY[key]["adapter"] == "openai_compatible", key

    def test_gemini_has_correct_base_url(self):
        assert "generativelanguage.googleapis.com" in PROVIDER_REGISTRY["gemini"]["base_url"]
