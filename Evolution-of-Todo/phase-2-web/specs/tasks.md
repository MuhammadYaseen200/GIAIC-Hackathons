# Task List: Phase 2 Full-Stack Web Application

**Branch**: `phase-2-web-init`
**Date**: 2025-12-29
**Plan**: `phase-2-web/specs/plan.md`
**Status**: Ready for Implementation

---

## Task Numbering Convention

- **T-2XX**: Phase 2 tasks (200 series)
- Format: `T-{phase}{sequence}` (e.g., T-201 = Phase 2, Task 1)

---

## Layer 0: Infrastructure Setup

### T-201: Create Backend Project Structure

**Priority**: P1 (Critical Path)
**Dependencies**: None
**Estimated Effort**: Small

**Description**: Initialize the FastAPI backend project with proper folder structure.

**Acceptance Criteria**:
1. `phase-2-web/backend/` directory exists
2. `pyproject.toml` with dependencies: fastapi, sqlmodel, uvicorn, python-jose, passlib, bcrypt, python-multipart, alembic, asyncpg
3. Folder structure: `app/{api/v1, core, models, services}`
4. `__init__.py` in all packages
5. `CLAUDE.md` with backend-specific instructions

**Verification**:
```bash
cd phase-2-web/backend
uv sync
python -c "import app; print('OK')"
```

---

### T-202: Create Frontend Project Structure

**Priority**: P1 (Critical Path)
**Dependencies**: None
**Estimated Effort**: Small

**Description**: Initialize the Next.js 15+ frontend project with App Router.

**Acceptance Criteria**:
1. `phase-2-web/frontend/` directory exists
2. Next.js 15+ with App Router enabled
3. TypeScript configured
4. Tailwind CSS configured
5. Folder structure: `app/{(auth), (dashboard), actions}`, `components/{ui, auth, tasks}`, `lib/`, `types/`
6. `CLAUDE.md` with frontend-specific instructions

**Verification**:
```bash
cd phase-2-web/frontend
pnpm install
pnpm dev  # Should start on port 3000
```

---

### T-203: Create Docker Compose for PostgreSQL

**Priority**: P1 (Critical Path)
**Dependencies**: None
**Estimated Effort**: Small

**Description**: Create docker-compose.yml for local PostgreSQL development.

**Acceptance Criteria**:
1. `docker-compose.yml` at project root (already created by agent)
2. PostgreSQL 16 Alpine image
3. Health check configured
4. Volume for data persistence
5. Environment variables from `.env`

**Verification**:
```bash
docker-compose up -d
docker-compose ps  # Should show healthy status
```

---

### T-204: Create Environment Configuration

**Priority**: P1 (Critical Path)
**Dependencies**: None
**Estimated Effort**: Small

**Description**: Create `.env.example` with all required environment variables.

**Acceptance Criteria**:
1. `.env.example` at project root (already created by agent)
2. Database configuration (POSTGRES_*, DATABASE_URL)
3. Backend configuration (JWT_SECRET, JWT_ALGORITHM, etc.)
4. Frontend configuration (NEXT_PUBLIC_*, BACKEND_URL)
5. Clear documentation comments

**Verification**:
```bash
cp .env.example .env
# Edit .env with actual values
cat .env  # Should have all required vars
```

---

## Layer 1: Database Models

### T-205: Create SQLModel User Model

**Priority**: P1 (Critical Path)
**Dependencies**: T-201
**Estimated Effort**: Small

**Description**: Implement the User entity with SQLModel.

**Acceptance Criteria**:
1. `backend/app/models/user.py` exists
2. `UserBase`, `UserCreate`, `User`, `UserRead` classes defined
3. UUID primary key with `uuid4` default
4. Email field with unique constraint and index
5. `password_hash` field (not `password`)
6. `created_at` timestamp with UTC default
7. Relationship to Task (back_populates="user")

**Verification**:
```python
from app.models.user import User, UserCreate, UserRead
user = User(email="test@example.com", password_hash="hash")
print(user.id)  # Should print UUID
```

