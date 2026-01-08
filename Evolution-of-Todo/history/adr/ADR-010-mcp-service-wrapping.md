# ADR-010: MCP Service Wrapping Strategy

**Status**: Proposed
**Date**: 2026-01-04
**Deciders**: Lead Architect, Backend Builder
**Applies To**: Phase III (AI Chatbot)
**Related**: ADR-007 (Brownfield Isolation Strategy)

---

## Context

Phase III requires Model Context Protocol (MCP) tools to expose task CRUD operations to AI agents. These tools need the same business logic implemented in Phase II's TaskService located at phase-2-web/backend/app/services/task_service.py.

**Problem Statement**: How should Phase III MCP tools access task business logic? Should they import from Phase II, copy the logic, or rewrite entirely?

**Constraints**:
1. Constitution mandates "evolve, not rewrite" (Brownfield Protocol)
2. ADR-007 explicitly forbids direct imports between phases
3. Phase II is sealed (complete REST API, no further changes)
4. Phase III requires stateless MCP tools with async database access
5. Monorepo structure must remain clean with clear phase boundaries

**Technical Context**:
- Phase II: FastAPI + SQLModel, async, UUID IDs, multi-tenant, REST endpoints
- Phase III: MCP Server, OpenAI Agents SDK, async, UUID IDs, multi-tenant, MCP Tools
- Shared concerns: TaskService business logic, multi-tenancy, UUID-based IDs

---

## Decision

Phase III must NOT import directly from phase-2-web/. TaskService business logic must be "Ported" (copied and adapted) to phase-3-chatbot/. This maintains clean isolation between phases while honoring the Brownfield Protocol through conceptual evolution, not code sharing.

### Isolation Boundary

```
Phase II (REST)  <--->  Phase III (MCP)
  TaskService           MCPTaskService (ported logic)
  task.py model          task.py model (same DB)

FORBIDDEN: from phase_2_web.app.services import TaskService
FORBIDDEN: from phase_2_web.app.models import Task
ALLOWED: Port TaskService logic to Phase 3 MCP layer
```

### What "Porting" Means for MCP Tools

1. Study Phase II TaskService: Read phase-2-web/backend/app/services/task_service.py
2. Extract Business Rules: Title validation, completion toggle, multi-tenant queries
3. Implement in Phase III Context: MCP tool handlers, async, same database
4. Do NOT Import: Adapt patterns and logic, not code

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Clean Boundaries | Each phase is self-contained and deployable |
| Independent Evolution | Phase III can evolve without affecting Phase II |
| Clear Ownership | Phase II remains sealed; Phase III has its own tests |
| No Import Conflicts | Phase III can run independently for MCP transport |
| Honest Documentation | Each phase documents its own architecture |
| Shared Database | Both phases can access same Neon PostgreSQL instance |

### Negative

| Drawback | Mitigation |
|----------|------------|
| Code Duplication | Acceptable; each phase serves different protocols (REST vs MCP) |
| Business Logic Drift | Document ported patterns; reference Phase II in comments |
| No Shared Library | Could create shared/ later; premature for Phase III |
| Effort to Port | One-time cost; logic is well-documented in Phase II |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Accidental Phase II import | Low | Medium | CI check: no cross-phase imports |
| Logic divergence | Medium | Low | Database schema is shared; behavior should align |
| Future refactoring difficulty | Low | Low | Each phase stands alone |

---

## Alternatives Considered

### Alternative 1: Direct Imports from Phase II

Approach: from phase_2_web.app.services import TaskService

Pros:
- True code reuse
- Single source of truth
- Less initial effort

Cons:
- Tight coupling across phases
- Changes to Phase II break Phase III
- Phase II would need to be "unsealed"
- Violates ADR-007 isolation principle
- MCP server would depend on REST API code (unnecessary)

Rejected Because: Explicitly forbidden by ADR-007; violates phase isolation.

### Alternative 2: Shared Library Package

Approach: Create shared/ package with common business logic.

Pros:
- Clean abstraction
- True DRY principle
- Single source of truth

Cons:
- Premature abstraction
- Overhead of maintaining shared code
- MCP needs stateless functions; REST needs FastAPI integration
- Adds complexity to monorepo structure

Rejected Because: Premature optimization; phases serve different protocols.

### Alternative 3: MCP Wraps HTTP API

Approach: MCP tools call Phase II REST endpoints via HTTP.

Pros:
- No code duplication
- REST API is single source of truth
- Phase III becomes a pure transport layer

