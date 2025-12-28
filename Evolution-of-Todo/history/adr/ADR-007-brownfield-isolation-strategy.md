# ADR-007: Brownfield Isolation Strategy

**Status**: Accepted
**Date**: 2025-12-29
**Deciders**: Lead Architect, Imperator
**Applies To**: Phase II (Full-Stack Web Application)
**Supersedes**: N/A
**Related**: Constitution (Brownfield Protocol)

---

## Context

The Evolution of Todo project follows a "Brownfield Protocol" where each phase builds on the previous. Phase I produced a console application in `phase-1-console/`, and Phase II must evolve this into a full-stack web application.

**Problem Statement**: How should Phase II code relate to Phase I code? Should Phase II import from Phase I, copy code, or rewrite entirely?

**Constraints**:
1. Constitution mandates "evolve, not rewrite" (Brownfield Protocol)
2. Phase I is sealed (69 tests passing, no further changes)
3. Phase II has different requirements (multi-tenant, async, UUID IDs)
4. Monorepo structure must remain clean and navigable
5. Future phases must not break past phases

**Technical Context**:
- Phase I: Python 3.13+, dataclasses, in-memory storage, sequential IDs
- Phase II: Python 3.13+, SQLModel, PostgreSQL, UUID IDs, async
- Breaking changes: ID type (int → UUID), user scoping (single → multi-tenant)

---

## Decision

**Phase II must NOT import directly from `phase-1-console/`. Business logic must be "Ported" (copied and adapted) to `phase-2-web/backend/`. This maintains clean isolation between phases while honoring the Brownfield Protocol through conceptual evolution, not code sharing.**

### Isolation Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                         MONOREPO                                 │
│                                                                  │
│  ┌──────────────────────┐    ┌──────────────────────┐          │
│  │   phase-1-console/   │    │   phase-2-web/       │          │
│  │   (SEALED)           │    │   backend/           │          │
│  │                      │    │                      │          │
│  │   src/               │    │   app/               │          │
│  │   ├── models/        │ X  │   ├── models/        │          │
│  │   │   └── task.py    │────│   │   └── task.py    │          │
│  │   ├── services/      │ X  │   ├── services/      │          │
│  │   │   └── todo_svc   │────│   │   └── task_svc   │          │
│  │   └── repositories/  │ NO │   └── (SQLModel)     │          │
│  │       └── memory_repo│IMPORT│                     │          │
│  │                      │    │                      │          │
│  └──────────────────────┘    └──────────────────────┘          │
│                                                                  │
│  ✗ FORBIDDEN: from phase-1-console.src.models import Task      │
│  ✓ ALLOWED: Port Task concept, adapt to SQLModel                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### What "Porting" Means

1. **Study Phase I Logic**: Read `phase-1-console/src/services/todo_service.py`
2. **Extract Business Rules**: Title validation (1-200 chars), completion toggle, etc.
3. **Implement in Phase II Context**: Async, multi-tenant, SQLModel
4. **Do NOT Copy-Paste**: Adapt patterns, not code

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Clean Boundaries | Each phase is self-contained and testable |
| Independent Evolution | Phase II can evolve without affecting Phase I |
| Clear Ownership | Phase I remains sealed; Phase II has fresh tests |
| No Import Conflicts | Different Python environments per phase |
| Honest Documentation | Each phase documents its own architecture |

### Negative

| Drawback | Mitigation |
|----------|------------|
| Code Duplication | Acceptable; each phase has different requirements |
| Business Logic Drift | Document ported patterns; reference Phase I in comments |
| No Shared Library | Could create `shared/` later; premature for Phase II |
| Effort to Port | One-time cost; logic is well-documented in specs |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Accidental Phase I import | Low | Medium | CI check: no cross-phase imports |
| Logic divergence | Medium | Low | Acceptance tests verify behavior parity |
| Future refactoring difficulty | Low | Low | Each phase stands alone |

---

## Alternatives Considered

### Alternative 1: Direct Imports from Phase I

**Approach**: `from phase_1_console.src.services import TodoService`

**Pros**:
- True code reuse
- Single source of truth

**Cons**:
- Tight coupling across phases
- Changes to Phase I break Phase II
- Conflicting requirements (int vs UUID)
- Phase I would need to be "unsealed"

**Rejected Because**: Violates phase isolation; risks regression in sealed Phase I.

### Alternative 2: Shared Library Package

**Approach**: Create `shared/` package with common business logic.

**Pros**:
- Clean abstraction
- True DRY principle

**Cons**:
- Premature abstraction
- Overhead of maintaining shared code
- Requirements differ significantly (sync vs async, int vs UUID)

**Rejected Because**: Premature optimization; Phase II requirements differ too much.

### Alternative 3: Complete Rewrite

**Approach**: Ignore Phase I entirely; write Phase II from scratch.

**Pros**:
- No legacy constraints
- Fresh design

**Cons**:
- Violates Constitution's Brownfield Protocol
- Loses validated business rules
- More effort to rediscover edge cases

**Rejected Because**: Constitution mandates evolution; Phase I insights are valuable.

---

## Porting Guidelines

### Phase I → Phase II Mapping

| Phase I | Phase II | Adaptation |
|---------|----------|------------|
| `Task` dataclass | `Task` SQLModel | Add `user_id`, change `id` to UUID |
| `TodoService` | `TaskService` | Add `user_id` to all methods, async |
| `MemoryRepository` | SQLModel session | Replace in-memory dict with DB queries |
| Sequential int IDs | UUID IDs | Security: prevent enumeration |
| Single user | Multi-tenant | All queries scoped by `user_id` |

### Validation Rules to Port

```python
# Phase I: phase-1-console/src/services/todo_service.py
MAX_TITLE_LENGTH = 200  # Port this constant

# Phase II: phase-2-web/backend/app/services/task_service.py
MAX_TITLE_LENGTH = 200  # Ported from Phase I

def _validate_title(title: str) -> str:
    """Ported from Phase I TodoService._validate_title"""
    if not title or not title.strip():
        raise ValueError("Title cannot be empty")
    title = title.strip()
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError(f"Title cannot exceed {MAX_TITLE_LENGTH} characters")
    return title
```

### Forbidden Patterns

```python
# ❌ NEVER
from phase_1_console.src.models import Task
from phase_1_console.src.services import TodoService

# ❌ NEVER
import sys
sys.path.insert(0, '../phase-1-console')

# ✅ ALLOWED - Reference in comments
# Ported from Phase I: phase-1-console/src/services/todo_service.py:45
MAX_TITLE_LENGTH = 200
```

---

## Verification

### CI Check (Recommended)

```yaml
# .github/workflows/isolation-check.yml
- name: Check Phase Isolation
  run: |
    # Fail if any phase-2 file imports from phase-1
    if grep -r "from phase_1_console" phase-2-web/; then
      echo "ERROR: Cross-phase import detected"
      exit 1
    fi
```

### Manual Check

```bash
# Should return no results
grep -r "phase_1_console" phase-2-web/
grep -r "phase-1-console" phase-2-web/backend/
```

---

## References

- Constitution: `.specify/memory/constitution.md` (Brownfield Protocol section)
- Phase I Specification: `phase-1-console/specs/001-core-crud/spec.md`
- Phase I Implementation: `phase-1-console/src/services/todo_service.py`
- Phase 2 Specification: `phase-2-web/specs/spec.md` (Migration Notes section)

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-29 | Lead Architect | Initial ADR created |
