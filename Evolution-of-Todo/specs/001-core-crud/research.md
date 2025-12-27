# Research: Phase I Core CRUD Console App

**Feature**: 001-core-crud
**Date**: 2025-12-27
**Status**: Complete

---

## Technical Decisions

### 1. CLI Framework Selection

**Decision**: Python standard library (`input()` + custom REPL loop)

**Rationale**:
- Constitution mandates "No external dependencies beyond Python standard library" for Phase I
- Interactive REPL pattern is simple to implement with `while True` loop
- Menu-driven approach aligns with clarified spec requirement
- Keeps the codebase minimal and focused

**Alternatives Considered**:
| Alternative | Rejected Because |
|------------|------------------|
| `typer` | External dependency violates Phase I constraints |
| `click` | External dependency violates Phase I constraints |
| `cmd` module | More complex than needed for menu-driven UI |
| `argparse` | Better for single-command CLI, not REPL |

---

### 2. Data Model Implementation

**Decision**: Python `dataclass` with `field()` defaults

**Rationale**:
- Native Python, no external dependencies
- Clean, readable, and supports type hints
- Easy to convert to SQLModel in Phase II (similar syntax)
- Auto-generates `__init__`, `__repr__`, `__eq__`

**Alternatives Considered**:
| Alternative | Rejected Because |
|------------|------------------|
| Plain `dict` | No type safety, harder to refactor |
| `NamedTuple` | Immutable, can't update fields |
| `Pydantic` | External dependency |
| Custom class | More boilerplate than dataclass |

---

### 3. ID Generation Strategy

**Decision**: Sequential integer counter (auto-increment from 1)

**Rationale**:
- Spec explicitly states "auto-generated sequential integer starting from 1"
- Simple implementation with class-level counter
- Easy for users to reference tasks by ID
- Sufficient for single-user, in-memory application

**Alternatives Considered**:
| Alternative | Rejected Because |
|------------|------------------|
| UUID | Overkill for Phase I; harder for users to type |
| Timestamp-based | Potential collisions, not user-friendly |
| Random int | No sequential ordering, potential collisions |

---

### 4. Storage Pattern

**Decision**: Service-Repository Pattern with in-memory dictionary

**Rationale**:
- User explicitly requested this pattern for Phase II evolution
- Repository encapsulates storage (easy to swap dict → SQLModel)
- Service layer handles validation and business logic
- Clean separation of concerns aligns with Constitution

**Implementation**:
```
CLI (UI) → TodoService (Logic) → TodoRepository (Storage) → dict
```

**Alternatives Considered**:
| Alternative | Rejected Because |
|------------|------------------|
| Direct dict access | No abstraction, harder to evolve to Phase II |
| Active Record pattern | Mixes data + persistence, less flexible |
| ORM directly | External dependency for Phase I |

---

### 5. Testing Framework

**Decision**: `pytest` with Service layer focus

**Rationale**:
- `pytest` is the de-facto Python testing standard
- Service layer tests validate business logic without CLI coupling
- Repository tests validate storage operations
- Minimal external dependency (acceptable for testing)

**Test Strategy**:
- Unit tests: Service methods (validation, CRUD logic)
- Unit tests: Repository methods (storage operations)
- Integration tests: Service + Repository together
- Manual tests: Full REPL flow verification

---

### 6. Project Structure

**Decision**: Layered architecture in `src/` directory

**Rationale**:
- Constitution specifies `src/` for Phase I code
- Service-Repository pattern requires clear module separation
- Easy to migrate to `backend/app/services/` in Phase II

**Structure**:
```
src/
├── __init__.py
├── main.py              # Entry point + REPL loop
├── models/
│   ├── __init__.py
│   └── task.py          # Task dataclass
├── repositories/
│   ├── __init__.py
│   └── memory_repo.py   # In-memory dict storage
└── services/
    ├── __init__.py
    └── todo_service.py  # Business logic + validation
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| ID collision on restart | Expected behavior (in-memory); will be fixed in Phase II |
| Data loss on exit | Documented in spec as expected Phase I behavior |
| No input sanitization | Title truncation at 200 chars; special chars allowed |
| No concurrent access | Single-user assumption documented in spec |

---

## Dependencies Summary

| Type | Dependency | Version | Purpose |
|------|------------|---------|---------|
| Runtime | Python | 3.13+ | Core runtime |
| Package Manager | uv | latest | Dependency management |
| Testing | pytest | latest | Test framework |

---

## Constitution Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Spec-Driven Development | PASS | Plan derived from approved spec |
| II. Iterative Evolution | PASS | Structure supports Phase II migration |
| III. Test-First Mindset | PASS | pytest tests planned for Service layer |
| IV. Smallest Viable Diff | PASS | Only essential components included |
| V. Intelligence Capture | PASS | PHR will be created |

---

**Research Status**: All NEEDS CLARIFICATION resolved. Ready for Phase 1 Design.
