"""Provider registry and factory for Ralph Wiggum Orchestrator.

Maps provider keys (from LLM_PROVIDER env var) to adapter configurations.
Instantiates the correct LLMProvider from environment variables.

Supported providers:
    anthropic   — native Anthropic SDK (AnthropicAdapter)
    openai      — OpenAI chat completions (OpenAICompatibleAdapter)
    gemini      — Google Gemini via OpenAI-compatible endpoint
    openrouter  — OpenRouter multi-model routing
    qwen        — Alibaba DashScope (Qwen)
    glm         — Zhipu AI BigModel (GLM)
    goose       — Custom/self-hosted endpoint (GOOSE_BASE_URL required)

Usage:
    from orchestrator.providers.registry import create_provider
    provider = create_provider()  # reads LLM_PROVIDER + LLM_MODEL from env
"""

from __future__ import annotations

import os

from watchers.utils import PrerequisiteError

from orchestrator.providers.anthropic_adapter import AnthropicAdapter
from orchestrator.providers.base import LLMProvider
from orchestrator.providers.openai_compatible_adapter import OpenAICompatibleAdapter

# ---------------------------------------------------------------------------
# Registry: provider key → adapter config
# ---------------------------------------------------------------------------

PROVIDER_REGISTRY: dict[str, dict] = {
    "anthropic": {
        "adapter": "anthropic",
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-20250514",
        "base_url": None,  # native SDK, no base_url
    },
    "openai": {
        "adapter": "openai_compatible",
        "api_key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
        "base_url": "https://api.openai.com/v1",
    },
    "gemini": {
        "adapter": "openai_compatible",
        "api_key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
    },
    "openrouter": {
        "adapter": "openai_compatible",
        "api_key_env": "OPENROUTER_API_KEY",
        "default_model": None,  # user MUST set LLM_MODEL
        "base_url": "https://openrouter.ai/api/v1",
    },
    "qwen": {
        "adapter": "openai_compatible",
        "api_key_env": "QWEN_API_KEY",
        "default_model": "qwen-turbo",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    },
    "glm": {
        "adapter": "openai_compatible",
        "api_key_env": "GLM_API_KEY",
        "default_model": "glm-4-flash",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
    },
    "goose": {
        "adapter": "openai_compatible",
        "api_key_env": "GOOSE_API_KEY",
        "default_model": None,  # user MUST set LLM_MODEL
        "base_url": None,       # user MUST set GOOSE_BASE_URL
    },
}

_SUPPORTED_PROVIDERS = ", ".join(sorted(PROVIDER_REGISTRY.keys()))


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_provider() -> LLMProvider:
    """Instantiate an LLMProvider from environment variables.

    Reads:
        LLM_PROVIDER — required; one of the PROVIDER_REGISTRY keys
        LLM_MODEL    — optional override; uses registry default if absent
        <PROVIDER>_API_KEY — required; must not be a placeholder value

    Returns:
        Configured LLMProvider ready for .complete() calls.

    Raises:
        PrerequisiteError: If LLM_PROVIDER is missing, unknown, or its API key
            is not configured. References HT-009 for human remediation steps.
    """
    # 1. Resolve provider key
    provider_key = os.getenv("LLM_PROVIDER", "").strip().lower()
    if not provider_key:
        raise PrerequisiteError(
            f"LLM_PROVIDER is not set. Set it to one of: {_SUPPORTED_PROVIDERS}",
            ht_reference="HT-009",
        )

    if provider_key not in PROVIDER_REGISTRY:
        raise PrerequisiteError(
            f"LLM_PROVIDER='{provider_key}' is not supported. "
            f"Supported providers: {_SUPPORTED_PROVIDERS}",
            ht_reference="HT-009",
        )

    config = PROVIDER_REGISTRY[provider_key]

    # 2. Resolve API key
    api_key_env = config["api_key_env"]
    api_key = os.getenv(api_key_env, "").strip()
    if not api_key or api_key.lower().startswith("your-"):
        raise PrerequisiteError(
            f"LLM_PROVIDER is set to '{provider_key}' but {api_key_env} is not configured. "
            f"Please set {api_key_env} in your .env file.",
            ht_reference="HT-009",
        )

    # 3. Resolve model
    model_override = os.getenv("LLM_MODEL", "").strip()
    model = model_override or config["default_model"]
    if not model:
        raise PrerequisiteError(
            f"LLM_MODEL must be set for provider '{provider_key}' (it has no default model). "
            f"Set LLM_MODEL in your .env file.",
            ht_reference="HT-009",
        )

    # 4. Resolve base_url (Goose uses GOOSE_BASE_URL)
    base_url: str | None = config["base_url"]
    if provider_key == "goose" and not base_url:
        base_url = os.getenv("GOOSE_BASE_URL", "").strip()
        if not base_url or base_url.lower().startswith("your-"):
            raise PrerequisiteError(
                "LLM_PROVIDER=goose requires GOOSE_BASE_URL to be set in your .env file.",
                ht_reference="HT-009",
            )

    # 5. Instantiate adapter
    if config["adapter"] == "anthropic":
        return AnthropicAdapter(api_key=api_key, model=model)

    return OpenAICompatibleAdapter(
        api_key=api_key,
        model=model,
        base_url=base_url,  # type: ignore[arg-type]
        provider_key=provider_key,
    )
