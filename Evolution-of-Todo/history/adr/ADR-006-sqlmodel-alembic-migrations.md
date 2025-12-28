# ADR-006: SQLModel with Alembic for Database Migrations

**Status**: Accepted
**Date**: 2025-12-29
**Deciders**: Lead Architect, Backend Builder
**Applies To**: Phase II (Full-Stack Web Application)
**Supersedes**: ADR-003 (Volatile In-Memory Persistence)
**Related**: CL-003 (Clarification)

---

## Context

Phase II transitions from in-memory storage (Phase I) to persistent PostgreSQL database. A critical decision is how to manage database schema evolution:

**Problem Statement**: SQLModel (built on SQLAlchemy) provides `SQLModel.metadata.create_all()` for quick schema creation, but this approach lacks version control and migration capabilities.

**Constraints**:
1. Schema must evolve safely across deployments
2. Rollback capability is required for failed deployments
3. Team must review schema changes in code review
4. CI/CD pipeline must apply migrations automatically
5. Local development and production must stay in sync

**Technical Context**:
- SQLModel as ORM (based on SQLAlchemy Core + Pydantic)
- Neon Serverless PostgreSQL as database
- Multiple environments (local Docker, staging, production)

---

## Decision

**Adopt Alembic for all database migrations immediately. Do NOT use `SQLModel.metadata.create_all()` in any environment except for isolated test databases. All schema changes must go through version-controlled migration scripts.**

### Migration Workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Developer     │    │   Alembic       │    │   PostgreSQL    │
│   Changes Model │    │   Migration     │    │   Database      │
│                 │    │                 │    │                 │
│ Edit task.py    │───▶│ alembic revision│───▶│ ALTER TABLE     │
│ Add column      │    │ --autogenerate  │    │ ADD COLUMN      │
│                 │    │ Review & commit │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Project Structure

```
backend/
├── alembic/
│   ├── versions/           # Migration files (version controlled)
│   │   ├── 001_initial_schema.py
│   │   └── 002_add_user_preferences.py
│   ├── env.py              # Alembic configuration
│   └── script.py.mako      # Migration template
├── alembic.ini             # Connection string config
└── app/
    └── models/             # SQLModel definitions
        ├── user.py
        └── task.py
```

---

## Consequences

### Positive

| Benefit | Description |
|---------|-------------|
| Version Control | Every schema change is a reviewable commit |
| Rollback Support | `alembic downgrade` reverts failed migrations |
| Team Collaboration | PRs include migration files; changes reviewed |
| CI/CD Integration | `alembic upgrade head` in deployment pipeline |
| History Tracking | `alembic history` shows all schema evolution |
| Environment Parity | Same migrations run in dev, staging, production |

### Negative

| Drawback | Mitigation |
|----------|------------|
| Learning Curve | Document standard workflow; provide examples |
| Merge Conflicts | Sequential revision IDs; resolve heads with `alembic merge` |
| Initial Setup | One-time `alembic init` configuration |
| Test Database | Use `create_all()` only for isolated pytest fixtures |

### Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Migration failure in prod | Low | High | Test migrations in staging; backup before deploy |
| Data loss on rollback | Medium | High | Backup policy; destructive migrations marked |
| Divergent migration heads | Medium | Low | CI check for single head |

---

## Alternatives Considered

### Alternative 1: SQLModel.metadata.create_all()

**Approach**: Use built-in SQLModel/SQLAlchemy schema creation.

**Pros**:
- Zero configuration
- Fast for prototyping

**Cons**:
- No version control
- No rollback
- Cannot track what changed
- Destructive if tables exist

**Rejected Because**: Unacceptable for production; no audit trail or rollback.

### Alternative 2: Django-style Migrations (via third-party)

**Approach**: Use a Django-inspired migration tool like `aerich` (for Tortoise ORM).

**Pros**:
- More opinionated
- Automatic migration generation

**Cons**:
- Not compatible with SQLModel directly
- Would require ORM change

**Rejected Because**: Requires switching from SQLModel; added complexity.

### Alternative 3: Raw SQL Migrations (Flyway/dbmate)

**Approach**: Use SQL-based migration tools.

**Pros**:
- Pure SQL, no ORM dependency
- Works with any database

**Cons**:
- Manual SQL writing
- No Python model integration
- Duplicate schema definition

**Rejected Because**: Loses SQLModel's single-source-of-truth for models.

---

## Implementation Guidelines

### Initial Setup

```bash
cd backend
alembic init alembic

# Edit alembic/env.py to import SQLModel
```

### alembic/env.py Configuration

```python
from sqlmodel import SQLModel
from app.models.user import User
from app.models.task import Task
from app.core.config import get_settings

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = SQLModel.metadata
```

### Creating Migrations

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add user preferences column"

# Review generated file
cat alembic/versions/xxx_add_user_preferences_column.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run migrations
  run: |
    cd backend
    alembic upgrade head
```

### Forbidden Patterns

```python
# ❌ NEVER in production code
SQLModel.metadata.create_all(engine)

# ❌ NEVER bypass migrations
engine.execute("ALTER TABLE task ADD COLUMN ...")

# ✅ ONLY in isolated test fixtures
@pytest.fixture
def test_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)
```

---

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLModel with Alembic Tutorial](https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/)
- Phase 2 Specification: `phase-2-web/specs/spec.md` (Section: Clarifications CL-003)
- Phase 2 Data Model: `phase-2-web/specs/data-model.md`

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2025-12-29 | Lead Architect | Initial ADR created |
