# ADR-011: Task Schema Extension (Priority Enum + Tags JSON)

**Status**: Accepted
**Date**: 2026-01-04
**Deciders**: Lead Architect, Backend Builder
**Applies To**: Phase III (AI Chatbot Integration)
**Supersedes**: None
**Related**: ADR-006 (SQLModel with Alembic Migrations), master-plan.md Section 1

---

## Context

Phase III introduces Intermediate Level Features from the project constitution:
- Priorities (High/Medium/Low)
- Tags/Categories (Work, Home, etc.)
- Search & Filter
- Sort Tasks

**Problem Statement**: The Phase 2 Task model needs extension to support these features. Two key decisions:
1. How to represent priority (enum vs string vs integer)
2. How to store tags (JSON array vs junction table vs comma-separated string)

**Constraints**:
1. Constitution mandate: Priorities are High/Medium/Low (3 values only)
2. ADR-006: All schema changes must go through Alembic
3. Phase 2 compatibility: Existing tasks must continue working
4. PostgreSQL optimization: Leverage Neon PostgreSQL features
5. Query performance: Tags must be searchable

**Technical Context**:
- SQLModel as ORM (SQLAlchemy Core + Pydantic)
- Neon Serverless PostgreSQL (supports JSONB natively)
- Alembic for migrations with version control
- Existing Task model has: id, user_id, title, description, completed, created_at, updated_at

---

## Decision

### Priority: PostgreSQL Enum Type

**Adopt a PostgreSQL ENUM type for priority with Python Enum class.**

```python
# phase-3-chatbot/backend/app/models/task.py

from enum import Enum
from sqlmodel import Field, SQLModel

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(SQLModel, table=True):
    # ... existing fields ...

    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Task priority level",
    )
```

**Rationale**:
- Type safety at database and application level
- Only 3 valid values enforced by PostgreSQL
- No invalid data possible (vs. string)
- Clear semantics in code

### Tags: PostgreSQL JSON Array

**Adopt a JSON array column for tags with application-level validation.**

```python
# phase-3-chatbot/backend/app/models/task.py

from sqlalchemy import JSON
from sqlmodel import Field, SQLModel

class Task(SQLModel, table=True):
    # ... existing fields ...

    tags: list[str] = Field(
        default_factory=list,
        sa_type=JSON,
        description="Task categorization labels (max 10)",
    )
```

**Constraints enforced at application level**:
- Maximum 10 tags per task
- Maximum 50 characters per tag
- Case-insensitive matching for search

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Type Safety (Priority) | PostgreSQL ENUM prevents invalid values at DB level |
| Schema Simplicity (Tags) | No junction table needed; single column |
| Query Performance (Tags) | PostgreSQL JSON operators for containment queries |
| Default Values | Existing Phase 2 tasks get 'medium' priority and empty tags |
| Python Integration | Pydantic validates Priority enum; list[str] for tags |
| Migration Reversibility | Both columns can be dropped cleanly in downgrade |

### Negative

| Drawback | Mitigation |
|----------|------------|
| ENUM modification requires migration | Priority values are fixed by constitution |
| JSON not normalized | Max 10 tags limit keeps data manageable |
| Tag uniqueness not enforced | Application-level deduplication |
| No referential integrity for tags | Not needed; tags are user-defined labels |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| JSON query performance on large datasets | Low | Medium | Index with GIN if needed |
| Priority enum expansion needed | Very Low | Medium | Constitution limits to 3 values |
| Tag explosion (too many unique tags) | Medium | Low | UI shows tag suggestions from existing |
| Migration failure on Neon | Low | High | Test migration in staging first |

---

## Alternatives Considered

### Priority Alternatives

#### Alternative 1: String Column

**Approach**: `priority: str = "medium"`

**Pros**:
- Simple migration
- No enum type to manage

**Cons**:
- No type safety
- Invalid values possible (e.g., "urgent", "asap")
- Typos create data inconsistency

**Rejected Because**: Constitution mandates exactly 3 values; string allows unbounded values.

#### Alternative 2: Integer Column

**Approach**: `priority: int = 2` (1=high, 2=medium, 3=low)

**Pros**:
- Easy sorting by numeric value
- Compact storage

**Cons**:
- Magic numbers in code
- No semantic meaning in database
- Requires mapping layer

**Rejected Because**: Reduces code readability; ENUM provides same sorting with clarity.

### Tags Alternatives

#### Alternative 1: Junction Table

**Approach**: Separate `tags` and `task_tags` tables.

```sql
CREATE TABLE tags (
    id UUID PRIMARY KEY,
    name VARCHAR(50) UNIQUE,
    user_id UUID REFERENCES users(id)
);

CREATE TABLE task_tags (
    task_id UUID REFERENCES tasks(id),
    tag_id UUID REFERENCES tags(id),
    PRIMARY KEY (task_id, tag_id)
);
```

**Pros**:
- Normalized design
- Referential integrity
- Tag reuse and analytics

