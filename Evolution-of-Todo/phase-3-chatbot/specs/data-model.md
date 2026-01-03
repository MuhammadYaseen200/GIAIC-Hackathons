# Data Model Specification: Phase 2

**Branch**: `phase-2-web-init`
**Date**: 2025-12-29
**Status**: Complete

---

## 1. Entity Overview

### 1.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────┐
│                         User                             │
├─────────────────────────────────────────────────────────┤
│  id: UUID (PK)                                          │
│  email: VARCHAR(254) UNIQUE                             │
│  password_hash: VARCHAR(255)                            │
│  created_at: TIMESTAMPTZ                                │
└─────────────────────────────────────────────────────────┘
                          │
                          │ 1:N (One User has Many Tasks)
                          │ ON DELETE CASCADE
                          ▼
┌─────────────────────────────────────────────────────────┐
│                         Task                             │
├─────────────────────────────────────────────────────────┤
│  id: UUID (PK)                                          │
│  user_id: UUID (FK → User.id)                           │
│  title: VARCHAR(200) NOT NULL                           │
│  description: VARCHAR(1000) DEFAULT ''                  │
│  completed: BOOLEAN DEFAULT FALSE                       │
│  created_at: TIMESTAMPTZ                                │
│  updated_at: TIMESTAMPTZ                                │
└─────────────────────────────────────────────────────────┘
```

---

## 2. User Entity

### 2.1 SQLModel Definition

```python
from datetime import datetime
from typing import List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .task import Task

class UserBase(SQLModel):
    """Base User model with shared fields."""
    email: str = Field(
        max_length=254,
        unique=True,
        index=True,
        description="User email address"
    )

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(min_length=8)

class User(UserBase, table=True):
    """User database model."""
    __tablename__ = "user"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique user identifier"
    )
    password_hash: str = Field(
        description="bcrypt hashed password"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Account creation timestamp"
    )

    # Relationships
    tasks: List["Task"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class UserRead(UserBase):
    """Schema for user responses (excludes password)."""
    id: UUID
    created_at: datetime
```

### 2.2 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique identifier |
| `email` | VARCHAR(254) | UNIQUE, NOT NULL, indexed | RFC 5322 compliant email |
| `password_hash` | VARCHAR(255) | NOT NULL | bcrypt hash with cost 12 |
| `created_at` | TIMESTAMPTZ | NOT NULL, auto-generated | UTC timestamp |

### 2.3 Validation Rules

- **email**: Must match RFC 5322 email format
- **password** (input): Minimum 8 characters
- **email uniqueness**: Enforced at database level

---

## 3. Task Entity

### 3.1 SQLModel Definition

```python
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User

class TaskBase(SQLModel):
    """Base Task model with shared fields."""
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Task title"
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Optional task description"
    )

class TaskCreate(TaskBase):
    """Schema for task creation."""
    pass

class TaskUpdate(SQLModel):
    """Schema for task updates (all fields optional)."""
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000
    )

class Task(TaskBase, table=True):
    """Task database model."""
    __tablename__ = "task"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique task identifier"
    )
    user_id: UUID = Field(
        foreign_key="user.id",
        index=True,
        description="Owner user ID"
    )
    completed: bool = Field(
        default=False,
        description="Completion status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="Last modification timestamp"
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="tasks")

class TaskRead(TaskBase):
    """Schema for task responses."""
    id: UUID
    user_id: UUID
    completed: bool
    created_at: datetime
    updated_at: datetime
```

### 3.2 Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PK, auto-generated | Unique task identifier |
| `user_id` | UUID | FK(user.id), NOT NULL, indexed | Task owner |
| `title` | VARCHAR(200) | NOT NULL, 1-200 chars | Task title |
| `description` | VARCHAR(1000) | DEFAULT '' | Optional description |
| `completed` | BOOLEAN | DEFAULT FALSE | Completion status |
| `created_at` | TIMESTAMPTZ | NOT NULL, auto-generated | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, auto-updated | Last modification |

### 3.3 Validation Rules

- **title**: 1-200 characters, trimmed, non-empty
- **description**: 0-1000 characters
- **user_id**: Must reference existing user

---

## 4. Database Schema (PostgreSQL)

### 4.1 SQL DDL

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_user_email ON "user"(email);

-- Tasks table
CREATE TABLE task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000) NOT NULL DEFAULT '',
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_task_user_id ON task(user_id);
CREATE INDEX idx_task_created_at ON task(created_at DESC);

-- Constraint: Max 1000 tasks per user
CREATE OR REPLACE FUNCTION check_task_limit()
RETURNS TRIGGER AS $$
BEGIN
    IF (SELECT COUNT(*) FROM task WHERE user_id = NEW.user_id) >= 1000 THEN
        RAISE EXCEPTION 'Maximum task limit (1000) reached for this user';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER enforce_task_limit
    BEFORE INSERT ON task
    FOR EACH ROW
    EXECUTE FUNCTION check_task_limit();

-- Auto-update updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_task_updated_at
    BEFORE UPDATE ON task
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## 5. TypeScript Interfaces

### 5.1 Frontend Types

```typescript
// types/index.ts

// User types
export interface User {
  id: string;           // UUID
  email: string;
  created_at: string;   // ISO 8601
}

export interface RegisterRequest {
  email: string;        // Required, valid email format
  password: string;     // Required, min 8 chars
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  success: true;
  data: {
    user: User;
    token: string;      // JWT
    expires_at: string; // ISO 8601
  };
}

// Task types
export interface Task {
  id: string;           // UUID
  user_id: string;      // UUID
  title: string;        // 1-200 chars
  description: string;  // 0-1000 chars
  completed: boolean;
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
}

export interface TaskCreateRequest {
  title: string;        // Required
  description?: string; // Optional
}

export interface TaskUpdateRequest {
  title?: string;       // Optional
  description?: string; // Optional (at least one required)
}

export interface TaskListResponse {
  success: true;
  data: Task[];
  meta: {
    total: number;
    limit: number;
    offset: number;
  };
}

export interface TaskResponse {
  success: true;
  data: Task;
}

export interface DeleteResponse {
  success: true;
  data: {
    id: string;
    deleted: true;
  };
}

// Error types
export interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}

// API Response union type
export type ApiResponse<T> =
  | { success: true; data: T; meta?: Record<string, unknown> }
  | ErrorResponse;
```

---

## 6. Schema Evolution from Phase 1

### 6.1 Comparison Table

| Aspect | Phase 1 | Phase 2 | Migration |
|--------|---------|---------|-----------|
| ID Type | `int` (sequential) | `UUID` | Breaking change |
| User Scope | Single user (implicit) | Multi-user (explicit `user_id`) | Breaking change |
| Storage | In-memory dict | PostgreSQL | Breaking change |
| `updated_at` | Not present | Auto-updated timestamp | New field |
| Persistence | Volatile (lost on restart) | Persistent | Breaking change |

### 6.2 Decision

**No migration path** - Phase 1 data was volatile and ephemeral. Phase 2 starts with a clean database.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Spec Architect | Initial data model specification |

---

**End of Data Model Specification**
