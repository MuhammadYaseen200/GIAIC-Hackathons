# ADR-009: Hybrid AI Engine (OpenAI Agents SDK + Gemini)

**Status**: Accepted
**Date**: 2026-01-04
**Deciders**: Lead Architect, Modular AI Architect
**Applies To**: Phase III (AI Chatbot Integration)
**Supersedes**: None
**Related**: ADR-007 (Brownfield Isolation Strategy), master-plan.md Section 3

---

## Context

Phase III introduces an AI chatbot layer that orchestrates MCP tools to manage tasks through natural language. A critical architectural decision is required for the AI framework:

**Problem Statement**: The project constitution mandates "OpenAI Agents SDK" as the AI framework, but the user requirement specifies using Google's Gemini model for inference rather than OpenAI's models.

**Constraints**:
1. Constitution compliance: Must use OpenAI Agents SDK for orchestration
2. User requirement: Must use Gemini Flash 1.5/2.0 for model inference
3. Cost optimization: Gemini offers competitive pricing for agentic workloads
4. MCP Integration: Agent must call MCP tools seamlessly
5. Phase 2 compatibility: Must not break existing REST API deployment

**Technical Context**:
- OpenAI Agents SDK provides superior tool-calling orchestration
- Gemini 2.0 supports OpenAI-compatible API endpoints
- MCP Server provides tool definitions for task management
- Stateless API pattern with conversation persistence in Neon PostgreSQL

---

## Decision

**Adopt a hybrid architecture: Use OpenAI Agents SDK for orchestration while configuring it to use Google Gemini via OpenAI-compatible endpoint.**

### Configuration Approach (Option A: OpenAI-Compatible Endpoint)

```python
# phase-3-chatbot/backend/app/agent/chat_agent.py

from agents import Agent, Runner
from agents.models.openai_compatible import OpenAICompatibleModel

# Configure Gemini via OpenAI-compatible interface
gemini_model = OpenAICompatibleModel(
    model="gemini-2.0-flash",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
    api_key=settings.GEMINI_API_KEY,
)

# Create agent with MCP tools
agent = Agent(
    name="TaskAssistant",
    instructions=SYSTEM_PROMPT,
    model=gemini_model,
    tools=[
        "add_task", "list_tasks", "complete_task",
        "delete_task", "update_task", "search_tasks",
        "update_priority", "add_tags", "remove_tags", "list_tags",
    ],
)
```

### Fallback Approach (Option B: Custom Adapter)

If OpenAI-compatible endpoint is unavailable or has limitations:

```python
# phase-3-chatbot/backend/app/agent/gemini_adapter.py

from agents.models import Model
import google.generativeai as genai

class GeminiModelAdapter(Model):
    """Adapter to use Google Gemini with OpenAI Agents SDK."""

    def __init__(self, model_name: str = "gemini-2.0-flash"):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(model_name)

    async def generate(self, messages, tools=None, **kwargs):
        # Convert OpenAI message format to Gemini format
        # Handle tool calls and responses
        pass
```

### Environment Configuration

```bash
# .env.example (additions for Phase 3)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
AGENT_MAX_TURNS=10
AGENT_TIMEOUT_SECONDS=30
```

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Constitution Compliance | Uses OpenAI Agents SDK as mandated |
| Cost Efficiency | Gemini pricing is competitive for agentic workloads |
| Best of Both Worlds | OpenAI's orchestration + Gemini's inference |
| API Compatibility | OpenAI-compatible endpoint minimizes code changes |
| Tool Calling | Native support for MCP tool integration |
| Future Flexibility | Can swap models without changing orchestration layer |

### Negative

| Drawback | Mitigation |
|----------|------------|
| Dependency on two providers | Both have high availability SLAs |
| Potential API divergence | Pin SDK versions; test with each upgrade |
| Additional configuration | Document in CLAUDE.md and .env.example |
| Debugging complexity | Log both orchestration and inference calls |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Gemini API changes | Low | High | Pin google-generativeai version |
| OpenAI Agents SDK incompatibility | Medium | High | Implement Option B (custom adapter) |
| Tool calling format mismatch | Low | Medium | Validate tool schemas on startup |
| Rate limiting | Medium | Medium | Implement retry logic with exponential backoff |

---

## Alternatives Considered

### Alternative 1: Pure OpenAI (GPT-4o/GPT-4o-mini)

**Approach**: Use OpenAI Agents SDK with OpenAI models as designed.

**Pros**:
- Native compatibility, no adapters needed
- Well-tested tool calling
- Strong documentation

**Cons**:
- Higher cost for agentic workloads
- Does not meet user requirement for Gemini

**Rejected Because**: User explicitly required Gemini model for inference.

### Alternative 2: Pure Google (Vertex AI Agent Builder)

**Approach**: Use Google's native agent framework with Gemini.

**Pros**:
- Native Gemini integration
- Google Cloud ecosystem

**Cons**:
- Violates constitution (mandates OpenAI Agents SDK)
- Less mature agentic framework
- Vendor lock-in to Google Cloud

**Rejected Because**: Violates project constitution; OpenAI Agents SDK has superior tool orchestration.

### Alternative 3: LangChain with Gemini

**Approach**: Use LangChain as abstraction layer over Gemini.

**Pros**:
- Model agnostic
- Large community
- Flexible

**Cons**:
- Not mandated by constitution
- Additional abstraction layer
- Heavier dependency footprint

**Rejected Because**: Constitution specifies OpenAI Agents SDK, not LangChain.

---

## Phase 2 Compatibility Guarantee

This decision does NOT affect Phase 2 deployment:

1. **Isolated Module**: Agent code lives in `app/agent/` directory, completely separate from Phase 2 services
2. **No Model Changes**: Phase 2 SQLModel definitions remain unchanged
3. **Additive Dependencies**: New packages (mcp, openai-agents, google-generativeai) are added, not replaced
4. **Environment Variables**: New env vars (GEMINI_API_KEY, etc.) have no effect if not set
5. **Optional Integration**: Chat endpoint is a NEW route; existing REST API unaffected

---

## Implementation Guidelines

### Phase 3 Startup Checklist

```python
# app/main.py (additions, not replacements)

from app.agent.chat_agent import verify_gemini_connection

@app.on_event("startup")
async def startup_event():
    # ... existing startup logic ...

    # Phase 3: Verify Gemini connection (optional, fails gracefully)
    try:
        await verify_gemini_connection()
        logger.info("Gemini connection verified")
    except Exception as e:
        logger.warning(f"Gemini not configured: {e}")
```

### Testing the Hybrid Setup

```python
# tests/test_agent.py

async def test_gemini_via_openai_agents():
    """Verify Gemini responds through OpenAI Agents SDK."""
    result = await agent.run("What is 2 + 2?")
    assert "4" in result.response
```

---

## References

- [OpenAI Agents SDK Documentation](https://github.com/openai/openai-agents-python)
- [Gemini API OpenAI Compatibility](https://ai.google.dev/gemini-api/docs/openai)
- Phase 3 Specification: `phase-3-chatbot/specs/phase-3-spec.md`
- Phase 3 Master Plan: `phase-3-chatbot/specs/master-plan.md` (Section 3)

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-01-04 | Modular AI Architect | Initial ADR created |

