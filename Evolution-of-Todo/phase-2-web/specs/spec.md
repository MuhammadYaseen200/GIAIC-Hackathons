# Feature Specification: Full-Stack Web Application

**Feature Branch**: `002-fullstack-web`
**Created**: 2025-12-29
**Status**: Draft
**Phase**: Phase II - Full-Stack Web Application
**Input**: User description: "Evolve Phase I in-memory console app into a full-stack web application with Next.js frontend, FastAPI backend, Neon PostgreSQL database, and Better Auth authentication"

---

## 1. Purpose & Context

- **What**: A multi-user web application that provides authenticated task management with persistent storage
- **Why**: Evolve the Phase I console app to a production-ready web application with proper authentication, database persistence, and RESTful API architecture
- **Where**: Standalone full-stack application; backend exposes REST API consumed by Next.js frontend; prepares foundation for Phase III AI chatbot integration

---

## 2. Constraints (MANDATORY)

### NOT Supported (Phase II)

- Task priorities (high/medium/low)
- Tags or categories
- Due dates or time reminders
- Recurring tasks
- Search and filter functionality
- Task sorting beyond default (created_at DESC)
- Task sharing between users
- Batch operations (bulk create/update/delete)
- File attachments
- Nested tasks or subtasks
- Task comments
- Social login (Google, GitHub, etc.) - email/password only
- Password reset via email (manual reset only)
- Email verification
- Two-factor authentication (2FA)
- Session management UI (view/revoke sessions)
- API versioning beyond `/v1/` prefix

### Performance Limits

- **Max Request Body Size**: 10KB
- **Max Response Time**: 500ms (p99)
- **Max Tasks Per User**: 1000 (enforced at database level)
- **Rate Limit**: 100 requests/minute per authenticated user
- **Max Title Length**: 200 characters
- **Max Description Length**: 1000 characters
- **Max Email Length**: 254 characters
- **Min Password Length**: 8 characters

### Security Boundaries

- **Authentication**: Required for ALL task endpoints (Bearer JWT)
- **Authorization**: Users can ONLY access their own tasks
- **Data Isolation**: All queries MUST be scoped by `user_id` from JWT claims
- **Password Storage**: bcrypt hashing with cost factor 12
- **JWT Expiration**: 24 hours (configurable)
- **HTTPS Only**: Production endpoints must use TLS
- **CORS**: Configured for frontend origin only

### Technical Debt (Accepted for Phase II)

- No caching layer (add in Phase IV)
- No real-time updates / WebSocket (add in Phase III)
- No email delivery system
- No API rate limiting dashboard
- No audit logging for security events

---

## 3. User Scenarios & Testing

### User Story 1 - User Registration (Priority: P1)

As a new user, I want to create an account so that I can access the todo application and have my tasks saved persistently.

**Why this priority**: Users cannot use the application without an account. This is the entry point to the entire system.

**Independent Test**: Can be fully tested by navigating to the registration page, filling in credentials, and verifying account creation. Delivers immediate value by enabling access to the system.

**Acceptance Scenarios**:

1. **Given** I am on the registration page, **When** I enter a valid email "user@example.com" and password "SecurePass123", **Then** my account is created and I am redirected to the login page with a success message
2. **Given** I am on the registration page, **When** I enter an email that already exists, **Then** I see an error message "An account with this email already exists"
3. **Given** I am on the registration page, **When** I enter a password shorter than 8 characters, **Then** I see a validation error "Password must be at least 8 characters"
4. **Given** I am on the registration page, **When** I enter an invalid email format, **Then** I see a validation error "Please enter a valid email address"
5. **Given** I am on the registration page, **When** I leave required fields empty, **Then** I see appropriate validation errors for each field

---

### User Story 2 - User Login (Priority: P1)

As a registered user, I want to log in to my account so that I can access my tasks.

**Why this priority**: Login is required to access any functionality. Tied with registration as the authentication foundation.

**Independent Test**: Can be tested by entering valid credentials and verifying successful authentication with redirect to dashboard.

**Acceptance Scenarios**:

1. **Given** I have a registered account, **When** I enter my correct email and password on the login page, **Then** I am authenticated and redirected to the task dashboard
2. **Given** I enter an incorrect password, **When** I submit the login form, **Then** I see an error message "Invalid email or password" (no indication of which is wrong)
3. **Given** I enter a non-existent email, **When** I submit the login form, **Then** I see the same error "Invalid email or password" (prevents email enumeration)
4. **Given** I am logged in, **When** I navigate to the login page, **Then** I am redirected to the dashboard
5. **Given** I am logged in, **When** I click logout, **Then** my session is terminated and I am redirected to the login page

