#!/usr/bin/env python3
"""Verify LLM provider connectivity — HT-009 verification script.

Loads .env, creates the configured provider, sends a single test message,
and prints the result. Use this to confirm your LLM_PROVIDER and API key
are configured correctly before running the orchestrator.

Usage:
    python scripts/verify_llm_provider.py

Exit codes:
    0 — provider responded successfully
    1 — configuration error or network failure

Environment variables (set in .env):
    LLM_PROVIDER       — required: anthropic | openai | gemini | ...
    LLM_MODEL          — optional: override default model for the provider
    ANTHROPIC_API_KEY  — required when LLM_PROVIDER=anthropic
    OPENAI_API_KEY     — required when LLM_PROVIDER=openai
    GEMINI_API_KEY     — required when LLM_PROVIDER=gemini
    OPENROUTER_API_KEY — required when LLM_PROVIDER=openrouter
    QWEN_API_KEY       — required when LLM_PROVIDER=qwen
    GLM_API_KEY        — required when LLM_PROVIDER=glm
    GOOSE_API_KEY      — required when LLM_PROVIDER=goose
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Ensure project root is on the path when run directly
_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv()


async def main() -> int:
    """Run the provider connectivity check. Returns exit code."""
    try:
        from orchestrator.providers.registry import create_provider
    except ImportError as exc:
        print(f"ERROR: Cannot import orchestrator package: {exc}")
        print(f"  Make sure you are running from project root: {_PROJECT_ROOT}")
        return 1

    # Create provider from environment
    try:
        provider = create_provider()
    except Exception as exc:
        print(f"ERROR: Failed to create provider: {exc}")
        print()
        print("Check your .env file contains:")
        print("  LLM_PROVIDER=<anthropic|openai|gemini|openrouter|qwen|glm|goose>")
        print("  <PROVIDER>_API_KEY=<your-api-key>")
        return 1

    print(f"Provider : {provider.provider_name()}")
    print(f"Model    : {provider.model_name()}")
    print()
    print("Sending test message...")

    try:
        text, in_tok, out_tok = await provider.complete(
            system_prompt="You are a connectivity test assistant.",
            user_message="Say 'hello' and nothing else.",
            temperature=0.0,
            max_tokens=16,
        )
    except Exception as exc:
        print(f"ERROR: LLM API call failed: {exc}")
        print()
        print("Check that:")
        print("  1. Your API key is valid and has remaining quota")
        print("  2. You have network access to the provider endpoint")
        return 1

    if not text or not text.strip():
        print("ERROR: Received empty response from LLM provider")
        return 1

    print(f"Response : {text.strip()[:200]}")
    print(f"Tokens   : {in_tok} input / {out_tok} output")
    print()
    print("OK  LLM provider connectivity verified")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