---

### T-206: Create SQLModel Task Model

**Priority**: P1 (Critical Path)
**Dependencies**: T-201, T-205
**Estimated Effort**: Small

**Description**: Implement the Task entity with SQLModel, evolving from Phase 1.

**Acceptance Criteria**:
1. `backend/app/models/task.py` exists
2. `TaskBase`, `TaskCreate`, `TaskUpdate`, `Task`, `TaskRead` classes defined
3. UUID primary key with `uuid4` default
4. `user_id` foreign key to User
5. `title` (1-200 chars), `description` (0-1000 chars)
6. `completed` boolean default False
7. `created_at` and `updated_at` timestamps
8. Relationship to User (back_populates="tasks")

**Verification**:
```python
from app.models.task import Task, TaskCreate
from uuid import uuid4
task = Task(user_id=uuid4(), title="Test")
print(task.id, task.completed)  # UUID, False
```

---

### T-207: Initialize Alembic

**Priority**: P1 (Critical Path)
**Dependencies**: T-201
**Estimated Effort**: Small

**Description**: Set up Alembic for database migrations with SQLModel.

**Acceptance Criteria**:
1. `alembic init alembic` executed
2. `alembic.ini` configured with sqlalchemy.url placeholder
3. `alembic/env.py` imports SQLModel metadata
4. `alembic/env.py` imports all models (User, Task)
5. Uses async driver configuration for asyncpg

**Verification**:
```bash
cd phase-2-web/backend
alembic check  # Should report no issues
```

---

### T-208: Create Initial Database Migration

**Priority**: P1 (Critical Path)
**Dependencies**: T-205, T-206, T-207, T-203
**Estimated Effort**: Small

**Description**: Generate and apply the initial database schema migration.

**Acceptance Criteria**:
1. `alembic revision --autogenerate -m "Initial schema"` succeeds
2. Migration file in `alembic/versions/`
3. `alembic upgrade head` applies successfully
4. `user` table exists in database
5. `task` table exists with foreign key to user
6. Indexes created (email, user_id, created_at)

**Verification**:
```bash
docker-compose up -d
alembic upgrade head
# Connect to DB and verify tables exist
```

---

## Layer 2: Backend Core

### T-209: Implement Core Configuration

**Priority**: P1 (Critical Path)
**Dependencies**: T-201, T-204
**Estimated Effort**: Small

**Description**: Create Pydantic Settings for configuration management.

**Acceptance Criteria**:
1. `backend/app/core/config.py` exists
2. `Settings` class with Pydantic BaseSettings
3. Loads from `.env` file
4. Fields: DATABASE_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION
5. Singleton pattern with `get_settings()` function

**Verification**:
```python
from app.core.config import get_settings
settings = get_settings()
print(settings.JWT_SECRET)  # Should print value from .env
```

---

### T-210: Implement Security Utilities

**Priority**: P1 (Critical Path)
**Dependencies**: T-209
**Estimated Effort**: Small

**Description**: Implement JWT and password hashing utilities.

**Acceptance Criteria**:
1. `backend/app/core/security.py` exists
2. `hash_password(password: str) -> str` using bcrypt
3. `verify_password(plain: str, hashed: str) -> bool`
4. `create_access_token(user_id: UUID) -> str` creates JWT
5. `decode_access_token(token: str) -> dict` validates and decodes JWT
6. JWT includes `sub` (user_id), `iat`, `exp` claims

**Verification**:
```python
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from uuid import uuid4

hashed = hash_password("password123")
assert verify_password("password123", hashed)

user_id = uuid4()
token = create_access_token(user_id)
payload = decode_access_token(token)
assert payload["sub"] == str(user_id)
```

---

### T-211: Implement Database Session

**Priority**: P1 (Critical Path)
**Dependencies**: T-208, T-209
**Estimated Effort**: Small

**Description**: Create database engine and session management.

