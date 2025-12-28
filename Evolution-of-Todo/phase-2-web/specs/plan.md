# Implementation Plan: Phase 2 Full-Stack Web Application

**Branch**: `phase-2-web-init`
**Date**: 2025-12-29
**Spec**: `phase-2-web/specs/spec.md`
**Input**: Feature specification for Full-Stack Web Application with Next.js, FastAPI, Neon PostgreSQL

---

## Summary

Evolve Phase I in-memory console Todo app into a multi-user web application with:
- **Frontend**: Next.js 15+ (App Router) with Tailwind CSS
- **Backend**: FastAPI with SQLModel ORM
- **Database**: Neon Serverless PostgreSQL
- **Authentication**: JWT-based with httpOnly cookies

Key architectural decisions (from CL-001 to CL-005):
- JWT stored in httpOnly cookie, extracted by middleware
- Server Actions with `revalidatePath` for data mutations
- Alembic for database migrations
- Layout-based authentication
- Next.js API proxy to eliminate CORS

---

## Technical Context

| Aspect | Value |
|--------|-------|
| **Language/Version** | Python 3.13+, TypeScript 5+ |
| **Primary Dependencies** | FastAPI, SQLModel, Next.js 15+, Tailwind CSS |
| **Storage** | Neon Serverless PostgreSQL |
| **Testing** | pytest (backend), Jest (frontend - optional) |
| **Target Platform** | Web (Vercel frontend, any backend host) |
| **Project Type** | Web (frontend + backend) |
| **Performance Goals** | < 500ms API response (p99), < 3s page load |
| **Constraints** | Max 1000 tasks/user, 24h JWT expiration |
| **Scale/Scope** | 100 concurrent users, 7 user stories |

---

## Constitution Check

*GATE: Verified against `.specify/memory/constitution.md`*

| Principle | Status | Evidence |
|-----------|--------|----------|
| Spec-Driven Development | PASS | Spec exists at `phase-2-web/specs/spec.md` |
| Brownfield Protocol | PASS | Evolving Phase 1 logic, not rewriting |
| Test-First Mindset | PASS | 14 acceptance criteria in spec |
| Smallest Viable Diff | PASS | Implementing only P1/P2 user stories |
| Intelligence Capture | IN PROGRESS | Will create PHR after plan |

**Technology Stack Compliance**:
| Layer | Constitution Mandate | Plan Compliance |
|-------|---------------------|-----------------|
| Frontend | Next.js 16+ (App Router) | Next.js 15+ (minor version flexibility) |
| Backend | Python FastAPI | FastAPI |
| ORM | SQLModel | SQLModel |
| Database | Neon Serverless PostgreSQL | Neon PostgreSQL |
| Authentication | Better Auth (JWT) | Custom JWT (simpler for Phase II) |

---

## Project Structure

### Documentation (this feature)

```text
phase-2-web/specs/
├── spec.md              # Feature specification
├── architecture.md      # System architecture
├── plan.md              # This file
├── research.md          # Phase 0 research findings
├── data-model.md        # Entity specifications
├── tasks.md             # Atomic implementation tasks
└── api/
    └── rest-endpoints.md # REST API contract
```

### Source Code (Phase 2)