**Cons**:
- Two additional tables
- JOIN queries for every task fetch
- More complex migrations
- Over-engineering for current requirements

**Rejected Because**: Adds complexity without proportional benefit; constitution features don't require tag analytics.

#### Alternative 2: Comma-Separated String

**Approach**: `tags: str = "work,urgent,q1"`

**Pros**:
- Simplest migration
- Human-readable in database

**Cons**:
- Parsing required on every access
- No array operations
- Delimiter conflicts possible
- Query complexity for search

**Rejected Because**: PostgreSQL JSON provides native array operations; string parsing is error-prone.

#### Alternative 3: PostgreSQL ARRAY Type

**Approach**: `tags: list[str] = Field(sa_type=ARRAY(String))`

**Pros**:
- Native PostgreSQL array
- Array operators (@>, &&)

**Cons**:
- SQLModel/SQLAlchemy ARRAY handling is complex
- JSON is more portable across databases

**Rejected Because**: JSON has better SQLModel integration and similar query performance.

---

## Phase 2 Compatibility Guarantee

This decision explicitly protects Phase 2 deployment:

### Migration Safety

```python
# alembic/versions/20260104_002_add_priority_tags.py

def upgrade():
    # Step 1: Create ENUM type
    op.execute("CREATE TYPE priority AS ENUM ('high', 'medium', 'low')")

    # Step 2: Add priority column with DEFAULT (existing rows get 'medium')
    op.add_column('tasks', sa.Column(
        'priority',
        sa.Enum('high', 'medium', 'low', name='priority'),
        server_default='medium',  # CRITICAL: Preserves existing data
        nullable=False
    ))

    # Step 3: Add tags column with DEFAULT (existing rows get empty array)
    op.add_column('tasks', sa.Column(
        'tags',
        sa.JSON(),
        server_default='[]',  # CRITICAL: Preserves existing data
        nullable=False
    ))

def downgrade():
    op.drop_column('tasks', 'tags')
    op.drop_column('tasks', 'priority')
    op.execute("DROP TYPE priority")
```

### Backward Compatibility Guarantees

1. **Existing Tasks Unchanged**: All Phase 2 tasks automatically get `priority='medium'` and `tags=[]`
2. **REST API Continues**: Phase 2 endpoints don't require priority/tags parameters
3. **Optional Fields**: API accepts tasks without priority/tags (defaults apply)
4. **No Breaking Changes**: TaskCreate schema extended, not replaced

### API Schema Evolution

```python
# phase-3-chatbot/backend/app/api/v1/tasks.py

class TaskCreate(BaseModel):
    title: str
    description: str = ""
    priority: Priority = Priority.MEDIUM  # Optional, defaults to medium
    tags: list[str] = []                   # Optional, defaults to empty

class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str
    completed: bool
    priority: Priority      # Always included in response
    tags: list[str]         # Always included in response
    created_at: datetime
    updated_at: datetime
```

---

## Implementation Guidelines

### Model Definition

```python
# phase-3-chatbot/backend/app/models/task.py

from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import JSON
from sqlmodel import Field, SQLModel

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=1000)
    completed: bool = Field(default=False)
    priority: Priority = Field(default=Priority.MEDIUM)
    tags: list[str] = Field(default_factory=list, sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Query Examples

```python
# Search by priority
query = select(Task).where(Task.priority == Priority.HIGH)

# Search by tag (PostgreSQL JSON containment)
query = select(Task).where(Task.tags.contains(["work"]))

# Sort by priority (ENUM sorts alphabetically: high < low < medium)
# For correct ordering, use CASE or custom sort
query = select(Task).order_by(
    case(
        (Task.priority == Priority.HIGH, 1),
        (Task.priority == Priority.MEDIUM, 2),
        (Task.priority == Priority.LOW, 3),
    )
)
```

### Validation in TaskService

```python
# phase-3-chatbot/backend/app/services/task_service.py

MAX_TAGS = 10
MAX_TAG_LENGTH = 50

async def add_tags(self, user_id: UUID, task_id: UUID, tags: list[str]) -> Task:
    task = await self.get_task(user_id, task_id)
    if not task:
        raise TaskNotFoundError(task_id)

    # Validate and normalize tags
    normalized_tags = [t.strip().lower()[:MAX_TAG_LENGTH] for t in tags if t.strip()]

    # Merge and limit
    new_tags = list(set(task.tags + normalized_tags))[:MAX_TAGS]
    task.tags = new_tags

    return task
```

---

## References

- ADR-006: SQLModel with Alembic Migrations
- Phase 3 Master Plan: `phase-3-chatbot/specs/master-plan.md` (Section 1)
- Phase 3 Specification: `phase-3-chatbot/specs/phase-3-spec.md` (Task Entity Extension)
- PostgreSQL JSON Documentation: https://www.postgresql.org/docs/current/functions-json.html
- PostgreSQL ENUM Documentation: https://www.postgresql.org/docs/current/datatype-enum.html

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-01-04 | Backend Builder | Initial ADR created |

