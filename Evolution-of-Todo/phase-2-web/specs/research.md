# Phase 2 Research Findings

**Branch**: `phase-2-web-init`
**Date**: 2025-12-29
**Status**: Complete

---

## Summary

This document consolidates research findings from specialized agents to resolve technical unknowns and establish best practices for Phase 2 implementation.

---

## 1. Frontend Architecture (Next.js 15+ App Router)

### 1.1 Server Actions Structure

**Decision**: File-level `'use server'` in dedicated action files

**Rationale**:
- Cleaner separation of concerns
- Prevents accidental client-side imports of server code
- Better tree-shaking and bundle optimization

**Recommended Structure**:
```
frontend/
├── app/
│   ├── actions/              # Global server actions
│   │   ├── auth.ts           # login, logout, register
│   │   └── tasks.ts          # createTask, updateTask, deleteTask, toggleComplete
│   └── (dashboard)/
│       └── tasks/
│           └── actions.ts    # Route-specific actions (optional)
```

**Pattern**:
```typescript
// app/actions/tasks.ts
'use server'

import { cookies } from 'next/headers'
import { revalidatePath } from 'next/cache'

export async function createTask(formData: FormData) {
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')?.value

  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/tasks`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: formData.get('title'),
      description: formData.get('description'),
    }),
  })

  if (!response.ok) throw new Error('Failed to create task')

  revalidatePath('/dashboard')
  return await response.json()
}
```

### 1.2 Middleware for Cookie-to-Header Extraction

**Decision**: Implement in `middleware.ts` at project root

**Pattern**:
```typescript
// frontend/middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Protect dashboard routes
  if (request.nextUrl.pathname.startsWith('/dashboard')) {
    const token = request.cookies.get('auth-token')?.value
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url))
    }
  }

  // Inject auth header for API proxy requests
  if (request.nextUrl.pathname.startsWith('/api/')) {
    const token = request.cookies.get('auth-token')?.value
    const requestHeaders = new Headers(request.headers)

    if (token) {
      requestHeaders.set('Authorization', `Bearer ${token}`)
    }

    return NextResponse.next({
      request: { headers: requestHeaders },
    })
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*', '/login', '/register'],
}
```

### 1.3 Layout-based Authentication

**Decision**: Dashboard layout with cookies() check

**Pattern**:
```typescript
// app/(dashboard)/layout.tsx
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const cookieStore = await cookies()
  const token = cookieStore.get('auth-token')?.value

  if (!token) {
    redirect('/login')
  }

  // Optional: Verify token with backend
  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` },
    cache: 'no-store',
  })

  if (!response.ok) {
    redirect('/login')
  }

  const user = await response.json()

  return (
    <div className="dashboard-layout">
      <header>Welcome, {user.email}</header>
      <main>{children}</main>
    </div>
  )
}
```

### 1.4 API Proxy Configuration

**Decision**: next.config.js rewrites to eliminate CORS

**Pattern**:
```javascript
// frontend/next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
```

---

## 2. Backend Architecture (FastAPI + SQLModel)

### 2.1 Project Structure

**Decision**: Standard FastAPI layered architecture

**Recommended Structure**:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependency injection (get_current_user)
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py       # APIRouter aggregation
│   │       ├── auth.py         # /api/v1/auth/* endpoints
│   │       └── tasks.py        # /api/v1/tasks/* endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Pydantic Settings
│   │   ├── security.py         # JWT encode/decode, password hashing
│   │   └── database.py         # SQLModel engine, session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLModel
│   │   └── task.py             # Task SQLModel
│   └── services/
│       ├── __init__.py
│       ├── auth_service.py     # Register, login logic
│       └── task_service.py     # CRUD + business logic
├── alembic/
│   ├── versions/               # Migration files
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── pyproject.toml
└── CLAUDE.md
```

### 2.2 JWT Verification Middleware

**Decision**: FastAPI Dependency Injection with `Depends()`

**Pattern**:
```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from uuid import UUID

