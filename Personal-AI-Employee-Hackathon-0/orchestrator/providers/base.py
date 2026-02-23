"""Abstract base class for all LLM provider adapters.

Every provider (Anthropic, OpenAI, Gemini, OpenRouter, Qwen, GLM, Goose)
must implement the LLMProvider ABC to participate in the Ralph Wiggum loop.

Contract:
    text, in_tokens, out_tokens = await provider.complete(system, user)

Design:
    - Anthropic uses native `anthropic.AsyncAnthropic` (dedicated system param)
    - All others use `openai.AsyncOpenAI(base_url=...)` with messages[system/user]
"""

from __future__ import annotations

import abc


class LLMProvider(abc.ABC):
    """Abstract LLM provider adapter.

    Implementations must be async-safe and stateless beyond client initialisation.
    """

    @abc.abstractmethod
    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> tuple[str, int, int]:
        """Send a single completion request and return the response.

        Args:
            system_prompt: System-level instructions for the LLM.
            user_message: The user turn content (email context in our case).
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative).
            max_tokens: Maximum tokens in the completion response.

        Returns:
            A 3-tuple of:
                - response_text (str): The raw LLM response (should be JSON for triage)
                - input_tokens (int): Token count consumed by the prompt
                - output_tokens (int): Token count consumed by the response
        """
        ...

    @abc.abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider key (e.g. 'anthropic', 'openai', 'gemini').

        Used for logging and drafted_by fields in DraftReply.
        """
        ...

    @abc.abstractmethod
    def model_name(self) -> str:
        """Exact model identifier used for this adapter instance.

        Examples: 'claude-sonnet-4-20250514', 'gpt-4o-mini', 'gemini-2.0-flash'.
        Used for logging and drafted_by fields in DraftReply.
        """
        ...
