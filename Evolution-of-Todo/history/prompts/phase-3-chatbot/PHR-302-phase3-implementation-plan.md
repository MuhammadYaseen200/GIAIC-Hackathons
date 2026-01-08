# PHR-302: Phase 3 Implementation Plan with Intermediate Features

**Date**: 2026-01-04
**Phase**: Phase 3 - AI Chatbot
**Stage**: plan
**Agents Used**: @spec-architect, @modular-ai-architect
**Duration**: ~30 minutes
**Status**: COMPLETE

---

## Context

Phase 3 specification was complete with 7 core user stories (US-301 to US-307). The user requested scope expansion to include Intermediate Level Features from the Constitution:
- Priorities (High/Medium/Low)
- Tags/Categories
- Search & Filter
- Sort Tasks

## Prompt

```text
/sp.plan

Update the Specification to include these new features and generate the
Implementation Plan and Task List.

Scope Expansion:
- Priorities: High/Medium/Low
- Tags/Categories: Labels (Work, Home, etc.)
- Search & Filter: By keyword, status, priority, date
- Sort: By due date, priority
```

## Response Summary

### Specification Updates (phase-3-spec.md)

| Change | Details |
|--------|---------|
| User Stories Added | 5 new stories (US-308 to US-312) |
| Functional Requirements Added | 19 new requirements (FR-329 to FR-347) |
| Task Entity Extended | Added `priority` (enum) and `tags` (JSON array) |
| Data Contracts Updated | Added `Priority` type, `TaskWithMetadata` interface |
| AI Intent Patterns Added | Priority, Tag, Search, Sort, Filter patterns |
| Acceptance Tests Added | 20+ new test cases |
| Version | 1.0.0 -> 2.0.0 |

### New User Stories

| ID | Title | Priority |
|----|-------|----------|
| US-308 | Set Task Priority via Chat | P1 |
| US-309 | Tag Tasks via Chat | P1 |
| US-310 | Search Tasks via Chat | P1 |
| US-311 | Sort Tasks via Chat | P2 |
| US-312 | Filter Tasks via Chat | P1 |

### Master Plan Updates (master-plan.md)

| Section | Changes |
|---------|---------|
| Section 1 | NEW: Database Evolution (Priority & Tags) |
| Section 2 | Extended MCP Tool Definitions (10 tools) |
| Section 3.2 | Updated System Prompt with priority/tag instructions |
| Section 8 | Updated Implementation Layers with new task IDs |
| Section 12 | Extended Acceptance Criteria |
| Section 14 | Added ADR candidates (ADR-011, ADR-012) |
| Version | 1.0.0 -> 2.0.0 |

### Database Evolution

```python
# New fields on Task model
priority: Priority = Field(default=Priority.MEDIUM)
tags: list[str] = Field(default_factory=list, sa_type=JSON)

# Priority enum
class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### MCP Tools (Extended)

| Tool | Category | Description |
|------|----------|-------------|
| `add_task` | Core | Create task (now with priority, tags) |
| `list_tasks` | Core | List tasks (now with filters, sort) |
| `complete_task` | Core | Toggle completion |
| `delete_task` | Core | Delete task |
| `update_task` | Core | Update task details |
| `search_tasks` | Extended | Keyword search with filters |
| `update_priority` | Extended | Change task priority |
| `add_tags` | Extended | Add tags to task |
| `remove_tags` | Extended | Remove tags from task |
| `list_tags` | Extended | Get user's unique tags |

### Tasks Generated (tasks.md)

| Layer | Tasks | Description |
|-------|-------|-------------|
| Layer 0 | T-301 to T-303 | Configuration & Dependencies |
| Layer 1 | T-304 to T-309 | Database Extension |
| Layer 2 | T-310 to T-313 | MCP Server |
| Layer 3 | T-314 to T-316 | Agent Integration |
| Layer 4 | T-317 to T-319 | Chat API |
| Layer 5 | T-320 to T-323 | Frontend Chat UI |
| Layer 6 | T-324 to T-328 | Integration & Testing |
| Layer 7 | T-329 to T-332 | Polish & Documentation |
| **Total** | **32** | 30 P1, 2 P2 |

### Files Modified

| File | Changes |
|------|---------|
| `specs/phase-3-spec.md` | +5 user stories, +19 FRs, entity extension |
| `specs/master-plan.md` | Database evolution, MCP tool upgrade, layer updates |
| `specs/tasks.md` | NEW: 32 atomic tasks |

### Quality Validation

- [x] All 12 user stories have acceptance scenarios
- [x] Functional requirements complete (FR-301 to FR-347)
- [x] Task entity extended with priority/tags
- [x] MCP tools expanded (5 core + 5 extended)
- [x] Implementation layers organized (8 layers)
- [x] Dependency graph documented
- [x] No [NEEDS CLARIFICATION] markers

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Priority as Enum | Type safety, limited values (high/medium/low) |
| Tags as JSON Array | Simpler than junction table, max 10 tags |
| Default Priority: Medium | Sensible default, doesn't require user input |
| Case-insensitive Search | Better UX, matches natural language |

## ADR Candidates

| ID | Title | Status |
|----|-------|--------|
| ADR-011 | Priority as Enum vs String | Proposed |
| ADR-012 | Tags as JSON Array | Proposed |

## Next Steps

1. `/sp.implement` - Execute tasks T-301 to T-332
2. Begin with Layer 0: Configuration & Dependencies
3. Run migrations for priority/tags on Neon DB

## Commit (Not Yet - Awaiting User Confirmation)

Files ready for commit:
- `phase-3-chatbot/specs/phase-3-spec.md`
- `phase-3-chatbot/specs/master-plan.md`
- `phase-3-chatbot/specs/tasks.md`
- `history/prompts/phase-3-chatbot/PHR-302-phase3-implementation-plan.md`

---

**End of PHR-302**
