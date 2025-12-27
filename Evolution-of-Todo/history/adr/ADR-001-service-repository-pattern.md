# ADR-001: Service-Repository Pattern for In-Memory App

> **Scope**: Architectural pattern decision for Phase I that enables Brownfield Evolution to Phase II.

- **Status:** Accepted
- **Date:** 2025-12-27
- **Feature:** 001-core-crud
- **Context:** Phase I requires a simple Python console app with in-memory storage. However, the Constitution mandates "Iterative Evolution (Brownfield Protocol)" where each phase builds on the previous. Phase II will migrate to SQLModel + Neon PostgreSQL. The question: should Phase I use a simple script approach or implement abstraction layers?

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - defines code structure for all phases
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - direct access vs patterns
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - affects all CRUD operations
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

Implement **Service-Repository Pattern** even for the in-memory Phase I application:

- **Model Layer**: `Task` dataclass in `src/models/task.py`
- **Repository Layer**: `TodoRepository` class in `src/repositories/memory_repo.py`
  - Encapsulates `dict[int, Task]` storage
  - Handles ID generation
  - Provides CRUD operations
- **Service Layer**: `TodoService` class in `src/services/todo_service.py`
  - Accepts `TodoRepository` via constructor injection
  - Handles validation (empty titles, length limits)
  - Orchestrates business operations
- **Presentation Layer**: REPL loop in `src/main.py`
  - Only calls `TodoService` methods
  - Handles user input/output formatting

## Consequences

### Positive

- **Phase II Migration Path**: Only need to replace `MemoryRepository` with `SQLModelRepository`; Service layer remains unchanged
- **Testability**: Service layer can be unit tested with mock repositories
- **Separation of Concerns**: Validation logic isolated from storage logic
- **Constitution Compliance**: Aligns with "Iterative Evolution" principle
- **Professional Practice**: Mirrors real-world application architecture

### Negative

- **Added Complexity**: Simple 100-line script becomes multi-file architecture
- **Overkill for Phase I Scope**: In-memory app doesn't need abstraction for functionality alone
- **Learning Curve**: Contributors must understand layered architecture
- **More Boilerplate**: Extra classes and imports compared to minimal approach

## Alternatives Considered

### Alternative A: Direct Dictionary Access

```python
# All in main.py
tasks = {}
next_id = 1

def add_task(title):
    global next_id
    tasks[next_id] = {"title": title, "completed": False}
    next_id += 1
```

**Why Rejected**: No abstraction means Phase II requires complete rewrite. Violates "Iterative Evolution" principle. Mixes validation with storage.

### Alternative B: Active Record Pattern

```python
@dataclass
class Task:
    id: int
    title: str

    def save(self):
        storage[self.id] = self
```

**Why Rejected**: Mixes data structure with persistence. Harder to swap storage implementation. Less flexible than Repository pattern.

### Alternative C: Repository-Only (No Service)

```python
class TodoRepository:
    def add(self, title):
        # validation + storage combined
```

**Why Rejected**: Mixes validation with storage. Service layer provides cleaner separation and makes testing easier.

## References

- Feature Spec: [specs/001-core-crud/spec.md](../../specs/001-core-crud/spec.md)
- Implementation Plan: [specs/001-core-crud/plan.md](../../specs/001-core-crud/plan.md)
- Related ADRs: None (first ADR)
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Section II: Iterative Evolution
