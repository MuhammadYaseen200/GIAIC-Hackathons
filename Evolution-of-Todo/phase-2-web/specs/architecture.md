# Phase II Architecture Specification: Full-Stack Web Application

**Status**: Draft
**Owner**: Lead Architect
**Dependencies**: Phase I Core CRUD (001-core-crud), REST API Specification
**Estimated Complexity**: High
**Created**: 2025-12-29
**Phase**: Phase II - Full-Stack Web Application

---

## 1. System Overview

### 1.1 Purpose & Context

- **What**: Three-tier web application architecture for task management with user authentication
- **Why**: Evolve Phase I console logic into a production-ready, multi-user web application
- **Where**: Bridges console-only (Phase I) to AI-enabled (Phase III) system

### 1.2 High-Level Architecture Diagram

```
+------------------------------------------------------------------+
|                        CLIENT LAYER                               |
|  +------------------------------------------------------------+  |
|  |                    Next.js 15+ (App Router)                 |  |
|  |  +--------+  +-----------+  +------------+  +------------+ |  |
|  |  | Pages  |  | Components |  | Server     |  | Better     | |  |
|  |  | (RSC)  |  | (Client)   |  | Actions    |  | Auth       | |  |
|  |  +--------+  +-----------+  +------------+  +------------+ |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|                     HTTPS (REST + JWT)                            |
|                              v                                    |
+------------------------------------------------------------------+
|                        API LAYER                                  |
|  +------------------------------------------------------------+  |
|  |                    FastAPI (Python 3.13+)                   |  |
|  |  +----------+  +-----------+  +-----------+  +-----------+ |  |
|  |  | Routers  |  | Middleware |  | Services  |  | Deps      | |  |
|  |  | /api/v1  |  | (Auth/CORS)|  | (Logic)   |  | (DI)      | |  |
|  |  +----------+  +-----------+  +-----------+  +-----------+ |  |
|  +------------------------------------------------------------+  |
|                              |                                    |
|                     SQLModel ORM                                  |
|                              v                                    |
+------------------------------------------------------------------+
|                        DATA LAYER                                 |
|  +------------------------------------------------------------+  |
|  |               Neon Serverless PostgreSQL                    |  |
|  |  +----------------+  +----------------+                     |  |
|  |  | users          |  | tasks          |                     |  |
|  |  | (Better Auth)  |  | (App Data)     |                     |  |
|  |  +----------------+  +----------------+                     |  |
|  +------------------------------------------------------------+  |
+------------------------------------------------------------------+
```

### 1.3 Component Interaction Flow

```
User Action -> Next.js Page -> Server Action/Client Fetch
                                       |
                                       v
                            Better Auth (JWT Generation)
                                       |
                                       v
                            FastAPI Endpoint (JWT Validation)
                                       |
                                       v
                            Service Layer (Business Logic)
                                       |
                                       v
                            Repository Layer (SQLModel)
                                       |
                                       v
                            Neon PostgreSQL
```

---

## 2. Constraints (MANDATORY - Define First)

### 2.1 NOT Supported (Phase II Scope)

| Feature | Reason | Deferred To |
|---------|--------|-------------|
| Real-time updates (WebSockets) | Complexity budget | Phase III |
| Offline mode / PWA | Requires service workers | Phase V |
| Social login (OAuth) | Better Auth supports, but out of scope | Phase V |
| Task sharing between users | Multi-tenancy complexity | Phase V |
| File attachments | Storage infrastructure needed | Never (out of scope) |
| Mobile app | Web-first approach | Phase V (responsive only) |
| GraphQL API | REST sufficient for Phase II | Never (design choice) |
| Internationalization (i18n) | English only for MVP | Phase V |

### 2.2 Performance Limits

| Metric | Limit | Enforcement Point |
|--------|-------|-------------------|
| Frontend bundle size | < 200KB (gzipped) | Vercel build |
| API response time (p99) | < 500ms | Backend monitoring |
| Database query time | < 100ms | SQLModel query optimization |
| Concurrent users | 100 | Neon connection pooling |
| Tasks per user | 1000 | Database constraint |
| Session duration | 24 hours | Better Auth config |

### 2.3 Security Boundaries

| Boundary | Enforcement |
|----------|-------------|
| Authentication required | All `/api/v1/*` endpoints |
| User data isolation | All queries scoped by `user_id` from JWT |
| HTTPS only | Vercel (frontend), Backend host (API) |
| CORS restricted | Backend allows only frontend origin |
| JWT signature | HS256 with shared secret |
| Password hashing | bcrypt (Better Auth default) |
| SQL injection | SQLModel parameterized queries |
| XSS prevention | React escaping, JSON-only API |