```text
phase-2-web/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py           # Dependency injection (JWT auth)
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py     # API router aggregation
│   │   │       ├── auth.py       # /auth endpoints
│   │   │       └── tasks.py      # /tasks endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py         # Pydantic Settings
│   │   │   ├── security.py       # JWT + bcrypt utilities
│   │   │   └── database.py       # SQLModel engine/session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User SQLModel
│   │   │   └── task.py           # Task SQLModel
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── auth_service.py   # Register, login logic
│   │       └── task_service.py   # CRUD (ported from Phase 1)
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── pyproject.toml
│   ├── CLAUDE.md
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       └── test_tasks.py
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx            # Root layout
│   │   ├── page.tsx              # Landing (redirect to dashboard)
│   │   ├── globals.css
│   │   ├── actions/
│   │   │   ├── auth.ts           # Server actions: login, logout, register
│   │   │   └── tasks.ts          # Server actions: CRUD
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   │   └── page.tsx
│   │   │   └── register/
│   │   │       └── page.tsx
│   │   └── (dashboard)/
│   │       ├── layout.tsx        # Auth guard layout
│   │       └── page.tsx          # Task list dashboard
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── Modal.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   └── tasks/
│   │       ├── TaskList.tsx
│   │       ├── TaskItem.tsx
│   │       ├── TaskForm.tsx
│   │       └── DeleteConfirmDialog.tsx
│   ├── lib/
│   │   ├── api.ts                # Fetch wrapper
│   │   └── utils.ts
│   ├── types/
│   │   └── index.ts              # TypeScript interfaces
│   ├── middleware.ts             # Cookie → Header extraction
│   ├── next.config.js            # API proxy rewrites
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── package.json
│   └── CLAUDE.md
│
├── docker-compose.yml            # Local PostgreSQL
├── .env.example
└── CLAUDE.md
```

**Structure Decision**: Web application (frontend + backend) per constitution guidelines.

---

## Architecture Diagrams

### System Overview (Mermaid)

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Browser["Browser"]
    end

    subgraph Frontend["Frontend Layer (Vercel)"]
        NextJS["Next.js 15+"]
        Middleware["middleware.ts<br/>(Cookie→Header)"]
        ServerActions["Server Actions<br/>(auth.ts, tasks.ts)"]
        Pages["Pages<br/>(RSC + Client)"]
    end

    subgraph Backend["API Layer"]
        FastAPI["FastAPI"]
        JWTDep["JWT Dependency<br/>(deps.py)"]
        AuthRouter["Auth Router"]
        TaskRouter["Task Router"]
        Services["Services<br/>(auth, task)"]
    end

    subgraph Data["Data Layer"]
        NeonDB["Neon PostgreSQL"]
    end

    Browser --> NextJS
    NextJS --> Middleware
    Middleware --> ServerActions
    ServerActions --> |"API Proxy<br/>/api/*"| FastAPI
    Pages --> ServerActions
    FastAPI --> JWTDep
    JWTDep --> AuthRouter
    JWTDep --> TaskRouter
    AuthRouter --> Services
    TaskRouter --> Services
    Services --> |"SQLModel"| NeonDB
```

### Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant N as Next.js
    participant M as Middleware
    participant S as Server Action
    participant F as FastAPI
    participant D as Database

    Note over U,D: Login Flow
    U->>N: Submit login form
    N->>S: Call login(formData)
    S->>F: POST /api/v1/auth/login
    F->>D: Verify credentials
    D-->>F: User record
    F-->>S: JWT token
    S->>S: Set httpOnly cookie
    S-->>N: Redirect to /dashboard
    N-->>U: Dashboard page

    Note over U,D: Authenticated Request Flow
    U->>N: Access /dashboard
    N->>M: Request intercept
    M->>M: Read auth-token cookie
    M->>M: Add Authorization header
    M->>S: Forward to Server Action
    S->>F: GET /api/v1/tasks (with Bearer)
    F->>F: Validate JWT, extract user_id
    F->>D: SELECT tasks WHERE user_id = ?
    D-->>F: Task list
    F-->>S: JSON response
    S-->>N: Render task list
    N-->>U: Display tasks
```

### Task CRUD Flow