**Acceptance Criteria**:
1. `backend/app/core/database.py` exists
2. SQLModel async engine creation
3. `get_session()` async generator for dependency injection
4. Connection pooling configured
5. Proper cleanup on shutdown

**Verification**:
```python
from app.core.database import get_session
from sqlmodel import select
from app.models.user import User

async def test():
    async for session in get_session():
        result = await session.exec(select(User))
        print(list(result))
```

---

### T-212: Port TaskService from Phase 1

**Priority**: P1 (Critical Path)
**Dependencies**: T-206, T-211
**Estimated Effort**: Medium

**Description**: Implement TaskService with async methods and multi-tenant support.

**Acceptance Criteria**:
1. `backend/app/services/task_service.py` exists
2. `create_task(session, user_id, data: TaskCreate) -> Task`
3. `list_tasks(session, user_id, limit, offset) -> List[Task]`
4. `get_task(session, user_id, task_id) -> Task | None`
5. `update_task(session, user_id, task_id, data: TaskUpdate) -> Task`
6. `delete_task(session, user_id, task_id) -> bool`
7. `toggle_complete(session, user_id, task_id) -> Task`
8. All methods scoped by user_id (multi-tenancy)
9. Validation: title 1-200 chars, description 0-1000 chars

**Verification**:
```bash
cd phase-2-web/backend
pytest tests/test_task_service.py -v
```

---

### T-213: Implement AuthService

**Priority**: P1 (Critical Path)
**Dependencies**: T-205, T-210, T-211
**Estimated Effort**: Medium

**Description**: Implement authentication service with register and login.

**Acceptance Criteria**:
1. `backend/app/services/auth_service.py` exists
2. `register(session, email, password) -> User` with duplicate check
3. `login(session, email, password) -> str` returns JWT token
4. `get_user_by_id(session, user_id) -> User | None`
5. Password hashed with bcrypt
6. Raises appropriate errors for invalid credentials

**Verification**:
```bash
cd phase-2-web/backend
pytest tests/test_auth_service.py -v
```

---

## Layer 3: API Endpoints

### T-214: Implement JWT Dependency

**Priority**: P1 (Critical Path)
**Dependencies**: T-210
**Estimated Effort**: Small

**Description**: Create FastAPI dependency for JWT authentication.

**Acceptance Criteria**:
1. `backend/app/api/deps.py` exists
2. `get_current_user(credentials) -> UUID` dependency
3. Uses HTTPBearer security scheme
4. Returns 401 for missing/invalid/expired tokens
5. Error response follows `{success: false, error: {code, message}}` format

**Verification**:
```python
# Tested via endpoint integration
```

---

### T-215: Implement Auth Endpoints

**Priority**: P1 (Critical Path)
**Dependencies**: T-213, T-214
**Estimated Effort**: Medium

**Description**: Implement authentication API endpoints.

**Acceptance Criteria**:
1. `backend/app/api/v1/auth.py` exists
2. `POST /api/v1/auth/register` - creates user, returns user data
3. `POST /api/v1/auth/login` - returns JWT token
4. `POST /api/v1/auth/logout` - returns success (client clears token)
5. `GET /api/v1/auth/me` - returns current user (requires auth)
6. Response format: `{success: true, data: {...}}`
7. Error format: `{success: false, error: {code, message}}`

**Verification**:
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

---

### T-216: Implement Task Endpoints

**Priority**: P1 (Critical Path)
**Dependencies**: T-212, T-214
**Estimated Effort**: Medium

**Description**: Implement task CRUD API endpoints.

**Acceptance Criteria**:
1. `backend/app/api/v1/tasks.py` exists
2. `GET /api/v1/tasks` - list tasks with pagination
3. `POST /api/v1/tasks` - create task
4. `GET /api/v1/tasks/{task_id}` - get single task
5. `PUT /api/v1/tasks/{task_id}` - update task
6. `DELETE /api/v1/tasks/{task_id}` - delete task
7. `PATCH /api/v1/tasks/{task_id}/complete` - toggle completion
8. All endpoints require JWT authentication
9. All queries scoped by user_id from JWT
10. 404 for non-existent or other user's tasks

