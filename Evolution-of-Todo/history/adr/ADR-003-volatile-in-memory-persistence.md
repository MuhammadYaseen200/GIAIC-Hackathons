# ADR-003: Volatile In-Memory Persistence (No File I/O)

> **Scope**: Data persistence strategy for Phase I, explicitly accepting data loss to prevent scope creep.

- **Status:** Accepted
- **Date:** 2025-12-27
- **Feature:** 001-core-crud
- **Context:** Phase I is a console application with in-memory storage. Users expect their tasks to persist between runs, but implementing file persistence (JSON, CSV, SQLite) would add complexity and potentially create technical debt that doesn't align with Phase II's PostgreSQL migration. The question: should Phase I implement any persistence mechanism?

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - defines data lifecycle expectations
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - file I/O vs pure memory
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - affects user expectations and testing
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

**Explicitly accept data volatility** for Phase I:

- **Storage**: Python `dict[int, Task]` in `TodoRepository`
- **Lifecycle**: Data exists only during application runtime
- **On Exit**: All tasks are lost
- **On Restart**: ID counter resets to 1
- **No File I/O**: No JSON, CSV, pickle, or SQLite

**User Communication**:
- Spec documents this as "expected behavior"
- Manual verification checklist confirms data loss on exit
- Future phases explicitly address persistence via Neon PostgreSQL

## Consequences

### Positive

- **Scope Control**: Prevents feature creep ("just add JSON export!")
- **Clean Migration**: No legacy file format to migrate in Phase II
- **Simplicity**: No file handling, encoding issues, or corruption risks
- **Testing**: State resets between test runs naturally
- **Focus**: Phase I validates CRUD logic, not persistence mechanisms
- **Constitution Alignment**: "Smallest Viable Diff" - only implement what's specified

### Negative

- **User Confusion**: Users may expect data to persist (familiar from other apps)
- **Limited Demo Value**: Can't showcase "returning user" scenario
- **No Recovery**: Accidental exit loses all work
- **ID Collision**: New session starts from ID 1, potential confusion if user remembers old IDs

## Alternatives Considered

### Alternative A: JSON File Persistence

```python
import json

def save_tasks():
    with open("tasks.json", "w") as f:
        json.dump(tasks, f)
```

**Why Rejected**:
- Adds file I/O complexity not in spec
- Creates migration burden for Phase II (JSON → PostgreSQL)
- Potential encoding/corruption issues
- Feature creep risk (export, import, backup, etc.)
- Constitution violation: adds unspecified features

### Alternative B: SQLite Local Database

```python
import sqlite3
conn = sqlite3.connect("tasks.db")
```

**Why Rejected**:
- Phase II uses PostgreSQL via SQLModel; SQLite would be throwaway
- Adds schema management complexity
- Different SQL dialect from Neon PostgreSQL
- Overkill for Phase I scope

### Alternative C: Pickle Serialization

```python
import pickle

def save_state():
    with open("state.pkl", "wb") as f:
        pickle.dump(repository, f)
```

**Why Rejected**:
- Security concerns with pickle (arbitrary code execution)
- Binary format not human-readable
- Same migration burden as JSON
- Not aligned with Phase II architecture

### Alternative D: CSV Export/Import

**Why Rejected**:
- Adds parsing complexity
- No schema enforcement
- Creates user expectation for data management features
- Not aligned with spec requirements

## References

- Feature Spec: [specs/001-core-crud/spec.md](../../specs/001-core-crud/spec.md) - FR-010: In-memory storage
- Implementation Plan: [specs/001-core-crud/plan.md](../../specs/001-core-crud/plan.md) - Data Volatility Notice
- Data Model: [specs/001-core-crud/data-model.md](../../specs/001-core-crud/data-model.md) - Storage Schema section
- Related ADRs:
  - [ADR-001](./ADR-001-service-repository-pattern.md) - Service-Repository Pattern (enables easy swap to DB)
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Principle IV: Smallest Viable Diff