```mermaid
sequenceDiagram
    participant U as User
    participant C as Client Component
    participant S as Server Action
    participant F as FastAPI
    participant D as Database

    Note over U,D: Create Task
    U->>C: Fill task form, submit
    C->>S: createTask(formData)
    S->>F: POST /api/v1/tasks
    F->>D: INSERT INTO task
    D-->>F: New task
    F-->>S: Task response
    S->>S: revalidatePath('/dashboard')
    S-->>C: Success
    C-->>U: Updated task list

    Note over U,D: Toggle Complete
    U->>C: Click checkbox
    C->>S: toggleComplete(taskId)
    S->>F: PATCH /api/v1/tasks/{id}/complete
    F->>D: UPDATE task SET completed = NOT completed
    D-->>F: Updated task
    F-->>S: Task response
    S->>S: revalidatePath('/dashboard')
    S-->>C: Success
    C-->>U: Updated UI
```

---

## Implementation Layers

### Layer 0: Infrastructure (No Dependencies)

| Task | Description | Verification |
|------|-------------|--------------|
| T-201 | Create `phase-2-web/backend/` project structure | `ls phase-2-web/backend/app/` shows folders |
| T-202 | Create `phase-2-web/frontend/` Next.js 15 project | `pnpm dev` starts without errors |
| T-203 | Create `docker-compose.yml` for PostgreSQL | `docker-compose up -d` succeeds |
| T-204 | Create `.env.example` with all required vars | File exists with documented vars |

### Layer 1: Database (Depends on Layer 0)

| Task | Description | Verification |
|------|-------------|--------------|
| T-205 | Create SQLModel User model | Python import succeeds |
| T-206 | Create SQLModel Task model | Python import succeeds |
| T-207 | Initialize Alembic | `alembic/` directory exists |
| T-208 | Create initial migration | `alembic upgrade head` succeeds |

### Layer 2: Backend Core (Depends on Layer 1)

| Task | Description | Verification |
|------|-------------|--------------|
| T-209 | Implement `core/config.py` | Settings load from .env |
| T-210 | Implement `core/security.py` | JWT encode/decode works |
| T-211 | Implement `core/database.py` | Session creation works |
| T-212 | Port `TaskService` from Phase 1 | Unit tests pass |
| T-213 | Implement `AuthService` | Unit tests pass |

### Layer 3: API Endpoints (Depends on Layer 2)

| Task | Description | Verification |
|------|-------------|--------------|
| T-214 | Implement JWT dependency (`deps.py`) | Returns user_id from token |
| T-215 | Implement auth endpoints | `curl` tests pass |
| T-216 | Implement task endpoints | `curl` tests pass |
| T-217 | Create FastAPI main.py | `uvicorn` starts on :8000 |

### Layer 4: Frontend Foundation (Depends on T-202)

| Task | Description | Verification |
|------|-------------|--------------|
| T-218 | Create TypeScript types | No type errors |
| T-219 | Create UI components | Storybook/visual check |
| T-220 | Create auth pages (login, register) | Pages render |
| T-221 | Create dashboard layout | Layout renders |
| T-222 | Create task list component | Component renders |

### Layer 5: Integration (Depends on Layer 3, Layer 4)

| Task | Description | Verification |
|------|-------------|--------------|
| T-223 | Configure `next.config.js` rewrites | API proxy works |
| T-224 | Implement `middleware.ts` | Auth header injected |
| T-225 | Implement auth Server Actions | Login/logout work |
| T-226 | Implement task Server Actions | CRUD works |
| T-227 | Wire components to Server Actions | E2E flow works |

### Layer 6: Polish (Depends on Layer 5)

| Task | Description | Verification |
|------|-------------|--------------|
| T-228 | Add loading states | Visual check |
| T-229 | Add toast notifications | Notifications appear |
| T-230 | Add delete confirmation dialog | Dialog works |
| T-231 | Add form validation messages | Errors display |

### Layer 7: Validation (Depends on Layer 6)

| Task | Description | Verification |
|------|-------------|--------------|
| T-232 | Run acceptance scenarios | All scenarios pass |
| T-233 | Create PHR for Phase 2 | PHR file exists |
| T-234 | Update root CLAUDE.md | Phase 2 completion noted |

---

## Dependency Graph