**Verification**:
```bash
TOKEN="your_jwt_token"

# List tasks
curl -X GET http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN"

# Create task
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Buy groceries"}'
```

---

### T-217: Create FastAPI Main Entry Point

**Priority**: P1 (Critical Path)
**Dependencies**: T-215, T-216
**Estimated Effort**: Small

**Description**: Create the FastAPI application entry point with router registration.

**Acceptance Criteria**:
1. `backend/app/main.py` exists
2. FastAPI app with title and version
3. `/api/v1` router includes auth and tasks routers
4. CORS middleware configured (for development)
5. Exception handlers for consistent error responses
6. Health check endpoint at `/health`

**Verification**:
```bash
cd phase-2-web/backend
uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health
# Should return {"status": "healthy"}
```

---

## Layer 4: Frontend Foundation

### T-218: Create TypeScript Types

**Priority**: P1 (Critical Path)
**Dependencies**: T-202
**Estimated Effort**: Small

**Description**: Define TypeScript interfaces matching backend models.

**Acceptance Criteria**:
1. `frontend/types/index.ts` exists
2. User, Task, and API response types defined
3. Request types: RegisterRequest, LoginRequest, TaskCreateRequest, TaskUpdateRequest
4. Response types: AuthResponse, TaskResponse, TaskListResponse, ErrorResponse
5. ApiResponse union type

**Verification**:
```bash
cd phase-2-web/frontend
pnpm tsc --noEmit  # No type errors
```

---

### T-219: Create UI Components

**Priority**: P2
**Dependencies**: T-202, T-218
**Estimated Effort**: Medium

**Description**: Create reusable UI components with Tailwind CSS.

**Acceptance Criteria**:
1. `components/ui/Button.tsx` - with variants (primary, secondary, danger)
2. `components/ui/Input.tsx` - with label and error state
3. `components/ui/Card.tsx` - container component
4. `components/ui/Modal.tsx` - dialog component
5. All components use Tailwind CSS
6. Accessible (proper ARIA attributes)

**Verification**:
Visual inspection in Storybook or development mode.

---

### T-220: Create Auth Pages

**Priority**: P1 (Critical Path)
**Dependencies**: T-218, T-219
**Estimated Effort**: Medium

**Description**: Create login and registration pages.

**Acceptance Criteria**:
1. `app/(auth)/login/page.tsx` - login form
2. `app/(auth)/register/page.tsx` - registration form
3. Form validation (email format, password length)
4. Error display for invalid credentials
5. Redirect to dashboard on success
6. Link between login and register pages

**Verification**:
Navigate to `/login` and `/register` in browser.

---

### T-221: Create Dashboard Layout

**Priority**: P1 (Critical Path)
**Dependencies**: T-202
**Estimated Effort**: Small

**Description**: Create authenticated dashboard layout with auth guard.

**Acceptance Criteria**:
1. `app/(dashboard)/layout.tsx` exists
2. Reads auth-token from cookies
3. Redirects to /login if no token
4. Fetches user info from /api/v1/auth/me
5. Displays user email in header
6. Logout button that clears cookie

**Verification**:
1. Without token: redirects to /login
2. With valid token: shows dashboard
3. With expired token: redirects to /login

---

### T-222: Create Task List Component

**Priority**: P1 (Critical Path)
**Dependencies**: T-218, T-219
**Estimated Effort**: Medium

**Description**: Create the main task list component.

**Acceptance Criteria**:
1. `components/tasks/TaskList.tsx` - container for task items
2. `components/tasks/TaskItem.tsx` - individual task display
3. Shows title, description, completion status
4. Checkbox to toggle completion
5. Edit button to open edit modal
6. Delete button with confirmation
7. Empty state when no tasks

**Verification**:
Visual inspection in development mode.

---

## Layer 5: Integration

### T-223: Configure API Proxy

