# Backend Implementation Guide

## Overview

FastAPI backend for the Evolution of Todo application (Phase 2).

## Tech Stack

- **Framework**: FastAPI 0.115+
- **ORM**: SQLModel
- **Database**: PostgreSQL (Neon Serverless in production)
- **Migrations**: Alembic
- **Auth**: JWT (python-jose) + bcrypt (passlib)
- **Package Manager**: UV

## Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── api/
│   │   ├── deps.py          # Dependency injection (JWT auth)
│   │   └── v1/
│   │       ├── router.py    # API router aggregation
│   │       ├── auth.py      # Auth endpoints
│   │       └── tasks.py     # Task endpoints
│   ├── core/
│   │   ├── config.py        # Pydantic Settings
│   │   ├── security.py      # JWT + bcrypt
│   │   └── database.py      # SQLModel engine/session
│   ├── models/
│   │   ├── user.py          # User model
│   │   └── task.py          # Task model
│   └── services/
│       ├── auth_service.py  # Register, login logic
│       └── task_service.py  # CRUD operations
├── alembic/
│   ├── versions/            # Migration files
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── pyproject.toml
└── tests/
    ├── conftest.py
    ├── test_auth.py
    └── test_tasks.py
```

## Commands

```bash
# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --port 8000

# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Run tests
uv run pytest -v

# Type check (via ruff)
uv run ruff check .
```

## Architecture Decisions

| Decision | Reference |
|----------|-----------|
| JWT in httpOnly cookie | ADR-004 |
| Alembic for migrations | ADR-006 |
| Port Phase 1 logic | ADR-007 |

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Get JWT token
- `POST /auth/logout` - Invalidate session (client-side)
- `GET /auth/me` - Get current user

### Tasks (requires auth)
- `GET /tasks` - List user's tasks
- `POST /tasks` - Create task
- `GET /tasks/{id}` - Get task
- `PUT /tasks/{id}` - Update task
- `DELETE /tasks/{id}` - Delete task
- `PATCH /tasks/{id}/complete` - Toggle completion

## Response Format

```json
// Success
{"success": true, "data": {...}}

// Error
{"success": false, "error": {"code": "ERROR_CODE", "message": "..."}}
```

## Multi-Tenancy

All task queries MUST include `WHERE user_id = :current_user_id` to enforce data isolation. The `user_id` is extracted from the JWT token in the `get_current_user` dependency.