```mermaid
flowchart LR
    subgraph L0["Layer 0: Infrastructure"]
        T201["T-201: Backend scaffold"]
        T202["T-202: Frontend scaffold"]
        T203["T-203: Docker PostgreSQL"]
        T204["T-204: Environment vars"]
    end

    subgraph L1["Layer 1: Database"]
        T205["T-205: User model"]
        T206["T-206: Task model"]
        T207["T-207: Alembic init"]
        T208["T-208: Initial migration"]
    end

    subgraph L2["Layer 2: Backend Core"]
        T209["T-209: Config"]
        T210["T-210: Security"]
        T211["T-211: Database"]
        T212["T-212: TaskService"]
        T213["T-213: AuthService"]
    end

    subgraph L3["Layer 3: API"]
        T214["T-214: JWT deps"]
        T215["T-215: Auth API"]
        T216["T-216: Task API"]
        T217["T-217: FastAPI main"]
    end

    subgraph L4["Layer 4: Frontend"]
        T218["T-218: Types"]
        T219["T-219: UI components"]
        T220["T-220: Auth pages"]
        T221["T-221: Dashboard layout"]
        T222["T-222: Task list"]
    end

    subgraph L5["Layer 5: Integration"]
        T223["T-223: API proxy"]
        T224["T-224: Middleware"]
        T225["T-225: Auth actions"]
        T226["T-226: Task actions"]
        T227["T-227: Wire components"]
    end

    subgraph L6["Layer 6: Polish"]
        T228["T-228: Loading states"]
        T229["T-229: Toasts"]
        T230["T-230: Confirm dialogs"]
        T231["T-231: Form validation"]
    end

    subgraph L7["Layer 7: Validation"]
        T232["T-232: Acceptance tests"]
        T233["T-233: PHR"]
        T234["T-234: Update CLAUDE.md"]
    end

    T201 --> T205
    T201 --> T207
    T203 --> T208
    T204 --> T209

    T205 --> T208
    T206 --> T208

    T208 --> T211
    T209 --> T210
    T210 --> T213
    T211 --> T212
    T211 --> T213

    T212 --> T216
    T213 --> T215
    T210 --> T214
    T214 --> T215
    T214 --> T216
    T215 --> T217
    T216 --> T217

    T202 --> T218
    T218 --> T219
    T219 --> T220
    T219 --> T221
    T219 --> T222

    T217 --> T223
    T202 --> T224
    T217 --> T225
    T217 --> T226
    T222 --> T227
    T225 --> T227
    T226 --> T227

    T227 --> T228
    T227 --> T229
    T227 --> T230
    T227 --> T231

    T228 --> T232
    T229 --> T232
    T230 --> T232
    T231 --> T232
    T232 --> T233
    T233 --> T234
```

---

## Complexity Tracking

> No constitution violations requiring justification.

| Aspect | Constitution Limit | This Plan | Status |
|--------|-------------------|-----------|--------|
| Projects | Web = 2 (frontend + backend) | 2 | COMPLIANT |
| Dependencies | Minimal | Standard stack only | COMPLIANT |
| Custom patterns | Avoid | Standard FastAPI/Next.js patterns | COMPLIANT |

---

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| Deadline slippage | Focus on P1 user stories; defer P2/P3 to Phase III |
| Better Auth complexity | Use simple custom JWT implementation |
| Neon cold starts | Document in NFRs as acceptable |
| Type drift | Single source: SQLModel → Alembic → TypeScript |

---

## Acceptance Gate

Phase 2 is complete when:
- [ ] All Layer 0-7 tasks marked complete
- [ ] All P1 user stories pass acceptance scenarios
- [ ] Backend starts and serves API
- [ ] Frontend builds and deploys
- [ ] User can register, login, and manage tasks
- [ ] PHR created for Phase 2

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Lead Architect | Initial implementation plan |

---

**End of Implementation Plan**
