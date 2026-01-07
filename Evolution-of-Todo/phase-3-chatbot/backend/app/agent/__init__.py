"""AI Agent module for Phase 3 chatbot.

This module provides the AI agent integration using OpenAI Agents SDK
with Gemini model inference per ADR-009 (Hybrid AI Engine).

Components:
- chat_agent: Gemini model configuration and agent runner
- prompts: System prompts for task management assistant
"""

from app.agent.chat_agent import AgentResult, run_agent
from app.agent.prompts import SYSTEM_PROMPT

__all__ = [
    "AgentResult",
    "run_agent",
    "SYSTEM_PROMPT",
]