---

### User Story 3 - Add Task via Web UI (Priority: P1)

As an authenticated user, I want to add a new task through the web interface so that I can track what I need to accomplish.

**Why this priority**: Core functionality - users must be able to create tasks. This validates the entire stack (frontend -> API -> database).

**Independent Test**: Can be tested by logging in, clicking "Add Task", filling in details, and verifying the task appears in the list.

**Acceptance Scenarios**:

1. **Given** I am logged in and on the dashboard, **When** I click "Add Task" and enter title "Buy groceries", **Then** a new task is created with status "pending" and appears in my task list
2. **Given** I am adding a task, **When** I provide both title "Call mom" and description "Wish her happy birthday", **Then** both fields are saved correctly
3. **Given** I am adding a task, **When** I try to submit with an empty title, **Then** I see a validation error "Title is required" and the form is not submitted
4. **Given** I am adding a task, **When** I enter a title longer than 200 characters, **Then** I see a validation error "Title must not exceed 200 characters"
5. **Given** I add a task, **When** it is created, **Then** I see a success notification and the task list refreshes to show the new task

---

### User Story 4 - View Task List (Priority: P1)

As an authenticated user, I want to view all my tasks so that I can see what I need to do and track my progress.

**Why this priority**: Users must see their tasks to manage them. Essential for any todo application.

**Independent Test**: Can be tested by logging in and verifying the task list displays correctly with appropriate status indicators.

**Acceptance Scenarios**:

1. **Given** I have created tasks "Task A" and "Task B", **When** I view my dashboard, **Then** I see both tasks with their titles and completion status
2. **Given** I have no tasks, **When** I view my dashboard, **Then** I see an empty state message "No tasks yet. Create your first task!"
3. **Given** I have tasks with different statuses, **When** I view my dashboard, **Then** completed tasks are visually distinct from pending tasks (e.g., strikethrough, different color, checkbox state)
4. **Given** I am logged in as User A, **When** I view my dashboard, **Then** I do NOT see tasks created by User B (multi-tenancy)
5. **Given** I have multiple tasks, **When** I view my dashboard, **Then** tasks are displayed in reverse chronological order (newest first)

---

### User Story 5 - Update Task (Priority: P2)

As an authenticated user, I want to update a task's title or description so that I can correct mistakes or add more detail.

**Why this priority**: Important for task management but less frequent than viewing or adding tasks.

**Independent Test**: Can be tested by clicking edit on a task, modifying fields, and verifying changes persist.

**Acceptance Scenarios**:

1. **Given** I have a task "Buy groceries", **When** I click edit and change the title to "Buy groceries and fruits", **Then** the task is updated and I see the new title
2. **Given** I am editing a task, **When** I update only the description, **Then** the title remains unchanged
3. **Given** I am editing a task, **When** I try to save with an empty title, **Then** I see a validation error and the task is not updated
4. **Given** I edit a task, **When** it is saved, **Then** the `updated_at` timestamp is refreshed

---

### User Story 6 - Delete Task (Priority: P2)

As an authenticated user, I want to delete a task so that I can remove tasks I no longer need.

**Why this priority**: Destructive operation, used less frequently. Users typically complete tasks rather than delete them.

**Independent Test**: Can be tested by clicking delete on a task and verifying it is removed from the list.

**Acceptance Scenarios**:

1. **Given** I have a task "Old task", **When** I click delete and confirm, **Then** the task is permanently removed from my list
2. **Given** I click delete on a task, **When** a confirmation dialog appears and I cancel, **Then** the task is NOT deleted
3. **Given** I delete a task, **When** I refresh the page, **Then** the deleted task does NOT reappear

---

### User Story 7 - Mark Task Complete (Priority: P2)

As an authenticated user, I want to mark a task as complete so that I can track my progress.

**Why this priority**: Core functionality but depends on tasks existing first.

**Independent Test**: Can be tested by clicking the completion toggle and verifying the status changes.

**Acceptance Scenarios**:

1. **Given** I have a pending task, **When** I click the completion checkbox/button, **Then** the task status changes to "completed" and the UI updates immediately
2. **Given** I have a completed task, **When** I click the completion checkbox/button, **Then** the task status changes back to "pending"
3. **Given** I toggle completion, **When** I refresh the page, **Then** the completion status persists (database saved)

---

### Edge Cases

- **What happens when the JWT expires during a session?**
  - API returns 401; frontend intercepts and redirects to login with message "Session expired. Please log in again."

- **What happens if the database connection fails?**
  - API returns 503 with error code `DATABASE_ERROR`; frontend shows "Service temporarily unavailable. Please try again."

