"""Ralph Wiggum Orchestrator — Phase 3 LLM Reasoning Loop.

Public API:
    from orchestrator import RalphWiggumOrchestrator, create_provider, LLMProvider
    from orchestrator.models import LLMDecision, EmailContext, OrchestratorState
"""

from orchestrator.models import EmailContext, LLMDecision, OrchestratorState
from orchestrator.orchestrator import RalphWiggumOrchestrator
from orchestrator.providers.base import LLMProvider
from orchestrator.providers.registry import PROVIDER_REGISTRY, create_provider

__version__ = "0.1.0"
__all__ = [
    "RalphWiggumOrchestrator",
    "create_provider",
    "PROVIDER_REGISTRY",
    "LLMProvider",
    "LLMDecision",
    "EmailContext",
    "OrchestratorState",
]
