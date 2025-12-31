# Phase 2: Full-Stack Web Application

A multi-user task management application built with Next.js, FastAPI, and PostgreSQL, featuring JWT authentication and persistent storage.

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (for PostgreSQL)
- **Node.js 18+** (for frontend)
- **Python 3.11+** (for backend)
- **UV** (Python package manager)

---

### 1. Database Setup (PostgreSQL)

Start the PostgreSQL container:

```bash
# From project root
docker-compose -f phase-2-web/docker-compose.yml up -d

# Verify container is healthy
docker ps | grep todo_postgres_dev
```

**Environment Variables**:
Copy `phase-2-web/.env.example` to `phase-2-web/.env` and configure:
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Random secret for JWT signing

---

### 2. Backend Setup (FastAPI)

```bash
cd phase-2-web/backend

# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload --port 8000
```

**Verify**: Visit http://localhost:8000/docs for interactive API documentation

---

### 3. Frontend Setup (Next.js)

```bash
cd phase-2-web/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Verify**: Visit http://localhost:3000

---

## Features

### User Stories Implemented

| Story | Description | Status |
|-------|-------------|--------|
| **US-1** | User Registration | Complete |
| **US-2** | User Login & Logout | Complete |
| **US-3** | Add Task | Complete |
| **US-4** | View Task List | Complete |
| **US-5** | Edit Task | Complete |
| **US-6** | Delete Task | Complete |
| **US-7** | Mark Task Complete | Complete |

### Core Capabilities

- **Authentication**: Email/password registration and login with JWT tokens stored in httpOnly cookies
- **Task CRUD**: Create, read, update, and delete tasks with title and description fields
- **Task Status**: Toggle tasks between pending and completed states
- **User Isolation**: Each user can only access their own tasks (enforced at database and API level)
- **Validation**: Client-side and server-side validation for all forms
- **Toast Notifications**: Success and error messages for all operations
- **Loading States**: Skeleton loaders during data fetching
- **Error Boundaries**: Graceful error handling with recovery options
- **Delete Confirmation**: Accessible modal dialog before deletion

---

## Architecture

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 15+ (App Router) | React framework with server components |
| Backend | FastAPI 0.115+ | Python async web framework |
| Database | PostgreSQL 16 | Relational database (Neon Serverless in production) |
| ORM | SQLModel | Type-safe database models with Pydantic |
| Migrations | Alembic | Version-controlled schema changes |
| Auth | JWT (python-jose) | Token-based authentication |
| Password Hashing | bcrypt (passlib) | Secure password storage |
| Package Manager | UV (backend), npm (frontend) | Dependency management |
| UI Components | Custom Tailwind CSS | Styled components with design system |
| Notifications | Sonner | Toast notification system |

### Project Structure

```
phase-2-web/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/v1/             # API endpoints
│   │   │   ├── auth.py         # Registration, login, logout
│   │   │   └── tasks.py        # Task CRUD operations
│   │   ├── core/               # Core configuration
│   │   │   ├── config.py       # Environment settings
│   │   │   ├── security.py     # JWT & bcrypt utilities
│   │   │   └── database.py     # SQLModel engine & session
│   │   ├── models/             # Database models
│   │   │   ├── user.py         # User model
│   │   │   └── task.py         # Task model
│   │   ├── services/           # Business logic
│   │   │   ├── auth_service.py # Register & login logic
│   │   │   └── task_service.py # Task CRUD operations
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Database migrations
│   ├── tests/                  # Unit & integration tests
│   └── pyproject.toml          # Python dependencies
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── (auth)/             # Auth route group
│   │   │   ├── login/          # Login page
│   │   │   └── register/       # Registration page
│   │   ├── dashboard/          # Dashboard (protected)
│   │   ├── actions/            # Server Actions
│   │   │   ├── auth.ts         # Auth actions
│   │   │   └── tasks.ts        # Task actions
│   │   ├── layout.tsx          # Root layout with ToastProvider
│   │   └── page.tsx            # Landing page with redirect
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   │   ├── Button.tsx      # Primary button with loading state
│   │   │   ├── Input.tsx       # Form input with validation
│   │   │   ├── Toast.tsx       # Toast notification provider
│   │   │   └── Skeleton.tsx    # Loading skeleton
│   │   ├── auth/               # Auth-specific components
│   │   │   ├── LoginForm.tsx
│   │   │   └── RegisterForm.tsx
│   │   └── tasks/              # Task-specific components
│   │       ├── TaskForm.tsx    # Add/edit task form
│   │       ├── TaskItem.tsx    # Single task display
│   │       └── TaskList.tsx    # Task list container
│   ├── lib/                    # Utilities
│   │   ├── api.ts              # API client
│   │   └── utils.ts            # Helper functions
│   ├── types/                  # TypeScript types
│   │   └── index.ts            # Shared type definitions
│   └── package.json            # Node dependencies
├── docker-compose.yml          # PostgreSQL container
└── .env.example                # Environment template
```

---

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

### Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Create new account | No |
| POST | `/auth/login` | Login and receive JWT | No |
| POST | `/auth/logout` | Invalidate session | No |
| GET | `/auth/me` | Get current user info | Yes |

### Tasks

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/tasks` | List user's tasks | Yes |
| POST | `/tasks` | Create new task | Yes |
| GET | `/tasks/{id}` | Get task details | Yes |
| PUT | `/tasks/{id}` | Update task | Yes |
| DELETE | `/tasks/{id}` | Delete task | Yes |
| PATCH | `/tasks/{id}/complete` | Toggle completion | Yes |