Cons:
- Adds network latency
- Requires JWT management in MCP server
- HTTP overhead for same-host communication
- Couples MCP to REST API availability

Rejected Because: Adds unnecessary network hops; defeats purpose of MCP direct DB access.

### Alternative 4: Complete Rewrite

Approach: Ignore Phase II entirely; write Phase III from scratch.

Pros:
- No legacy constraints
- Fresh design

Cons:
- Violates Constitution Brownfield Protocol
- Loses validated business rules
- More effort to rediscover edge cases

Rejected Because: Constitution mandates evolution; Phase II insights are valuable.

---

## Phase 2 Compatibility Guarantee

This decision does NOT affect Phase 2 deployment:

1. **No Imports**: Phase 3 explicitly forbids `from phase_2_web...`
2. **Isolated MCP Server**: Runs independently; does not depend on Phase 2 code
3. **Shared Database Only**: Both phases connect to same Neon PostgreSQL, but via separate code paths
4. **REST API Unchanged**: Phase 2 endpoints continue working independently
5. **Additive Changes Only**: New MCP layer added; no Phase 2 code modified

---

## Porting Guidelines

### Phase II to Phase III Mapping

| Phase II Component | Phase III Component | Adaptation |
|--------------------|--------------------|------------|
| Task SQLModel | Task SQLModel | Identical model (same database) |
| TaskService.create_task() | add_task() MCP tool | Same logic, async tool handler |
| TaskService.list_tasks() | list_tasks() MCP tool | Same logic, async tool handler |
| TaskService.get_task() | Internal helper | Same query pattern |
| TaskService.update_task() | update_task() MCP tool | Same logic, async tool handler |
| TaskService.delete_task() | delete_task() MCP tool | Same logic, async tool handler |
| TaskService.toggle_complete() | complete_task() MCP tool | Same logic, async tool handler |

### Validation Rules to Port

Phase II: phase-2-web/backend/app/services/task_service.py
- MAX_TITLE_LENGTH = 200 (Port this constant)
- MAX_DESCRIPTION_LENGTH = 1000 (Port this constant)

Phase III: phase-3-chatbot/backend/app/mcp/tools/task_tools.py
- MAX_TITLE_LENGTH = 200 (Ported from Phase II)
- MAX_DESCRIPTION_LENGTH = 1000 (Ported from Phase II)

### MCP Tool Pattern

phase-3-chatbot/backend/app/mcp/tools/task_tools.py
- Import from mcp and app.models.task
- Async handler functions with session, user_id, task parameters
- Return MCP-compatible dict responses

### Forbidden Patterns

NEVER:
- from phase_2_web.app.services import TaskService
- from phase_2_web.app.models import Task
- import sys; sys.path.insert(0, '../phase-2-web/backend')

ALLOWED:
- Reference in comments: Ported from Phase II: phase-2-web/backend/app/services/task_service.py:43
- Port logic to local MCPTaskService class

### Database Connection Strategy

Since both phases share the same database (Neon PostgreSQL):
- Phase III can reuse the same DATABASE_URL environment variable
- Use the same SQLModel session pattern as Phase II
- Both phases connect to the same PostgreSQL instance

---

## MCP Tool Definitions

### Tool Registry

phase-3-chatbot/backend/app/mcp/server.py
- Server: evolution-of-todo-mcp
- Tools:
  - add_task: Add new task to user's todo list
  - list_tasks: List all tasks for authenticated user
  - complete_task: Mark a task as completed
  - update_task: Update task title or description
  - delete_task: Delete a task permanently

All tool handlers use ported business logic from Phase II TaskService.

---

## Verification

### CI Check (Recommended)

.github/workflows/isolation-check.yml
- Fail if any phase-3 file imports from phase-2
- Check for: from phase_2_web, import phase_2_web

### Manual Check

Commands that should return no results:
- grep -r "phase_2_web" phase-3-chatbot/
- grep -r "phase-2-web" phase-3-chatbot/backend/
- grep -r "phase-2" phase-3-chatbot/backend/app/mcp/

---

## References

- Constitution: CLAUDE.md (Brownfield Protocol section)
- ADR-007: history/adr/ADR-007-brownfield-isolation-strategy.md
- Phase II TaskService: phase-2-web/backend/app/services/task_service.py
- Phase II Task Model: phase-2-web/backend/app/models/task.py
- Phase 3 Specification: phase-3-chatbot/specs/phase-3-spec.md
- MCP Specification: https://modelcontextprotocol.io/

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-01-04 | Lead Architect | Initial ADR created |