- **What happens when a user tries to access another user's task directly via URL?**
  - API returns 404 (not 403) to prevent task ID enumeration

- **What happens if the user enters special characters in title/description?**
  - System accepts all printable UTF-8 characters; XSS is prevented via JSON responses only

- **What happens if concurrent updates occur on the same task?**
  - Last-write-wins; no optimistic locking in Phase II

- **What happens if a user has 1000+ tasks?**
  - Creation fails with 400 error: "Maximum task limit (1000) reached"

---

## 4. Requirements

### Functional Requirements - Authentication

- **FR-001**: System MUST allow new users to register with email and password
- **FR-002**: System MUST validate email format (RFC 5322 compliant)
- **FR-003**: System MUST enforce minimum password length of 8 characters
- **FR-004**: System MUST store passwords using bcrypt with cost factor 12
- **FR-005**: System MUST prevent duplicate email registrations
- **FR-006**: System MUST authenticate users via email/password and issue JWT tokens
- **FR-007**: System MUST validate JWT tokens on all protected endpoints
- **FR-008**: System MUST allow users to log out (invalidate session on client)
- **FR-009**: System MUST return consistent error messages for invalid credentials (prevent enumeration)

### Functional Requirements - Task CRUD (Brownfield from Phase I)

- **FR-010**: System MUST allow authenticated users to create tasks with required title (1-200 chars)
- **FR-011**: System MUST allow optional description when creating tasks (0-1000 chars)
- **FR-012**: System MUST auto-generate UUID for each new task
- **FR-013**: System MUST auto-generate timestamps (`created_at`, `updated_at`) for tasks
- **FR-014**: System MUST allow authenticated users to list all their own tasks
- **FR-015**: System MUST allow authenticated users to view a single task by ID
- **FR-016**: System MUST allow authenticated users to update task title and/or description
- **FR-017**: System MUST allow authenticated users to delete their own tasks
- **FR-018**: System MUST allow authenticated users to toggle task completion status
- **FR-019**: System MUST enforce user isolation - users can ONLY access their own tasks

### Functional Requirements - Frontend

- **FR-020**: System MUST provide a responsive web interface using Next.js App Router
- **FR-021**: System MUST display clear loading states during API calls
- **FR-022**: System MUST display success/error notifications for user actions
- **FR-023**: System MUST provide confirmation dialogs for destructive actions (delete)
- **FR-024**: System MUST redirect unauthenticated users to login page for protected routes
- **FR-025**: System MUST persist authentication state across page refreshes

---

## 5. Key Entities

### User Entity

Represents an authenticated user of the system.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | UUID | Primary Key, Auto-generated | Unique user identifier |
| `email` | String | Unique, Required, Max 254 chars | User's email address |
| `password_hash` | String | Required | bcrypt hash of password |
| `created_at` | Timestamp | Auto-generated (UTC) | Account creation time |

### Task Entity

Represents a todo item belonging to a user.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| `id` | UUID | Primary Key, Auto-generated | Unique task identifier |
| `user_id` | UUID | Foreign Key (User.id), Required | Owner of the task |
| `title` | String | Required, 1-200 chars | Task title |
| `description` | String | Optional, 0-1000 chars, Default "" | Task details |
| `completed` | Boolean | Default false | Completion status |
| `created_at` | Timestamp | Auto-generated (UTC) | Task creation time |
| `updated_at` | Timestamp | Auto-updated (UTC) | Last modification time |

### Entity Relationships

```
User (1) ----< (N) Task
```

- One User can have many Tasks
- Each Task belongs to exactly one User
- Deleting a User cascades to delete all their Tasks

---

## 6. Data Contracts

### TypeScript Interfaces (Frontend)

```typescript
// User types
interface User {
  id: string;           // UUID
  email: string;
  created_at: string;   // ISO 8601
}

interface RegisterRequest {
  email: string;        // Required, valid email format
  password: string;     // Required, min 8 chars
}

interface LoginRequest {
  email: string;
  password: string;
}

interface AuthResponse {
  success: true;
  data: {
    user: User;
    token: string;      // JWT
    expires_at: string; // ISO 8601
  };
}

// Task types
interface Task {
  id: string;           // UUID
  user_id: string;      // UUID
  title: string;        // 1-200 chars
  description: string;  // 0-1000 chars
  completed: boolean;
  created_at: string;   // ISO 8601
  updated_at: string;   // ISO 8601
}

interface TaskCreateRequest {
  title: string;        // Required
  description?: string; // Optional
}

interface TaskUpdateRequest {
  title?: string;       // Optional, but one field required
  description?: string; // Optional
}

interface TaskListResponse {
  success: true;
  data: Task[];
  meta: {
    total: number;
    limit: number;
    offset: number;
  };
}

interface TaskResponse {
  success: true;
  data: Task;
}

interface DeleteResponse {
  success: true;
  data: {
    id: string;
    deleted: true;
  };
}

// Error types
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: Record<string, string>;
  };
}
```

