# ADR-008: SQLite Development Fallback

## Status
Accepted

## Date
2025-12-30

## Context

During Phase 2 development, the team encountered situations where Docker Desktop was unavailable or impractical for local development. The Constitution mandates "Neon Serverless PostgreSQL" for Phase II, but this requires either:

1. A Docker container running PostgreSQL locally
2. Network access to Neon cloud database
3. Docker Desktop installed and running

When none of these are available, developers cannot run or test the backend locally.

## Decision

Implement SQLite as an **environment-configurable development fallback** that:

1. Is controlled entirely via `DATABASE_URL` environment variable
2. Uses `aiosqlite` driver for async compatibility with SQLModel/SQLAlchemy
3. Automatically detects database type from URL prefix (`sqlite` vs `postgresql`)
4. Preserves PostgreSQL-specific configuration (connection pooling) for production

### Implementation

```python
# app/core/database.py
def _is_sqlite_url(url: str) -> bool:
    return url.startswith("sqlite")

def _create_engine_for_url(url: str):
    if _is_sqlite_url(url):
        return create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False}
        )
    else:
        return create_async_engine(
            url,
            echo=False,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
```

### Environment Configuration

```bash
# Development (SQLite)
DATABASE_URL=sqlite+aiosqlite:///./todo_dev.db

# Production (Neon PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?sslmode=require
```

## Consequences

### Positive

- **Zero Docker requirement** for local development
- **No code changes** needed to switch databases - only env var
- **Faster onboarding** for new developers
- **CI/CD flexibility** - tests can run without PostgreSQL service

### Negative

- **Feature parity gaps** between SQLite and PostgreSQL:
  - SQLite `onupdate` triggers may not auto-update `updated_at` columns
  - UUID storage differs (string in SQLite vs native in PostgreSQL)
  - Advanced PostgreSQL features (JSONB, arrays) unavailable

### Mitigations

1. All production deployments MUST use PostgreSQL (`postgresql+asyncpg://`)
2. CI/CD pipelines SHOULD test against PostgreSQL in addition to SQLite
3. SQLite database files (`*.db`) are gitignored

## Constraints

- **SQLite MUST NOT be used in production** - only for local development
- **Tests SHOULD pass on both** SQLite and PostgreSQL
- **Migrations** remain Alembic-managed; SQLite creates tables on startup for dev convenience

## Related ADRs

- ADR-006: SQLModel with Alembic for Migrations
- ADR-007: Brownfield Isolation Strategy

## References

- [SQLAlchemy AsyncIO Documentation](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [aiosqlite PyPI](https://pypi.org/project/aiosqlite/)