**Priority**: P1 (Critical Path)
**Dependencies**: T-202, T-217
**Estimated Effort**: Small

**Description**: Configure Next.js rewrites for API proxy.

**Acceptance Criteria**:
1. `frontend/next.config.js` with rewrites
2. `/api/*` proxies to `${BACKEND_URL}/api/*`
3. Environment variable for BACKEND_URL
4. Works in development (localhost:8000)

**Verification**:
```bash
# Start backend on :8000
# Start frontend on :3000
curl http://localhost:3000/api/v1/health
# Should proxy to backend and return health response
```

---

### T-224: Implement Middleware

**Priority**: P1 (Critical Path)
**Dependencies**: T-202
**Estimated Effort**: Small

**Description**: Create Next.js middleware for auth and header injection.

**Acceptance Criteria**:
1. `frontend/middleware.ts` exists
2. Protects `/dashboard/*` routes (redirect to /login if no token)
3. Injects Authorization header for `/api/*` requests
4. Reads token from `auth-token` cookie
5. Matcher config for relevant paths

**Verification**:
1. Access /dashboard without cookie -> redirects to /login
2. Access /api/* with cookie -> Authorization header added

---

### T-225: Implement Auth Server Actions

**Priority**: P1 (Critical Path)
**Dependencies**: T-215, T-224
**Estimated Effort**: Medium

**Description**: Create Server Actions for authentication.

**Acceptance Criteria**:
1. `app/actions/auth.ts` with `'use server'`
2. `register(formData)` - calls backend, handles errors
3. `login(formData)` - calls backend, sets httpOnly cookie
4. `logout()` - clears cookie, redirects to /login
5. Proper error handling and user feedback

**Verification**:
1. Register new user via form
2. Login with valid credentials
3. Logout clears session

---

### T-226: Implement Task Server Actions

**Priority**: P1 (Critical Path)
**Dependencies**: T-216, T-224
**Estimated Effort**: Medium

**Description**: Create Server Actions for task CRUD.

**Acceptance Criteria**:
1. `app/actions/tasks.ts` with `'use server'`
2. `createTask(formData)` - creates task, revalidatePath
3. `updateTask(taskId, formData)` - updates task
4. `deleteTask(taskId)` - deletes task
5. `toggleComplete(taskId)` - toggles completion
6. All actions read token from cookies
7. All actions call revalidatePath('/dashboard')

**Verification**:
1. Create task via form
2. Edit task
3. Delete task
4. Toggle completion

---

### T-227: Wire Components to Actions

**Priority**: P1 (Critical Path)
**Dependencies**: T-222, T-225, T-226
**Estimated Effort**: Medium

**Description**: Connect frontend components to Server Actions.

**Acceptance Criteria**:
1. LoginForm calls login action
2. RegisterForm calls register action
3. TaskForm calls createTask/updateTask
4. TaskItem checkbox calls toggleComplete
5. Delete button calls deleteTask
6. Dashboard page fetches tasks on mount
7. All mutations trigger UI refresh via revalidatePath

**Verification**:
End-to-end flow:
1. Register -> Login -> Create Task -> Complete Task -> Delete Task -> Logout

---

## Layer 6: Polish

### T-228: Add Loading States

**Priority**: P2
**Dependencies**: T-227
**Estimated Effort**: Small

**Description**: Add loading indicators for async operations.

**Acceptance Criteria**:
1. Button shows loading spinner during form submission
2. Task list shows skeleton while loading
3. Page transitions show loading indicator
4. Disable form inputs during submission

**Verification**:
Visual inspection during slow network simulation.

---

### T-229: Add Toast Notifications

**Priority**: P2
**Dependencies**: T-227
**Estimated Effort**: Small

**Description**: Add success/error notifications for user actions.

**Acceptance Criteria**:
1. Success toast on task creation
2. Success toast on task update
3. Success toast on task deletion
4. Error toast on failed operations
5. Auto-dismiss after 3 seconds

**Verification**:
Perform CRUD operations and observe notifications.

---

### T-230: Add Delete Confirmation Dialog

**Priority**: P2
**Dependencies**: T-227
**Estimated Effort**: Small

**Description**: Add confirmation dialog before task deletion.

**Acceptance Criteria**:
1. Click delete shows confirmation modal
2. Modal has "Cancel" and "Delete" buttons
3. Cancel closes modal, task unchanged
4. Delete removes task and closes modal
5. Modal is accessible (keyboard navigation, focus trap)

**Verification**:
1. Click delete -> modal appears
2. Cancel -> modal closes, task exists
3. Confirm -> task deleted

---

### T-231: Add Form Validation Messages

**Priority**: P2
**Dependencies**: T-227
**Estimated Effort**: Small

**Description**: Add client-side validation with clear error messages.

**Acceptance Criteria**:
1. Email format validation on auth forms
2. Password length validation (min 8 chars)
3. Title required validation on task form
4. Title length validation (max 200 chars)
5. Description length validation (max 1000 chars)
6. Error messages displayed below input fields
7. Submit disabled when validation fails

**Verification**:
1. Submit empty form -> shows errors
2. Enter invalid email -> shows format error
3. Enter short password -> shows length error

---

## Layer 7: Validation

### T-232: Run Acceptance Scenarios

**Priority**: P1 (Critical Path)
**Dependencies**: T-228, T-229, T-230, T-231
**Estimated Effort**: Medium

**Description**: Manually verify all acceptance scenarios from spec.

**Acceptance Criteria**:
Verify all scenarios from spec.md Section 3:
- [ ] User Registration (5 scenarios)
- [ ] User Login (5 scenarios)
- [ ] Add Task (5 scenarios)
- [ ] View Task List (5 scenarios)
- [ ] Update Task (4 scenarios)
- [ ] Delete Task (3 scenarios)
- [ ] Mark Complete (3 scenarios)

**Verification**:
Document pass/fail for each scenario in acceptance test report.

---

### T-233: Create PHR for Phase 2

**Priority**: P1 (Critical Path)
**Dependencies**: T-232
**Estimated Effort**: Small

**Description**: Create Prompt History Record for Phase 2 implementation.

**Acceptance Criteria**:
1. PHR file in `history/prompts/phase-2-web/`
2. Documents key implementation decisions
3. Lists files created/modified
4. Notes any deviations from spec
5. Includes lessons learned

**Verification**:
PHR file exists and is properly formatted.

---

### T-234: Update Root CLAUDE.md

**Priority**: P1 (Critical Path)
**Dependencies**: T-233
**Estimated Effort**: Small

**Description**: Update project CLAUDE.md with Phase 2 completion status.

**Acceptance Criteria**:
1. Phase 2 marked complete in constitution
2. Feature checklist updated
3. Phase 2 due date noted (even if past)
4. Any technical debt documented

**Verification**:
Read CLAUDE.md and verify Phase 2 section is complete.

---

## Summary

| Layer | Tasks | P1 (Critical) | P2 (Important) |
|-------|-------|---------------|----------------|
| 0: Infrastructure | T-201 to T-204 | 4 | 0 |
| 1: Database | T-205 to T-208 | 4 | 0 |
| 2: Backend Core | T-209 to T-213 | 5 | 0 |
| 3: API | T-214 to T-217 | 4 | 0 |
| 4: Frontend | T-218 to T-222 | 4 | 1 |
| 5: Integration | T-223 to T-227 | 5 | 0 |
| 6: Polish | T-228 to T-231 | 0 | 4 |
| 7: Validation | T-232 to T-234 | 3 | 0 |
| **Total** | **34** | **29** | **5** |

**Critical Path**: T-201 → T-205/T-206 → T-208 → T-211 → T-212/T-213 → T-214 → T-215/T-216 → T-217 → T-223/T-224 → T-225/T-226 → T-227 → T-232

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Task Orchestrator | Initial task breakdown |

---

**End of Task List**