### 2.4 Technical Debt (Accepted)

| Item | Rationale | Remediation Phase |
|------|-----------|-------------------|
| No API rate limiting | Complexity vs. value for MVP | Phase IV |
| No caching layer | Database performance sufficient | Phase IV |
| Single database region | Latency acceptable for MVP | Phase V |
| No retry logic for DB | Neon auto-reconnect handles most cases | Phase IV |
| No request tracing | Console logging sufficient for MVP | Phase IV |

---

## 3. Frontend Architecture

### 3.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | Next.js | 15.x (App Router) |
| Language | TypeScript | 5.x |
| Styling | Tailwind CSS | 3.x |
| Auth Library | Better Auth | latest |
| HTTP Client | Native fetch | N/A |
| State Management | React hooks + URL state | N/A |
| Form Handling | React Hook Form | latest |
| Validation | Zod | latest |

### 3.2 Directory Structure

```
frontend/
├── app/                         # Next.js App Router
│   ├── (auth)/                  # Auth route group (no layout)
│   │   ├── login/
│   │   │   └── page.tsx         # Login page
│   │   └── register/
│   │       └── page.tsx         # Registration page
│   ├── (dashboard)/             # Protected route group
│   │   ├── layout.tsx           # Dashboard layout (auth check)
│   │   └── tasks/
│   │       ├── page.tsx         # Task list page
│   │       └── [id]/
│   │           └── page.tsx     # Task detail page
│   ├── api/
│   │   └── auth/
│   │       └── [...betterauth]/ # Better Auth catch-all route
│   │           └── route.ts
│   ├── layout.tsx               # Root layout
│   ├── page.tsx                 # Landing page (redirect to /tasks)
│   └── globals.css              # Global styles
├── components/
│   ├── ui/                      # Reusable UI primitives
│   │   ├── Button.tsx
│   │   ├── Input.tsx
│   │   ├── Modal.tsx
│   │   └── Card.tsx
│   ├── tasks/                   # Task-specific components
│   │   ├── TaskList.tsx
│   │   ├── TaskItem.tsx
│   │   ├── TaskForm.tsx
│   │   └── TaskActions.tsx
│   └── auth/                    # Auth components
│       ├── LoginForm.tsx
│       ├── RegisterForm.tsx
│       └── AuthGuard.tsx
├── lib/
│   ├── auth.ts                  # Better Auth client config
│   ├── api.ts                   # API client (fetch wrapper)
│   └── utils.ts                 # Utility functions
├── types/
│   └── index.ts                 # TypeScript type definitions
├── hooks/
│   ├── useTasks.ts              # Task data fetching hook
│   └── useAuth.ts               # Auth state hook
├── public/                      # Static assets
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
└── CLAUDE.md                    # Frontend-specific instructions
```

### 3.3 Route Definitions

| Route | Component | Auth Required | Purpose |
|-------|-----------|---------------|---------|
| `/` | `page.tsx` | No | Landing, redirect to `/tasks` if authenticated |
| `/login` | `(auth)/login/page.tsx` | No | User login |
| `/register` | `(auth)/register/page.tsx` | No | User registration |
| `/tasks` | `(dashboard)/tasks/page.tsx` | Yes | Task list (main view) |
| `/tasks/[id]` | `(dashboard)/tasks/[id]/page.tsx` | Yes | Task detail/edit |

### 3.4 Better Auth Integration

#### Client Configuration (`lib/auth.ts`)

```typescript
// Configuration structure (not implementation)
interface AuthConfig {
  baseURL: string;          // Backend URL for auth endpoints
  credentials: 'include';   // Send cookies with requests
  session: {
    strategy: 'jwt';
    maxAge: 86400;          // 24 hours
  };
}
```

#### Auth Flow

```
1. User submits credentials -> Better Auth client
2. Better Auth client -> POST /api/auth/login
3. Backend validates -> Returns JWT in httpOnly cookie
4. Subsequent requests include cookie automatically
5. AuthGuard component checks session before rendering protected routes
```

### 3.5 API Client Design

```typescript
// Type definitions for API client
interface APIClient {
  get<T>(path: string): Promise<T>;
  post<T>(path: string, body: object): Promise<T>;
  put<T>(path: string, body: object): Promise<T>;
  patch<T>(path: string, body?: object): Promise<T>;
  delete<T>(path: string): Promise<T>;
}

// All methods include:
// - Authorization header with JWT from cookie
// - Content-Type: application/json
// - Error handling with typed error responses
```

### 3.6 Component Hierarchy

