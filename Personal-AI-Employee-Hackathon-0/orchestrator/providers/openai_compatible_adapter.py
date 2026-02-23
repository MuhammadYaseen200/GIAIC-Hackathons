"""OpenAI-compatible provider adapter — covers 6 providers via one class.

Providers using this adapter (all implement the OpenAI chat completions format):
    - OpenAI         (https://api.openai.com/v1)
    - Gemini         (https://generativelanguage.googleapis.com/v1beta/openai/)
    - OpenRouter     (https://openrouter.ai/api/v1)
    - Qwen/DashScope (https://dashscope.aliyuncs.com/compatible-mode/v1)
    - GLM/BigModel   (https://open.bigmodel.cn/api/paas/v4)
    - Goose          (user-defined via GOOSE_BASE_URL env var)

Usage:
    adapter = OpenAICompatibleAdapter(
        api_key=os.environ["GEMINI_API_KEY"],
        model="gemini-2.0-flash",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        provider_key="gemini",
    )
    text, in_tok, out_tok = await adapter.complete(system_prompt, user_msg)
"""

from __future__ import annotations

import openai

from orchestrator.providers.base import LLMProvider


class OpenAICompatibleAdapter(LLMProvider):
    """LLMProvider adapter for any provider implementing the OpenAI chat completions API."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        provider_key: str,
    ) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        self._provider_key = provider_key

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """Call provider via the OpenAI chat completions API.

        Returns:
            (response_text, prompt_tokens, completion_tokens)
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        text = response.choices[0].message.content or ""
        usage = response.usage
        return (text, usage.prompt_tokens, usage.completion_tokens)

    def provider_name(self) -> str:
        return self._provider_key

    def model_name(self) -> str:
        return self._model