**Response Format**:

```json
// Success
{"success": true, "data": {...}}

// Error
{"success": false, "error": {"code": "ERROR_CODE", "message": "..."}}
```

---

## Security

### Authentication Flow

1. User submits email/password via registration or login form
2. Backend validates credentials and generates JWT token
3. Token stored in httpOnly cookie (prevents XSS attacks)
4. Next.js middleware extracts cookie and adds Bearer header to API requests
5. FastAPI validates JWT on protected endpoints
6. User ID extracted from JWT claims for data isolation

### Data Isolation

- All task queries include `WHERE user_id = :current_user_id` clause
- User ID extracted from JWT token in `get_current_user` dependency
- No cross-user data access possible at database or API level

### Password Security

- Passwords hashed with bcrypt (cost factor 12)
- Plaintext passwords never stored or logged
- Login failures return generic error message (prevents email enumeration)

---

## Development Workflow

### Running Migrations

```bash
cd phase-2-web/backend

# Generate new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback last migration
uv run alembic downgrade -1
```

### Type Checking & Linting

```bash
# Backend
cd phase-2-web/backend
uv run ruff check .
uv run ruff check . --fix  # Auto-fix issues

# Frontend
cd phase-2-web/frontend
npm run lint
```

### Testing

```bash
# Backend
cd phase-2-web/backend
uv run pytest -v

# Frontend
cd phase-2-web/frontend
npm run test
```

---

## Architectural Decision Records

Key decisions documented in `history/adr/`:

| ADR | Title | Summary |
|-----|-------|---------|
| ADR-004 | httpOnly Cookie JWT Strategy | JWT tokens stored in httpOnly cookies, extracted by Next.js middleware |
| ADR-005 | Next.js Server Actions Data Layer | Server Actions used for form submissions with revalidatePath |
| ADR-006 | SQLModel + Alembic Migrations | Type-safe ORM with version-controlled schema changes |
| ADR-007 | Brownfield Isolation Strategy | Phase 1 code ported to `backend/app/services/` |
| ADR-008 | SQLite Development Fallback | Local dev can use SQLite via `DATABASE_URL` env var |

---

## Known Limitations (Phase 2)

### Not Implemented

- Task priorities (high/medium/low)
- Tags or categories
- Due dates or reminders
- Search and filter functionality
- Task sorting options
- Social login (Google, GitHub)
- Password reset via email
- Email verification
- Two-factor authentication (2FA)
- Real-time updates (WebSocket)

### Planned for Later Phases

- **Phase 3**: AI chatbot integration, MCP server, real-time updates
- **Phase 4**: Kubernetes deployment, Helm charts, caching layer
- **Phase 5**: Cloud deployment, Kafka event streaming, Dapr runtime

---

## Troubleshooting

### Database Connection Issues

**Symptom**: Backend fails to start with "could not connect to server"

**Solution**:
1. Verify PostgreSQL container is running: `docker ps`
2. Check `DATABASE_URL` format in `.env`: `postgresql+asyncpg://user:pass@localhost:5432/todo_db`
3. Test connection: `docker exec -it todo_postgres_dev psql -U todo_user -d todo_db`

### Frontend Build Errors

**Symptom**: `npm run dev` fails with module not found

**Solution**:
1. Delete `node_modules/` and `.next/`
2. Run `npm install` again
3. Verify Node.js version: `node --version` (should be 18+)

### JWT Authentication Failures

**Symptom**: Protected routes return 401 Unauthorized

**Solution**:
1. Check `JWT_SECRET_KEY` matches between frontend and backend `.env` files
2. Clear browser cookies and login again
3. Verify token expiration (default: 24 hours)

---

## Contributing

This project follows **Spec-Driven Development (SDD)**:

1. All changes must reference an approved specification
2. Tasks defined in `phase-2-web/specs/tasks.md`
3. Every implementation session documented in PHR (Prompt History Record)
4. Architecture decisions captured in ADRs

See `CLAUDE.md` in project root for complete development guidelines.

---

## License

This project is part of the GIAIC Hackathon: Evolution of Todo. See main repository for licensing details.

---

**Last Updated**: 2025-12-31 | **Phase Status**: Complete | **Branch**: phase-2-web-init
