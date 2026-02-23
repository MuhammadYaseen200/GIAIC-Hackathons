"""Anthropic provider adapter — uses native anthropic Python SDK.

Key differences from the OpenAI-compatible adapter:
- Dedicated `system` parameter (not a system-role message in the messages array)
- Response via response.content[0].text (not choices[0].message.content)
- Token usage: response.usage.input_tokens / response.usage.output_tokens

Usage:
    adapter = AnthropicAdapter(api_key=os.environ["ANTHROPIC_API_KEY"])
    text, in_tok, out_tok = await adapter.complete(system_prompt, user_msg)
"""

from __future__ import annotations

import anthropic

from orchestrator.providers.base import LLMProvider

_DEFAULT_MODEL = "claude-sonnet-4-20250514"


class AnthropicAdapter(LLMProvider):
    """LLMProvider adapter for Claude models via the native Anthropic SDK."""

    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """Call Claude via the Anthropic messages API.

        Returns:
            (response_text, input_tokens, output_tokens)
        """
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,  # Anthropic-specific: dedicated system parameter
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text
        return (text, response.usage.input_tokens, response.usage.output_tokens)

    def provider_name(self) -> str:
        return "anthropic"

    def model_name(self) -> str:
        return self._model
