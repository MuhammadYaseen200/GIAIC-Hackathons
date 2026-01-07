# PHR-301: Phase 3 AI Chatbot Specification

**Date**: 2026-01-04
**Phase**: Phase 3 - AI Chatbot
**Stage**: spec
**Agents Used**: @path-warden, @modular-ai-architect, @spec-architect
**Duration**: ~15 minutes
**Status**: COMPLETE

---

## Context

Phase 2 (Full-Stack Web) is deployed and stable on Vercel. Phase 3 adds a conversational AI interface using MCP Server, OpenAI Agents SDK, and Google Gemini model.

## Prompt

```text
/sp.specify use @agent-imperator @agent-loop-controller @agent-qa-overseer
@agent-path-warden @agent-modular-ai-architect @agent-ux-frontend-developer @agent-spec-architect

Context: We are starting Phase 3: AI Chatbot.
- Source: phase-2-web (Deployed Gold Master)
- Destination: phase-3-chatbot (New Workspace)
- Goal: Initialize workspace and generate Specification & Master Plan

Constraints:
1. Model Strategy: OpenAI Agents SDK with Gemini model
2. Code Reuse (Import Rule): MCP Server imports existing TaskService

Execution Protocol:
1. @path-warden: Create phase-3-chatbot/, copy phase-2-web/*
2. @modular-ai-architect: Create master-plan.md
3. @spec-architect: Create phase-3-spec.md
```

## Response Summary

### Agent Orchestration

| Agent | Task | Status |
|-------|------|--------|
| @path-warden | Workspace initialization | COMPLETE |
| @modular-ai-architect | Master plan creation | COMPLETE |
| @spec-architect | Functional specification | COMPLETE |

### Files Created

| File | Size | Purpose |
|------|------|---------|
| `phase-3-chatbot/` | 92 files | Brownfield workspace from Phase 2 |
| `specs/master-plan.md` | 34KB | Architecture strategy |
| `specs/phase-3-spec.md` | 30KB | Functional requirements |
| `specs/checklists/requirements.md` | 2KB | Quality checklist |

### Master Plan Highlights

1. **MCP Server Design**: Import existing `TaskService` directly
2. **AI Stack**: OpenAI Agents SDK + Gemini via OpenAI-compatible endpoint
3. **Frontend**: ChatKit UI alongside existing Task List
4. **State**: Conversation history in Neon DB
5. **Tasks**: 26 atomic tasks (T-301 to T-326)

### Specification Highlights

1. **User Stories**: 7 (US-301 to US-307)
   - Add Task via Chat (P1)
   - List Tasks via Chat (P1)
   - Complete Task via Chat (P1)
   - Delete Task via Chat (P2)
   - Update Task via Chat (P2)
   - Conversation Persistence (P1)
   - Error Handling (P1)

2. **Functional Requirements**: 28 (FR-301 to FR-328)

3. **Constraints**:
   - English only (no multi-language)
   - No voice input
   - No proactive reminders
   - 500 char message limit
   - 2s response time target

### Quality Validation

| Category | Total | Passed |
|----------|-------|--------|
| Content Quality | 4 | 4 |
| Requirement Completeness | 8 | 8 |
| Feature Readiness | 4 | 4 |
| Phase 3 Specific | 4 | 4 |
| **Total** | **20** | **20** |

### Commit

```
d4f8f43 feat: initialize Phase 3 AI Chatbot workspace and specifications
```

### Branch

`004-phase3-chatbot`

## Next Steps

1. `/sp.clarify` - Resolve any ambiguities (none identified)
2. `/sp.plan` - Generate detailed implementation plan
3. `/sp.tasks` - Break down into atomic tasks

---

**End of PHR-301**