```
RootLayout
├── (auth routes - no persistent layout)
│   ├── LoginPage
│   │   └── LoginForm
│   └── RegisterPage
│       └── RegisterForm
│
└── DashboardLayout (AuthGuard wrapper)
    └── TasksPage
        ├── TaskForm (create new)
        └── TaskList
            └── TaskItem (for each task)
                └── TaskActions (complete, edit, delete)
```

### 3.7 State Management Strategy

| State Type | Location | Rationale |
|------------|----------|-----------|
| Auth state | Better Auth client | Centralized session management |
| Task list | Server Component + revalidation | Fresh data on each render |
| Form state | React Hook Form | Local form handling |
| UI state (modals) | React useState | Component-local |
| URL state (filters) | searchParams | Shareable, bookmarkable |

---

## 4. Backend Architecture

### 4.1 Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.115.x |
| Language | Python | 3.13+ |
| ORM | SQLModel | 0.0.22+ |
| Database Driver | psycopg (async) | 3.x |
| Validation | Pydantic v2 | 2.x |
| Auth Verification | PyJWT | 2.x |
| Package Manager | UV | latest |
| ASGI Server | Uvicorn | 0.32.x |

### 4.2 Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application factory
│   ├── config.py                # Settings (from env vars)
│   ├── database.py              # SQLModel engine + session
│   ├── dependencies.py          # FastAPI dependencies (DI)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Main v1 router
│   │   │   └── tasks.py         # Task endpoints
│   │   └── deps.py              # API-level dependencies
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User SQLModel
│   │   └── task.py              # Task SQLModel
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── task.py              # Task Pydantic schemas
│   │   └── common.py            # Shared response schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   └── task_service.py      # Task business logic
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── task_repository.py   # Task data access
│   │
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py              # JWT verification middleware
│       └── cors.py              # CORS configuration
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/
│   │   └── test_task_service.py
│   └── integration/
│       └── test_task_endpoints.py
│
├── alembic/                     # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml               # UV/pip dependencies
├── CLAUDE.md                    # Backend-specific instructions
└── .env.example                 # Environment template
```

### 4.3 Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (Routers)                       │
│  - HTTP request/response handling                                │
│  - Request validation (Pydantic schemas)                         │
│  - Response serialization                                        │
│  - Dependency injection                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  - Business logic (validation rules, constraints)                │
│  - Transaction coordination                                      │
│  - Cross-entity operations                                       │
│  - Error classification                                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Repository Layer                              │
│  - Database queries (SQLModel)                                   │
│  - Data access abstraction                                       │
│  - Query optimization                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer (Models)                         │
│  - SQLModel entity definitions                                   │
│  - Database schema representation                                │
│  - Relationships                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.4 Dependency Injection Pattern

```python
# Conceptual structure (not implementation)
# Dependencies flow: Router -> Service -> Repository -> Session

Router Endpoint:
    Depends(get_current_user)      # Extracts user from JWT
    Depends(get_task_service)      # Provides TaskService instance

TaskService:
    Depends(get_task_repository)   # Provides TaskRepository instance

TaskRepository:
    Depends(get_session)           # Provides SQLModel Session
