"""LLM provider abstraction layer.

Two adapter classes:
- AnthropicAdapter   — native anthropic SDK (Anthropic Claude only)
- OpenAICompatibleAdapter — openai SDK with base_url (OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose)

Usage:
    from orchestrator.providers.registry import create_provider
    provider = create_provider()  # reads LLM_PROVIDER from .env
    text, in_tok, out_tok = await provider.complete(system_prompt, user_message)
"""