### Python Models (Backend - SQLModel)

```python
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class UserBase(SQLModel):
    email: str = Field(max_length=254, unique=True, index=True)

class User(UserBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class TaskBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)

class Task(TaskBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### Database Schema (PostgreSQL)

```sql
-- Users table
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_email ON "user"(email);

-- Tasks table
CREATE TABLE task (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description VARCHAR(1000) DEFAULT '',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
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
```

---

## 7. API Endpoints Summary

Full specification in: `specs/api/rest-endpoints.md`

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create new user account |
| POST | `/api/v1/auth/login` | Authenticate and receive JWT |
| POST | `/api/v1/auth/logout` | Invalidate session (client-side) |
| GET | `/api/v1/auth/me` | Get current user info |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tasks` | List all tasks for authenticated user |
| POST | `/api/v1/tasks` | Create a new task |
| GET | `/api/v1/tasks/{task_id}` | Get a specific task |
| PUT | `/api/v1/tasks/{task_id}` | Update a task |
| DELETE | `/api/v1/tasks/{task_id}` | Delete a task |
| PATCH | `/api/v1/tasks/{task_id}/complete` | Toggle completion status |

---

## 8. Success Criteria

### SC-001: Authentication Works End-to-End

- [ ] Users can register with email/password
- [ ] Users can log in and receive JWT
- [ ] Protected routes redirect unauthenticated users
- [ ] JWT is validated on all API requests
- [ ] Invalid credentials return appropriate errors

### SC-002: All 5 CRUD Operations Function Correctly

- [ ] Add Task: Creates task with title, optional description, pending status
- [ ] View Tasks: Lists all tasks for authenticated user only
- [ ] Update Task: Modifies title/description, refreshes `updated_at`
- [ ] Delete Task: Permanently removes task from database
- [ ] Mark Complete: Toggles completion status

### SC-003: Data Persists Across Sessions

- [ ] Tasks created in one session appear after logout/login
- [ ] Database stores all task data reliably
- [ ] No data loss on application restart

### SC-004: Multi-Tenancy Enforced

- [ ] User A cannot see User B's tasks
- [ ] User A cannot modify User B's tasks
- [ ] Task queries are always scoped by `user_id`
- [ ] Accessing another user's task returns 404 (not 403)

### SC-005: Frontend Provides Good UX

- [ ] Loading states shown during API calls
- [ ] Success/error notifications display appropriately
- [ ] Confirmation required before delete
- [ ] Form validation provides clear feedback
- [ ] Responsive design works on mobile

### SC-006: Brownfield Evolution Verified

- [ ] All Phase I features (Add, View, Update, Delete, Complete) work in Phase II
- [ ] Service layer logic from Phase I is preserved in FastAPI services
- [ ] No regression in core functionality

---

## 9. Non-Functional Requirements

### Performance

- **Response Time**: < 500ms (p99) for all API endpoints
- **Page Load**: < 3s initial load, < 1s subsequent navigations
- **Database Queries**: Max 2 queries per API request
- **Concurrent Users**: Support 100 concurrent users

### Security

- **Transport**: HTTPS in production
- **Password Hashing**: bcrypt, cost factor 12
- **JWT Signing**: HS256 with 256-bit secret
- **Token Expiration**: 24 hours
- **SQL Injection**: Prevented via SQLModel parameterized queries
- **XSS Prevention**: JSON responses only, CSP headers
- **CORS**: Whitelist frontend origin only

### Reliability

- **Uptime Target**: 99% (allowing for Neon serverless cold starts)
- **Error Handling**: All errors return structured JSON responses
- **Data Integrity**: Foreign key constraints enforced

### Observability

- **Logging**: Request/response logging with correlation IDs
- **Errors**: Stack traces logged server-side, sanitized errors to client
- **Metrics**: Request count, latency by endpoint (future enhancement)

---

## 10. Integration Points

### Upstream Dependencies

- **Neon PostgreSQL**: Serverless database for persistence
- **Better Auth**: JWT generation and validation (or custom implementation)

### Downstream Consumers

- **Next.js Frontend**: Consumes REST API
- **Phase III MCP Server**: Will wrap these endpoints as MCP tools

### External Services

- **None in Phase II** (email service deferred)

---

## 11. Migration Notes (Phase I to Phase II)

### ID Format Change

| Phase I | Phase II |
|---------|----------|
| Sequential integer (1, 2, 3...) | UUID v4 |

**Rationale**: UUIDs prevent ID enumeration attacks and support distributed systems.

### Storage Change

| Phase I | Phase II |
|---------|----------|
| In-memory Python dict | Neon PostgreSQL |

**Rationale**: Persistent storage required for multi-session, multi-user application.

### User Scoping Change

| Phase I | Phase II |
|---------|----------|
| Single user (implicit) | Multi-user (JWT-based) |

**Rationale**: All queries MUST include `WHERE user_id = <jwt.sub>` for data isolation.

### Architecture Evolution

```
Phase I:                          Phase II:
+----------------+                +----------------+     +----------------+
|   Console UI   |                |  Next.js App   | --> |  FastAPI API   |
+----------------+                +----------------+     +----------------+
        |                                                        |
+----------------+                                       +----------------+
| TodoService    |  ---- EVOLVES TO ---->                | TaskService    |
+----------------+                                       +----------------+
        |                                                        |
+----------------+                                       +----------------+
| MemoryRepo     |  ---- REPLACED BY ---->               | SQLModel/Neon  |
+----------------+                                       +----------------+
```

---

## 12. Out of Scope (Deferred to Later Phases)

### Deferred to Phase V

- Task priorities (high/medium/low)
- Tags and categories
- Due dates and time reminders
- Recurring tasks
- Search and filter functionality
- Task sorting options

### Deferred to Phase III

- AI chatbot interface
- MCP tool integration
- Natural language task management

### Deferred to Phase IV

- Docker containerization
- Kubernetes deployment
- Helm charts
- Caching layer

---

## 13. Technology Stack (Phase II)

| Layer | Technology | Version |
|-------|------------|---------|
| Frontend Framework | Next.js (App Router) | 15+ |
| Frontend Language | TypeScript | 5+ |
| UI Styling | Tailwind CSS | 3+ |
| Backend Framework | FastAPI | 0.100+ |
| Backend Language | Python | 3.13+ |
| ORM | SQLModel | 0.0.14+ |
| Database | Neon Serverless PostgreSQL | - |
| Authentication | Better Auth (or custom JWT) | - |
| Package Manager (Python) | UV | - |
| Package Manager (Node) | pnpm | 8+ |

---

## 14. Acceptance Testing Checklist

### Authentication Tests

- [ ] Register with valid credentials succeeds
- [ ] Register with duplicate email fails
- [ ] Register with invalid email fails
- [ ] Register with short password fails
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials fails (same error message)
- [ ] Protected endpoints reject missing token
- [ ] Protected endpoints reject expired token
- [ ] Logout clears client session

### Task CRUD Tests

- [ ] Create task with title only succeeds
- [ ] Create task with title and description succeeds
- [ ] Create task with empty title fails
- [ ] Create task with too-long title fails
- [ ] List tasks returns only current user's tasks
- [ ] List tasks returns empty array for new user
- [ ] Get task by ID succeeds for owner
- [ ] Get task by ID fails for non-owner (404)
- [ ] Update task title succeeds
- [ ] Update task description succeeds
- [ ] Update task with empty title fails
- [ ] Delete task succeeds for owner
- [ ] Delete task fails for non-owner (404)
- [ ] Toggle completion changes status
- [ ] Toggle completion updates `updated_at`

### Frontend Tests

- [ ] Registration form validates input
- [ ] Login form validates input
- [ ] Dashboard shows loading state
- [ ] Task list renders correctly
- [ ] Add task form works
- [ ] Edit task modal works
- [ ] Delete confirmation dialog works
- [ ] Success notifications appear
- [ ] Error notifications appear
- [ ] Responsive on mobile viewport

---

## Approval

**Specification Status**: Draft - Ready for Review

- [ ] All user stories have acceptance scenarios
- [ ] Functional requirements cover auth + CRUD
- [ ] Data contracts defined (TypeScript, Python, SQL)
- [ ] Success criteria are measurable
- [ ] Constraints and out-of-scope clearly defined
- [ ] Migration from Phase I documented

**Next Steps**:
1. Upon approval, proceed to `/sp.plan` for architectural planning
2. Create detailed database schema spec (`specs/database/schema.md`)
3. Create frontend component spec (`specs/ui/components.md`)
4. Create authentication flow spec (`specs/api/auth.md`)

---

**Version**: 1.0.0 | **Author**: spec-architect | **Phase**: II