```

### 4.5 Middleware Stack

```
Request Flow:
┌──────────────────────────────────────────────────────────┐
│  1. CORS Middleware                                       │
│     - Validates Origin header                             │
│     - Adds CORS response headers                          │
├──────────────────────────────────────────────────────────┤
│  2. Request ID Middleware                                 │
│     - Generates X-Request-Id                              │
│     - Attaches to request state                           │
├──────────────────────────────────────────────────────────┤
│  3. Authentication Middleware                             │
│     - Extracts JWT from Authorization header              │
│     - Validates signature and expiration                  │
│     - Attaches user_id to request state                   │
├──────────────────────────────────────────────────────────┤
│  4. Route Handler                                         │
│     - Business logic execution                            │
└──────────────────────────────────────────────────────────┘
```

### 4.6 Error Handling Strategy

| Exception Type | HTTP Status | Error Code | Handling |
|---------------|-------------|------------|----------|
| `ValidationError` (Pydantic) | 400 | `VALIDATION_ERROR` | FastAPI default |
| `JWTError` | 401 | `AUTH_*` | Auth middleware |
| `TaskNotFoundError` | 404 | `TASK_NOT_FOUND` | Service layer |
| `PermissionError` | 404 | `TASK_NOT_FOUND` | Return 404, not 403 |
| `DatabaseError` | 503 | `DATABASE_ERROR` | Global handler |
| `Exception` | 500 | `INTERNAL_ERROR` | Global handler |

### 4.7 Phase I to Phase II Migration

| Phase I Component | Phase II Equivalent |
|-------------------|---------------------|
| `models/task.py` (dataclass) | `models/task.py` (SQLModel) |
| `repositories/memory_repo.py` | `repositories/task_repository.py` |
| `services/todo_service.py` | `services/task_service.py` |
| `main.py` (CLI REPL) | `api/v1/tasks.py` (HTTP endpoints) |

**Key Changes**:
1. Task ID: `int` (sequential) -> `uuid.UUID` (v4)
2. User scoping: Implicit (single user) -> Explicit (`user_id` column)
3. Timestamps: `datetime.now()` -> `datetime.utcnow()` (UTC standard)
4. Persistence: In-memory dict -> PostgreSQL via SQLModel

---

## 5. Database Layer

### 5.1 Database Selection Rationale

| Requirement | Solution |
|-------------|----------|
| PostgreSQL compatibility | Neon is PostgreSQL 16+ |
| Serverless scaling | Neon auto-scales to zero |
| Connection pooling | Neon provides built-in pooling |
| Low latency | Choose region closest to backend host |
| Cost efficiency | Free tier sufficient for Phase II |

### 5.2 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                           users                                  │
├─────────────────────────────────────────────────────────────────┤
│ id          : UUID (PK)           # Better Auth manages         │
│ email       : VARCHAR(255) UNIQUE # Better Auth manages         │
│ password    : VARCHAR(255)        # Better Auth manages (hash)  │
│ created_at  : TIMESTAMP           # Better Auth manages         │
│ updated_at  : TIMESTAMP           # Better Auth manages         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           tasks                                  │
├─────────────────────────────────────────────────────────────────┤
│ id          : UUID (PK)           # gen_random_uuid()           │
│ user_id     : UUID (FK -> users)  # NOT NULL                    │
│ title       : VARCHAR(200)        # NOT NULL                    │
│ description : TEXT                # DEFAULT ''                  │
│ completed   : BOOLEAN             # DEFAULT FALSE               │
│ created_at  : TIMESTAMP           # DEFAULT NOW()               │
│ updated_at  : TIMESTAMP           # DEFAULT NOW()               │
├─────────────────────────────────────────────────────────────────┤
│ INDEXES:                                                         │
│   - idx_tasks_user_id ON (user_id)                              │
│   - idx_tasks_user_completed ON (user_id, completed)            │
├─────────────────────────────────────────────────────────────────┤
│ CONSTRAINTS:                                                     │
│   - tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES users   │
│   - tasks_title_length CHECK (char_length(title) <= 200)        │
│   - tasks_description_length CHECK (char_length(description)    │
│     <= 1000)                                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 SQLModel Entity Definitions

#### User Entity (Better Auth Managed)

```python
# Conceptual structure - Better Auth creates and manages this table
class User:
    id: UUID                    # Primary key
    email: str                  # Unique, indexed
    password: str               # Hashed by Better Auth
    created_at: datetime        # Auto-set
    updated_at: datetime        # Auto-updated
```

#### Task Entity (Application Managed)

```python
# Conceptual structure for Task SQLModel
class Task:
    id: UUID                    # Primary key, default uuid4()
    user_id: UUID               # Foreign key to users.id
    title: str                  # Max 200 chars, required
    description: str            # Max 1000 chars, default ""
    completed: bool             # Default False
    created_at: datetime        # Default utcnow()
    updated_at: datetime        # Updated on modification
```

### 5.4 Connection Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Connection string | `postgresql+psycopg://...` | Async driver |
| Pool size | 5 | Neon free tier limit |
| Max overflow | 10 | Handle burst traffic |
| Pool timeout | 30s | Fail fast on exhaustion |
| SSL mode | `require` | Neon requires SSL |

### 5.5 Migration Strategy

| Tool | Purpose |
|------|---------|
| Alembic | Schema migrations |
| SQLModel | ORM and schema definition |
| Neon Console | Manual inspection/debugging |

**Migration Workflow**:
1. Modify SQLModel entity
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration file
4. Apply migration: `alembic upgrade head`

---

## 6. Authentication Flow

### 6.1 Authentication Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                          FRONTEND                                  │
│  ┌─────────────────┐    ┌─────────────────┐    ┌───────────────┐ │
│  │   Login Form    │───>│  Better Auth    │───>│   API Client  │ │
│  │                 │    │    Client       │    │  (with JWT)   │ │
│  └─────────────────┘    └─────────────────┘    └───────────────┘ │
│                                │                        │         │
│                                │ Session                │ Bearer  │
│                                │ Cookie                 │ Token   │
│                                ▼                        ▼         │
└────────────────────────────────┼────────────────────────┼─────────┘
                                 │                        │
                                 │                        │