from app.core.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """Extract and validate user_id from JWT token."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "AUTH_INVALID", "message": "Invalid token claims"}
            )
        return UUID(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_INVALID", "message": "Invalid or expired token"}
        )
```

**Usage in endpoints**:
```python
# backend/app/api/v1/tasks.py
from fastapi import APIRouter, Depends
from uuid import UUID

from app.api.deps import get_current_user
from app.services.task_service import TaskService

router = APIRouter()

@router.get("/tasks")
async def list_tasks(user_id: UUID = Depends(get_current_user)):
    return await TaskService.list_tasks(user_id)
```

### 2.3 SQLModel Best Practices

**UUID Primary Keys**:
```python
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    email: str = Field(max_length=254, unique=True, index=True)

class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

**One-to-Many Relationships**:
```python
from typing import List, Optional
from sqlmodel import Relationship

class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    # ... other fields
    tasks: List["Task"] = Relationship(back_populates="user")

class Task(TaskBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    user: Optional[User] = Relationship(back_populates="tasks")
```

### 2.4 Alembic Setup

**Initialization**:
```bash
cd backend
alembic init alembic
```

**Configure env.py**:
```python
# backend/alembic/env.py
from sqlmodel import SQLModel
from app.models import User, Task  # Import all models
from app.core.config import settings

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
target_metadata = SQLModel.metadata
```

**Create migration**:
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## 3. DevOps: Local Development Environment

### 3.1 Docker Compose for PostgreSQL

**Decision**: PostgreSQL 16 Alpine with health checks

**docker-compose.yml**:
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:16-alpine
    container_name: todo_postgres_dev
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-todo_db}
      POSTGRES_USER: ${POSTGRES_USER:-todo_user}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-todo_user} -d ${POSTGRES_DB:-todo_db}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - todo_network

volumes:
  postgres_data:

networks:
  todo_network:
```

### 3.2 Environment Variables

**.env.example**:
```bash
# Database
POSTGRES_DB=todo_db
POSTGRES_USER=todo_user
POSTGRES_PASSWORD=dev_password_change_me
DATABASE_URL=postgresql://todo_user:dev_password_change_me@localhost:5432/todo_db

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
JWT_SECRET=replace_with_32_char_secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION=86400

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

---

## 4. Schema Evolution: Phase 1 to Phase 2

### 4.1 Field Mapping

| Phase 1 (dataclass) | Phase 2 (SQLModel) | Change |
|---------------------|-------------------|--------|
| `id: int` | `id: UUID` | Type change (breaking) |
| N/A | `user_id: UUID` | New field (multi-tenancy) |
| `title: str` | `title: str` | No change |
| `description: str` | `description: str` | No change |
| `completed: bool` | `completed: bool` | No change |
| `created_at: datetime` | `created_at: datetime` | No change |
| N/A | `updated_at: datetime` | New field |

### 4.2 Decision: No Migration Path

**Rationale**: Phase 1 used volatile in-memory storage. There is no data to migrate. Phase 2 starts with a clean database.

### 4.3 Service Layer Porting

Phase 1 `TodoService` methods map to Phase 2 as follows:

| Phase 1 Method | Phase 2 Method | Signature Change |
|----------------|----------------|------------------|
| `add_task(title, description)` | `create_task(user_id, title, description)` | +user_id, async |
| `get_all_tasks()` | `list_tasks(user_id)` | +user_id, async |
| `get_task(task_id)` | `get_task(user_id, task_id)` | +user_id, async, UUID |
| `update_task(task_id, title, description)` | `update_task(user_id, task_id, title, description)` | +user_id, async, UUID |
| `delete_task(task_id)` | `delete_task(user_id, task_id)` | +user_id, async, UUID |
| `mark_complete(task_id)` | `toggle_complete(user_id, task_id)` | +user_id, async, UUID |

---

## 5. API Validation Report

### 5.1 Endpoint Coverage

| # | Endpoint | Specified | Notes |
|---|----------|-----------|-------|
| 1 | GET `/api/v1/tasks` | EP-001 | List tasks |
| 2 | POST `/api/v1/tasks` | EP-002 | Create task |
| 3 | GET `/api/v1/tasks/{task_id}` | EP-003 | Get task |
| 4 | PUT `/api/v1/tasks/{task_id}` | EP-004 | Update task |
| 5 | DELETE `/api/v1/tasks/{task_id}` | EP-005 | Delete task |
| 6 | PATCH `/api/v1/tasks/{task_id}/complete` | EP-006 | Toggle complete |
| 7 | POST `/api/v1/auth/register` | spec.md | Register |
| 8 | POST `/api/v1/auth/login` | spec.md | Login |
| 9 | POST `/api/v1/auth/logout` | spec.md | Logout |
| 10 | GET `/api/v1/auth/me` | spec.md | Get user |

**Status**: All 10 endpoints accounted for.

### 5.2 Response Envelope Compliance

All endpoints must return:
```typescript
// Success
{ success: true, data: T, meta?: {...} }

// Error
{ success: false, error: { code: string, message: string, details?: {...} } }
```

**Status**: Verified in all endpoint specifications.

---

## 6. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Better Auth complexity | Medium | Medium | Use simple custom JWT if needed |
| Neon cold starts | Low | Low | Documented as acceptable |
| TypeScript/Python type drift | Medium | Medium | Single source: SQLModel generates types |
| Deadline passed | Confirmed | N/A | Focus on P1 stories only |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Research Agents | Initial research compilation |

---

**End of Research Document**