┌────────────────────────────────┼────────────────────────┼─────────┐
│                          BACKEND                        │         │
│                                │                        │         │
│  ┌─────────────────────────────┼────────────────────────┼───────┐ │
│  │              Auth Endpoints  │        Task Endpoints │       │ │
│  │  ┌─────────────────┐        │      ┌───────────────┐ │       │ │
│  │  │ POST /auth/login│        │      │ GET /api/v1/* │ │       │ │
│  │  │ POST /auth/signup        │      └───────────────┘ │       │ │
│  │  │ POST /auth/logout        │              │         │       │ │
│  │  └─────────────────┘        │              ▼         │       │ │
│  │           │                 │      ┌───────────────┐ │       │ │
│  │           ▼                 │      │  Auth         │ │       │ │
│  │  ┌─────────────────┐        │      │  Middleware   │ │       │ │
│  │  │  Better Auth    │        │      │  (JWT Verify) │ │       │ │
│  │  │  Server         │        │      └───────────────┘ │       │ │
│  │  └─────────────────┘        │              │         │       │ │
│  │           │                 │              ▼         │       │ │
│  │           │ JWT             │      ┌───────────────┐ │       │ │
│  │           │ Generation      │      │  User Context │ │       │ │
│  │           ▼                 │      │  (user_id)    │ │       │ │
│  │  ┌─────────────────┐        │      └───────────────┘ │       │ │
│  │  │    Database     │◄───────┴────────────────────────┘       │ │
│  │  │    (users)      │                                         │ │
│  │  └─────────────────┘                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### 6.2 Registration Flow

```
1. User fills registration form (email, password)
2. Frontend validates input (Zod schema)
3. POST /api/auth/signup (Better Auth endpoint)
4. Backend validates:
   - Email format
   - Password strength (min 8 chars)
   - Email uniqueness
5. Backend creates user record (password hashed with bcrypt)
6. Backend returns JWT in httpOnly cookie
7. Frontend redirects to /tasks
```

### 6.3 Login Flow

```
1. User fills login form (email, password)
2. Frontend validates input (Zod schema)
3. POST /api/auth/login (Better Auth endpoint)
4. Backend validates credentials:
   - Email exists
   - Password matches hash
5. Backend generates JWT with claims:
   - sub: user_id (UUID)
   - email: user email
   - iat: issued at timestamp
   - exp: expiration (24h from now)
6. Backend returns JWT in httpOnly cookie
7. Frontend redirects to /tasks
```

### 6.4 Request Authentication Flow

```
1. Client makes request to /api/v1/* endpoint
2. Request includes:
   - Authorization: Bearer <jwt_token>
   - (or) Cookie containing session token
3. Auth middleware extracts token
4. Auth middleware validates:
   - Token structure (3 parts, base64 encoded)
   - Signature (HS256 with secret)
   - Expiration (exp claim vs. current time)
5. Auth middleware extracts user_id from sub claim
6. Auth middleware attaches user_id to request state
7. Endpoint handler accesses user_id via dependency injection
8. All database queries scoped by user_id
```

### 6.5 Logout Flow

```
1. User clicks logout
2. POST /api/auth/logout (Better Auth endpoint)
3. Backend invalidates session
4. Backend clears httpOnly cookie
5. Frontend redirects to /login
```

### 6.6 JWT Token Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "iat": 1735344000,
    "exp": 1735430400
  },
  "signature": "<base64_encoded_signature>"
}
```

### 6.7 Security Considerations

| Concern | Mitigation |
|---------|------------|
| Token theft | httpOnly cookie (XSS protection) |
| CSRF | SameSite=Lax cookie attribute |
| Token replay | 24h expiration |
| Brute force | Rate limiting (Phase IV) |
| Password leak | bcrypt hashing (cost factor 12) |
| Token tampering | HS256 signature verification |

---

## 7. API Communication

### 7.1 Request/Response Flow

```
Frontend                    Backend                     Database
   │                           │                            │
   │ 1. User Action            │                            │
   │ (click, submit)           │                            │
   │                           │                            │
   │ 2. API Call               │                            │
   │ ────────────────────────> │                            │
   │ Headers:                  │                            │
   │   Authorization: Bearer   │                            │
   │   Content-Type: json      │                            │
   │                           │                            │
   │                           │ 3. JWT Validation          │
   │                           │ (middleware)               │
   │                           │                            │
   │                           │ 4. Request Validation      │
   │                           │ (Pydantic schema)          │
   │                           │                            │
   │                           │ 5. Service Call            │
   │                           │ (business logic)           │
   │                           │                            │
   │                           │ 6. Repository Query        │
   │                           │ ─────────────────────────> │
   │                           │                            │
   │                           │ 7. Query Result            │
   │                           │ <───────────────────────── │
   │                           │                            │
   │                           │ 8. Response Serialization  │
   │                           │ (Pydantic schema)          │
   │                           │                            │
   │ 9. JSON Response          │                            │
   │ <──────────────────────── │                            │
   │ Headers:                  │                            │
   │   Content-Type: json      │                            │
   │   X-Request-Id: uuid      │                            │
   │                           │                            │
   │ 10. UI Update             │                            │
   │ (revalidate/setState)     │                            │
   │                           │                            │
```

### 7.2 API Base Configuration

| Setting | Development | Production |
|---------|-------------|------------|
| Backend URL | `http://localhost:8000` | `https://api.example.com` |
| Frontend URL | `http://localhost:3000` | `https://example.com` |
| API Prefix | `/api/v1` | `/api/v1` |
| Timeout | 30000ms | 10000ms |

### 7.3 CORS Configuration

```python
# Conceptual CORS settings
cors_config = {
    "allow_origins": [FRONTEND_URL],   # Exact origin, not *
    "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    "allow_headers": ["Authorization", "Content-Type", "X-Request-Id"],
    "allow_credentials": True,          # Required for cookies
    "max_age": 86400,                   # Preflight cache 24h
}
```

### 7.4 Response Envelope Format

All API responses follow a consistent envelope format:

**Success Response**:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "total": 10,
    "limit": 50,
    "offset": 0
  }
}
```

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Title cannot be empty"
    }
  }
}
```

### 7.5 Frontend API Client Pattern

```typescript
// Conceptual API client structure
interface ApiClientConfig {
  baseURL: string;
  timeout: number;
  getAuthToken: () => Promise<string | null>;
}

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
  meta?: {
    total?: number;
    limit?: number;
    offset?: number;
  };
}
```

---

## 8. Deployment Architecture

### 8.1 Deployment Topology

```
┌───────────────────────────────────────────────────────────────────┐
│                            INTERNET                                │
│                                                                    │
│    Users ──────────────────────────────────────────────────────>  │
│                              │                                     │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     VERCEL EDGE NETWORK                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Next.js Application                      │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │  Static     │  │  Server     │  │  API        │        │  │
│  │  │  Assets     │  │  Components │  │  Routes     │        │  │
│  │  │  (CDN)      │  │  (Serverless)│  │  (Proxy)    │        │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │  │
│  │                                            │               │  │
│  └────────────────────────────────────────────┼───────────────┘  │
│                                               │                   │
│                      Frontend Origin: example.vercel.app          │
└───────────────────────────────────────────────┼───────────────────┘
                                                │
                                     HTTPS (REST API)
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                    BACKEND HOST (Railway/Render/Fly.io)           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                      │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │  │
│  │  │  Uvicorn    │  │  FastAPI    │  │  SQLModel   │        │  │
│  │  │  ASGI       │  │  Router     │  │  ORM        │        │  │
│  │  │  Server     │  │             │  │             │        │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘        │  │
│  │                                            │               │  │
│  └────────────────────────────────────────────┼───────────────┘  │
│                                               │                   │
│                      Backend Origin: api.example.com              │
└───────────────────────────────────────────────┼───────────────────┘
                                                │
                                     PostgreSQL Protocol (SSL)
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                         NEON SERVERLESS                           │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    PostgreSQL 16+                           │  │
│  │                                                             │  │
│  │  ┌─────────────┐  ┌─────────────┐                          │  │
│  │  │  users      │  │  tasks      │                          │  │
│  │  │  (auth)     │  │  (app data) │                          │  │
│  │  └─────────────┘  └─────────────┘                          │  │
│  │                                                             │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                   │
│                      Database: neon.tech                          │
└───────────────────────────────────────────────────────────────────┘
```

### 8.2 Vercel Configuration (Frontend)

| Setting | Value | Purpose |
|---------|-------|---------|
| Framework Preset | Next.js | Auto-detect build settings |
| Build Command | `next build` | Compile application |
| Output Directory | `.next` | Build artifacts |
| Node.js Version | 20.x | Runtime compatibility |
| Environment Variables | See below | Configuration injection |

**Environment Variables (Frontend)**:

| Variable | Example | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `https://api.example.com` | Backend URL |
| `BETTER_AUTH_SECRET` | `<random-32-chars>` | JWT signing secret |
| `BETTER_AUTH_URL` | `https://example.com` | Callback URL base |

### 8.3 Backend Host Configuration

**Recommended Platforms** (in order of preference):
1. **Railway** - Simple deployment, good free tier
2. **Render** - Easy setup, auto-deploy from Git
3. **Fly.io** - Global edge deployment

| Setting | Value | Purpose |
|---------|-------|---------|
| Runtime | Python 3.13 | Language version |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | ASGI server |
| Health Check | `GET /health` | Uptime monitoring |
| Auto-deploy | On push to `main` | CI/CD integration |

**Environment Variables (Backend)**:

| Variable | Example | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `postgresql+psycopg://...` | Neon connection string |
| `JWT_SECRET` | `<same-as-BETTER_AUTH_SECRET>` | JWT verification |
| `FRONTEND_URL` | `https://example.com` | CORS origin |
| `ENVIRONMENT` | `production` | Feature flags |

### 8.4 Neon Configuration

| Setting | Value | Purpose |
|---------|-------|---------|
| Region | `us-east-1` | Closest to backend host |
| Compute Size | 0.25 CU | Free tier |
| Auto-suspend | 5 minutes | Cost optimization |
| Connection Pooling | Enabled | Handle concurrent requests |
| SSL Mode | Require | Security |

### 8.5 Environment Isolation

| Environment | Frontend URL | Backend URL | Database Branch |
|-------------|--------------|-------------|-----------------|
| Development | `localhost:3000` | `localhost:8000` | `dev` |
| Preview | `*.vercel.app` | `*.railway.app` | `preview` |
| Production | `example.com` | `api.example.com` | `main` |

### 8.6 Deployment Pipeline

```
Developer Push to GitHub
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions (CI)                                          │
│  - Lint (ruff, eslint)                                        │
│  - Type check (mypy, tsc)                                     │
│  - Unit tests (pytest, jest)                                  │
└──────────────────────────────────────────────────────────────┘
           │
           │ (on success)
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Parallel Deployments                                         │
│                                                               │
│  ┌────────────────────┐     ┌────────────────────┐           │
│  │  Vercel            │     │  Railway/Render    │           │
│  │  (Frontend)        │     │  (Backend)         │           │
│  │                    │     │                    │           │
│  │  next build        │     │  docker build      │           │
│  │  deploy to edge    │     │  deploy to host    │           │
│  └────────────────────┘     └────────────────────┘           │
│                                                               │
└──────────────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────────────────────┐
│  Post-Deployment Verification                                 │
│  - Health check endpoints                                     │
│  - Smoke tests (optional)                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 9. Non-Functional Requirements

### 9.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to First Byte (TTFB) | < 200ms | Vercel Analytics |
| Largest Contentful Paint (LCP) | < 2.5s | Lighthouse |
| First Input Delay (FID) | < 100ms | Lighthouse |
| Cumulative Layout Shift (CLS) | < 0.1 | Lighthouse |
| API Response Time (p99) | < 500ms | Backend logs |
| Database Query Time | < 100ms | SQLModel logging |

### 9.2 Scalability

| Dimension | Phase II Capacity | Scaling Strategy |
|-----------|-------------------|------------------|
| Concurrent Users | 100 | Neon auto-scaling |
| Requests/Second | 50 | Backend horizontal scaling |
| Database Connections | 5 | Connection pooling |
| Data Volume | 100K tasks | Index optimization |

### 9.3 Availability

| Metric | Target | Strategy |
|--------|--------|----------|
| Uptime | 99% | Managed hosting (Vercel, Railway) |
| Recovery Time | < 5 min | Auto-restart on failure |
| Backup Frequency | Daily | Neon automatic backups |
| Disaster Recovery | N/A | Phase V scope |

### 9.4 Security

| Control | Implementation |
|---------|----------------|
| Transport Encryption | TLS 1.3 (HTTPS) |
| Data at Rest | Neon encryption |
| Authentication | JWT with 24h expiry |
| Authorization | User-scoped queries |
| Input Validation | Pydantic/Zod schemas |
| Secrets Management | Environment variables |
| Dependency Scanning | Dependabot (GitHub) |

### 9.5 Observability

| Aspect | Phase II Implementation | Phase IV+ Enhancement |
|--------|------------------------|----------------------|
| Logging | Console (structured JSON) | Centralized logging |
| Metrics | Basic (request count, latency) | Prometheus/Grafana |
| Tracing | X-Request-Id header | OpenTelemetry |
| Alerting | None | PagerDuty/Slack |
| Dashboards | None | Grafana |

---

## 10. Integration Points

### 10.1 Upstream Dependencies

| Dependency | Type | Purpose | Failure Impact |
|------------|------|---------|----------------|
| Neon PostgreSQL | Database | Data persistence | Total outage |
| Better Auth | Library | User authentication | Auth failures |
| Vercel | Platform | Frontend hosting | Frontend unavailable |
| Backend Host | Platform | API hosting | API unavailable |

### 10.2 Downstream Consumers

| Consumer | Protocol | Purpose |
|----------|----------|---------|
| Next.js Frontend | HTTPS/REST | UI data fetching |
| (Phase III) MCP Client | HTTPS/REST | AI tool execution |
| (Phase III) OpenAI Agent | MCP Protocol | Task management commands |

### 10.3 External Service Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase II Integrations                         │
│                                                                  │
│  ┌───────────────┐                    ┌───────────────────────┐ │
│  │   Frontend    │ ── REST/JSON ────> │      Backend         │ │
│  │  (Next.js)    │                    │     (FastAPI)        │ │
│  └───────────────┘                    └───────────────────────┘ │
│         │                                       │                │
│         │ Better Auth                           │ SQLModel       │
│         │ Session API                           │ Queries        │
│         ▼                                       ▼                │
│  ┌───────────────┐                    ┌───────────────────────┐ │
│  │  Better Auth  │                    │   Neon PostgreSQL    │ │
│  │   (Library)   │ ───────────────────│      (Service)       │ │
│  └───────────────┘   Shared JWT       └───────────────────────┘ │
│                      Secret                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Phase Transition Considerations

### 11.1 Phase II to Phase III Preparation

| Aspect | Phase II State | Phase III Requirement |
|--------|---------------|----------------------|
| API Layer | REST endpoints | MCP Tool wrapper needed |
| Authentication | JWT-based | Pass through to MCP |
| State Management | Stateless API | Conversation state needed |
| Error Handling | HTTP status codes | MCP error format |

### 11.2 Migration Checklist (Phase I to II)

- [ ] Task model migrated to SQLModel
- [ ] Integer IDs converted to UUIDs
- [ ] User scoping added to all queries
- [ ] In-memory repo replaced with PostgreSQL
- [ ] Business logic preserved in service layer
- [ ] All 5 core features functional via REST API
- [ ] Authentication integrated end-to-end
- [ ] Frontend CRUD operations working

### 11.3 Brownfield Safety Measures

| Measure | Implementation |
|---------|----------------|
| Phase I isolation | `phase-1-console/` directory preserved |
| Backup before migration | `CLAUDE.md.phase1_backup` |
| Spec versioning | Date and phase in spec headers |
| Rollback capability | Git branches per phase |

---

## 12. Acceptance Criteria

### 12.1 Architecture Validation

- [ ] AC-ARCH-01: Frontend loads in < 3s on 3G network
- [ ] AC-ARCH-02: API responds in < 500ms for all endpoints
- [ ] AC-ARCH-03: Database queries execute in < 100ms
- [ ] AC-ARCH-04: Authentication flow completes successfully
- [ ] AC-ARCH-05: CORS configured correctly (no preflight failures)
- [ ] AC-ARCH-06: User data isolation verified (cannot access other users' tasks)

### 12.2 Component Integration

- [ ] AC-INT-01: Frontend can call all 6 REST endpoints
- [ ] AC-INT-02: JWT token flows from login to API calls
- [ ] AC-INT-03: Database persists data across server restarts
- [ ] AC-INT-04: Better Auth handles registration and login
- [ ] AC-INT-05: Error responses render correctly in UI

### 12.3 Deployment Verification

- [ ] AC-DEPLOY-01: Frontend deploys to Vercel successfully
- [ ] AC-DEPLOY-02: Backend deploys to chosen host successfully
- [ ] AC-DEPLOY-03: Database migrations apply cleanly
- [ ] AC-DEPLOY-04: Environment variables configured correctly
- [ ] AC-DEPLOY-05: Health check endpoints respond 200 OK

---

## 13. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Spec Architect | Initial architecture specification |

---

## Approval

**Specification Status**: Draft - Ready for Review

- [ ] System architecture diagram complete
- [ ] Frontend architecture defined
- [ ] Backend architecture defined
- [ ] Database schema documented
- [ ] Authentication flow specified
- [ ] API communication patterns established
- [ ] Deployment architecture planned
- [ ] Non-functional requirements stated
- [ ] Acceptance criteria testable

**Next Steps**:
1. Database schema specification (`specs/database/schema.md`)
2. Frontend UI specification (`specs/ui/`)
3. Implementation plan generation

---

**End of Architecture Specification**
