# Tasks: Phase 2 Full-Stack Web Application

**Input**: Design documents from `phase-2-web/specs/`
**Prerequisites**: plan.md (required), spec.md (required), data-model.md, research.md
**Branch**: `phase-2-web-init`
**Date**: 2025-12-29
**Status**: Ready for Implementation

---

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions (Web App)

- **Backend**: `phase-2-web/backend/`
- **Frontend**: `phase-2-web/frontend/`
- **Root**: `phase-2-web/` (docker-compose, .env)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create backend project structure per plan.md in phase-2-web/backend/
- [x] T002 [P] Initialize FastAPI project with pyproject.toml in phase-2-web/backend/pyproject.toml
- [x] T003 [P] Create frontend Next.js 15+ project with App Router in phase-2-web/frontend/
- [x] T004 [P] Create docker-compose.yml for PostgreSQL in phase-2-web/docker-compose.yml
- [x] T005 [P] Create .env.example with all required environment variables in phase-2-web/.env.example
- [x] T006 [P] Create backend CLAUDE.md with implementation instructions in phase-2-web/backend/CLAUDE.md
- [x] T007 [P] Create frontend CLAUDE.md with implementation instructions in phase-2-web/frontend/CLAUDE.md

**Verification**:
```bash
# Backend structure exists
ls phase-2-web/backend/app/

# Frontend runs
cd phase-2-web/frontend && pnpm dev

# Docker PostgreSQL starts
docker-compose -f phase-2-web/docker-compose.yml up -d
```

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

### Database & Models

- [x] T008 Create SQLModel User model in phase-2-web/backend/app/models/user.py
- [x] T009 Create SQLModel Task model in phase-2-web/backend/app/models/task.py
- [x] T010 Create models __init__.py exporting User, Task in phase-2-web/backend/app/models/__init__.py
- [x] T011 Initialize Alembic with SQLModel metadata in phase-2-web/backend/alembic/
- [x] T012 Create initial database migration in phase-2-web/backend/alembic/versions/

### Core Infrastructure

- [x] T013 [P] Implement Pydantic Settings configuration in phase-2-web/backend/app/core/config.py
- [x] T014 [P] Implement JWT encode/decode and password hashing in phase-2-web/backend/app/core/security.py
- [x] T015 Implement async database session management in phase-2-web/backend/app/core/database.py
- [x] T016 [P] Create core __init__.py exports in phase-2-web/backend/app/core/__init__.py

### Backend Services

- [x] T017 Implement AuthService (register, login, get_user) in phase-2-web/backend/app/services/auth_service.py
- [x] T018 Port TaskService from Phase 1 with multi-tenancy in phase-2-web/backend/app/services/task_service.py
- [x] T019 [P] Create services __init__.py exports in phase-2-web/backend/app/services/__init__.py

### API Framework

- [x] T020 Implement JWT authentication dependency in phase-2-web/backend/app/api/deps.py
- [x] T021 Create API v1 router aggregation in phase-2-web/backend/app/api/v1/router.py
- [x] T022 Create FastAPI main entry point with router registration in phase-2-web/backend/app/main.py

### Frontend Foundation

- [x] T023 [P] Create TypeScript types matching backend models in phase-2-web/frontend/types/index.ts
- [x] T024 [P] Create lib/api.ts fetch wrapper with error handling in phase-2-web/frontend/lib/api.ts
- [x] T025 Implement Next.js middleware for auth and header injection in phase-2-web/frontend/middleware.ts
- [x] T026 Configure next.config.ts API proxy rewrites in phase-2-web/frontend/next.config.ts

**Verification**:
```bash
# Backend starts
cd phase-2-web/backend && uvicorn app.main:app --port 8000

# Alembic migration works
alembic upgrade head

# Frontend compiles
cd phase-2-web/frontend && pnpm tsc --noEmit
```

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - User Registration (Priority: P1)

**Goal**: Allow new users to create accounts and access the system

**Independent Test**: Navigate to /register, fill credentials, verify account created and redirected to login

### Implementation for User Story 1

- [x] T027 [US1] Implement POST /api/v1/auth/register endpoint in phase-2-web/backend/app/api/v1/auth.py
- [x] T028 [P] [US1] Create RegisterForm component with validation in phase-2-web/frontend/components/auth/RegisterForm.tsx
- [x] T029 [P] [US1] Create Button UI component with variants in phase-2-web/frontend/components/ui/Button.tsx
- [x] T030 [P] [US1] Create Input UI component with error state in phase-2-web/frontend/components/ui/Input.tsx
- [x] T031 [US1] Create register page using RegisterForm in phase-2-web/frontend/app/(auth)/register/page.tsx
- [x] T032 [US1] Implement register Server Action in phase-2-web/frontend/app/actions/auth.ts

**Acceptance Criteria** (from spec.md):
- [x] Valid email/password creates account, redirects to login with success message ✅
- [x] Duplicate email shows "An account with this email already exists" ✅
- [x] Password < 8 chars shows "Password must be at least 8 characters" ✅
- [x] Invalid email format shows "Please enter a valid email address" ✅
- [x] Empty fields show validation errors ✅

**Checkpoint**: User Story 1 complete - users can register accounts ✅ VERIFIED

---

## Phase 4: User Story 2 - User Login (Priority: P1)

**Goal**: Allow registered users to authenticate and access their tasks

**Independent Test**: Login with valid credentials, verify JWT cookie set, redirected to dashboard

### Implementation for User Story 2

- [x] T033 [US2] Implement POST /api/v1/auth/login endpoint in phase-2-web/backend/app/api/v1/auth.py
- [x] T034 [US2] Implement POST /api/v1/auth/logout endpoint in phase-2-web/backend/app/api/v1/auth.py
- [x] T035 [US2] Implement GET /api/v1/auth/me endpoint in phase-2-web/backend/app/api/v1/auth.py
- [x] T036 [P] [US2] Create LoginForm component with validation in phase-2-web/frontend/components/auth/LoginForm.tsx
- [x] T037 [US2] Create login page using LoginForm in phase-2-web/frontend/app/(auth)/login/page.tsx
- [x] T038 [US2] Implement login Server Action (sets httpOnly cookie) in phase-2-web/frontend/app/actions/auth.ts
- [x] T039 [US2] Implement logout Server Action (clears cookie) in phase-2-web/frontend/app/actions/auth.ts

**Acceptance Criteria** (from spec.md):
- [x] Valid credentials authenticate and redirect to dashboard ✅
- [x] Invalid password shows "Invalid email or password" (no indication which is wrong) ✅
- [x] Non-existent email shows same error (prevents enumeration) ✅
- [x] Logged-in user accessing /login redirects to dashboard ✅
- [x] Logout terminates session and redirects to login ✅

**Checkpoint**: User Story 2 complete - users can login/logout ✅ VERIFIED

---

## Phase 5: User Story 3 - Add Task (Priority: P1)

**Goal**: Allow authenticated users to create new tasks

**Independent Test**: Login, click Add Task, enter title, verify task appears in list

### Implementation for User Story 3

- [x] T040 [US3] Implement POST /api/v1/tasks endpoint in phase-2-web/backend/app/api/v1/tasks.py
- [x] T041 [P] [US3] Create Card UI component in phase-2-web/frontend/components/ui/Card.tsx
- [x] T042 [P] [US3] Create TaskForm component for create/edit in phase-2-web/frontend/components/tasks/TaskForm.tsx
- [x] T043 [US3] Implement createTask Server Action in phase-2-web/frontend/app/actions/tasks.ts

**Acceptance Criteria** (from spec.md):
- [x] Add Task with title creates task with status "pending" ✅
- [x] Title + description both saved correctly ✅
- [x] Empty title shows "Title is required" ✅
- [x] Title > 200 chars shows "Title must not exceed 200 characters" ✅
- [x] Success notification appears, task list refreshes ✅

**Checkpoint**: User Story 3 complete - users can create tasks ✅ VERIFIED

---

## Phase 6: User Story 4 - View Task List (Priority: P1)

**Goal**: Allow authenticated users to see all their tasks

**Independent Test**: Login with user who has tasks, verify list displays with status indicators

### Implementation for User Story 4

- [x] T044 [US4] Implement GET /api/v1/tasks endpoint with pagination in phase-2-web/backend/app/api/v1/tasks.py
- [x] T045 [US4] Implement GET /api/v1/tasks/{task_id} endpoint in phase-2-web/backend/app/api/v1/tasks.py
- [x] T046 [P] [US4] Create TaskList container component in phase-2-web/frontend/components/tasks/TaskList.tsx
- [x] T047 [P] [US4] Create TaskItem display component in phase-2-web/frontend/components/tasks/TaskItem.tsx
- [x] T048 [US4] Create dashboard layout with auth guard in phase-2-web/frontend/app/dashboard/layout.tsx
- [x] T049 [US4] Create dashboard page with task list in phase-2-web/frontend/app/dashboard/page.tsx
- [x] T050 [US4] Implement getTasks Server Action in phase-2-web/frontend/app/actions/tasks.ts

**Acceptance Criteria** (from spec.md):
- [x] Dashboard shows all user's tasks with titles and status ✅
- [x] Empty state shows "No tasks yet. Create your first task!" ✅
- [x] Completed tasks visually distinct (strikethrough, checkbox checked) ✅
- [x] User A cannot see User B's tasks (multi-tenancy) ✅
- [x] Tasks in reverse chronological order (newest first) ✅

**Checkpoint**: User Story 4 complete - users can view their tasks ✅ VERIFIED

---

## Phase 7: User Story 5 - Update Task (Priority: P2)

**Goal**: Allow users to modify task title or description

**Independent Test**: Click edit on task, modify fields, verify changes persist

### Implementation for User Story 5

- [x] T051 [US5] Implement PUT /api/v1/tasks/{task_id} endpoint in phase-2-web/backend/app/api/v1/tasks.py
- [x] T052 [P] [US5] Create Modal UI component for dialogs in phase-2-web/frontend/components/ui/Modal.tsx (implemented inline in TaskItem.tsx per Smallest Viable Diff)
- [x] T053 [US5] Add edit functionality to TaskItem component in phase-2-web/frontend/components/tasks/TaskItem.tsx
- [x] T054 [US5] Implement updateTask Server Action in phase-2-web/frontend/app/actions/tasks.ts

**Acceptance Criteria** (from spec.md):
- [x] Edit title saves and displays new title ✅
- [x] Edit description only leaves title unchanged ✅
- [x] Empty title on save shows validation error ✅
- [x] updated_at timestamp refreshed on save ✅

**Checkpoint**: User Story 5 complete - users can edit tasks ✅ VERIFIED

---

## Phase 8: User Story 6 - Delete Task (Priority: P2)

**Goal**: Allow users to permanently remove tasks

**Independent Test**: Click delete on task, confirm, verify task removed from list

### Implementation for User Story 6

- [x] T055 [US6] Implement DELETE /api/v1/tasks/{task_id} endpoint in phase-2-web/backend/app/api/v1/tasks.py
- [x] T056 [P] [US6] Create DeleteConfirmDialog component in phase-2-web/frontend/components/tasks/DeleteConfirmDialog.tsx (implemented inline in TaskItem.tsx per Smallest Viable Diff)
- [x] T057 [US6] Add delete functionality to TaskItem component in phase-2-web/frontend/components/tasks/TaskItem.tsx
- [x] T058 [US6] Implement deleteTask Server Action in phase-2-web/frontend/app/actions/tasks.ts

**Acceptance Criteria** (from spec.md):
- [x] Delete + confirm permanently removes task ✅
- [x] Cancel in confirmation dialog does NOT delete task ✅
- [x] Deleted task does not reappear after refresh ✅

**Checkpoint**: User Story 6 complete - users can delete tasks ✅ VERIFIED

---

## Phase 9: User Story 7 - Mark Task Complete (Priority: P2)

**Goal**: Allow users to toggle task completion status

**Independent Test**: Click checkbox on task, verify status toggles and persists

### Implementation for User Story 7

- [x] T059 [US7] Implement PATCH /api/v1/tasks/{task_id}/complete endpoint in phase-2-web/backend/app/api/v1/tasks.py
- [x] T060 [US7] Add completion toggle to TaskItem component in phase-2-web/frontend/components/tasks/TaskItem.tsx
- [x] T061 [US7] Implement toggleComplete Server Action in phase-2-web/frontend/app/actions/tasks.ts

**Acceptance Criteria** (from spec.md):
- [x] Click checkbox toggles pending -> completed ✅
- [x] Click again toggles completed -> pending ✅
- [x] Status persists after page refresh ✅

**Checkpoint**: User Story 7 complete - users can mark tasks complete ✅ VERIFIED

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: UX improvements that affect multiple user stories

### Loading & Feedback

- [x] T062 [P] Add loading spinner to Button component in phase-2-web/frontend/components/ui/Button.tsx
- [x] T063 [P] Add skeleton loader to TaskList component in phase-2-web/frontend/components/ui/Skeleton.tsx
- [x] T064 [P] Create Toast notification component in phase-2-web/frontend/components/ui/Toast.tsx
- [x] T065 Implement toast notifications for CRUD operations in phase-2-web/frontend/app/actions/tasks.ts

### Validation & Error Handling

- [x] T066 [P] Add client-side form validation to RegisterForm in phase-2-web/frontend/components/auth/RegisterForm.tsx
- [x] T067 [P] Add client-side form validation to LoginForm in phase-2-web/frontend/components/auth/LoginForm.tsx
- [x] T068 [P] Add client-side form validation to TaskForm in phase-2-web/frontend/components/tasks/TaskForm.tsx

### Final Integration

- [x] T069 Wire all components to Server Actions in phase-2-web/frontend/app/dashboard/page.tsx
- [x] T070 Add root layout with global styles in phase-2-web/frontend/app/layout.tsx
- [x] T071 Add landing page redirect logic in phase-2-web/frontend/app/page.tsx

---

## Phase 11: Validation & Acceptance

**Purpose**: Verify all acceptance criteria pass

- [x] T072 Run all User Story 1 acceptance scenarios (5 scenarios) ✅ ALL PASS
- [x] T073 Run all User Story 2 acceptance scenarios (5 scenarios) ✅ ALL PASS
- [x] T074 Run all User Story 3 acceptance scenarios (5 scenarios) ✅ ALL PASS
- [x] T075 Run all User Story 4 acceptance scenarios (5 scenarios) ✅ ALL PASS
- [x] T076 Run all User Story 5 acceptance scenarios (4 scenarios) ✅ ALL PASS
- [x] T077 Run all User Story 6 acceptance scenarios (3 scenarios) ✅ ALL PASS
- [x] T078 Run all User Story 7 acceptance scenarios (3 scenarios) ✅ ALL PASS
- [x] T079 Create PHR for Phase 2 implementation in history/prompts/phase-2-web/
- [x] T080 Update root CLAUDE.md with Phase 2 completion status

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) ─────────────────┐
                                 ▼
Phase 2 (Foundational) ──────────┤ BLOCKS all user stories
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│                  User Stories (Parallel OK)                  │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Phase 3: US1 │ Phase 4: US2 │ Phase 5: US3 │ Phase 6: US4   │
│ (Register)   │ (Login)      │ (Add Task)   │ (View Tasks)   │
│ [P1]         │ [P1]         │ [P1]         │ [P1]           │
├──────────────┼──────────────┼──────────────┼────────────────┤
│ Phase 7: US5 │ Phase 8: US6 │ Phase 9: US7 │                │
│ (Update)     │ (Delete)     │ (Complete)   │                │
│ [P2]         │ [P2]         │ [P2]         │                │
└──────────────┴──────────────┴──────────────┴────────────────┘
                                 │
                                 ▼
Phase 10 (Polish) ───────────────┤
                                 ▼
Phase 11 (Validation) ───────────┘
```

### User Story Dependencies

| Story | Dependencies | Can Parallelize With |
|-------|--------------|---------------------|
| US1 (Register) | Phase 2 only | US2, US3, US4 |
| US2 (Login) | Phase 2 only | US1, US3, US4 |
| US3 (Add Task) | Phase 2 only | US1, US2, US4 |
| US4 (View Tasks) | Phase 2 only | US1, US2, US3 |
| US5 (Update) | US4 (TaskItem exists) | US6, US7 |
| US6 (Delete) | US4 (TaskItem exists) | US5, US7 |
| US7 (Complete) | US4 (TaskItem exists) | US5, US6 |

### Parallel Opportunities

**Setup Phase (all parallel)**:
```
T002, T003, T004, T005, T006, T007 → All run simultaneously
```

**Foundational Phase (partial parallel)**:
```
T008, T009 → Parallel (User, Task models)
T013, T014, T016 → Parallel (config, security, exports)
```

**User Story 1 (partial parallel)**:
```
T028, T029, T030 → Parallel (RegisterForm, Button, Input)
```

**User Story 4 (partial parallel)**:
```
T046, T047 → Parallel (TaskList, TaskItem)
```

---

## Implementation Strategy

### MVP First (User Stories 1-4)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: US1 - Registration
4. Complete Phase 4: US2 - Login
5. Complete Phase 5: US3 - Add Task
6. Complete Phase 6: US4 - View Tasks
7. **STOP and VALIDATE**: Test full CRUD flow independently
8. Deploy/demo MVP

### Incremental Delivery

| Milestone | Stories | Deliverable |
|-----------|---------|-------------|
| M1: Foundation | Setup + Foundational | Backend starts, frontend compiles |
| M2: Auth | US1 + US2 | Users can register and login |
| M3: Core CRUD | US3 + US4 | Users can add and view tasks |
| M4: Full CRUD | US5 + US6 + US7 | Complete task management |
| M5: Polish | Phase 10 | Loading states, notifications |
| M6: Release | Phase 11 | Acceptance tests pass |

---

## Summary

| Phase | Tasks | P1 (Critical) | P2 (Important) |
|-------|-------|---------------|----------------|
| 1: Setup | T001-T007 | 7 | 0 |
| 2: Foundational | T008-T026 | 19 | 0 |
| 3: US1 Register | T027-T032 | 6 | 0 |
| 4: US2 Login | T033-T039 | 7 | 0 |
| 5: US3 Add Task | T040-T043 | 4 | 0 |
| 6: US4 View Tasks | T044-T050 | 7 | 0 |
| 7: US5 Update | T051-T054 | 0 | 4 |
| 8: US6 Delete | T055-T058 | 0 | 4 |
| 9: US7 Complete | T059-T061 | 0 | 3 |
| 10: Polish | T062-T071 | 0 | 10 |
| 11: Validation | T072-T080 | 9 | 0 |
| 12: Production Deployment | T081-T089 | 6 | 3 |
| **Total** | **89** | **65** | **24** |

**Critical Path**: T001 → T008 → T011 → T012 → T015 → T017 → T020 → T022 → T027 → T033 → T040 → T044 → T049 → T072

---

## Agent Assignments (per /sp.tasks request)

| Agent | Responsibilities |
|-------|------------------|
| @task-orchestrator | Ensured every task has Definition of Done and Verification |
| @backend-builder | T008-T022 (Models, Services, API) |
| @ux-frontend-developer | T023-T071 (Types, Components, Actions, Pages) |
| @path-warden | Verified all file paths use `phase-2-web/backend/` or `phase-2-web/frontend/` |
| @qa-overseer | T072-T080 (Acceptance testing, PHR, closure) |

---

## Phase 12: Production Deployment 🚀

**Purpose**: Deploy Phase 2 Full-Stack Application to Vercel with Neon DB

**Milestone**: M7 Production

### T081: Create Vercel Configuration for FastAPI Serverless [P1] ✅

**Files**:
- `phase-2-web/backend/vercel.json`
- `phase-2-web/backend/api/index.py`
- `phase-2-web/backend/requirements.txt`

**DoD**:
- [x] vercel.json configured with @vercel/python runtime
- [x] api/index.py exposes FastAPI app as handler
- [x] requirements.txt extracted from pyproject.toml

**Verification**:
```bash
cd phase-2-web/backend
npx vercel deploy
```

---

### T082: Document Environment Variables [P1] ✅

**Files**:
- `phase-2-web/DEPLOYMENT.md`
- `phase-2-web/.env.example`

**DoD**:
- [x] DEPLOYMENT.md lists all required variables
- [x] .env.example updated with Neon DB format
- [x] SSL parameter documented (ssl=require for asyncpg)

**Verification**: Review DEPLOYMENT.md for completeness

---

### T083: Run Alembic Migrations on Neon DB [P1] ✅

**Files**:
- Neon DB schema (remote)

**DoD**:
- [x] `user` table created with correct schema
- [x] `task` table created with user_id foreign key
- [x] SSL connection issue resolved (ssl=require)

**Verification**:
```bash
DATABASE_URL="postgresql+asyncpg://...?ssl=require" uv run alembic upgrade head
```

**Result**: ✅ Tables created successfully

---

### T084: Deploy Backend to Vercel [P1] ✅

**Files**:
- Vercel deployment (remote)

**DoD**:
- [x] Backend deployed to: https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app
- [x] Health endpoint accessible

**Verification**:
```bash
curl https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app/health
```

**Status**: ✅ Deployed (awaiting environment variable configuration)

---

### T085: Deploy Frontend to Vercel [P1] ✅

**Files**:
- Vercel deployment (remote)

**DoD**:
- [x] Frontend deployed to: https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app
- [x] UI renders correctly

**Verification**: Visit URL in browser

**Status**: ✅ Deployed and working

---

### T086: Create PHR for Deployment Session [P1] ✅

**Files**:
- `history/prompts/phase-2-web/PHR-011-vercel-deployment.md`

**DoD**:
- [x] PHR documents Vercel configuration
- [x] Neon DB migration steps recorded
- [x] SSL parameter fix documented

**Verification**: Review PHR-011

---

### T087: Create Deployment Automation Scripts [P2] ✅

**Files**:
- `phase-2-web/vercel-env-setup.txt`
- `phase-2-web/deploy-to-vercel.ps1`
- `phase-2-web/deploy-to-vercel.sh`
- `phase-2-web/QUICK-START.md`
- `phase-2-web/VERCEL-AUTOMATION-GUIDE.md`

**DoD**:
- [x] Cross-platform scripts (PowerShell + Bash)
- [x] Auto-generate JWT secret
- [x] Set environment variables via Vercel CLI
- [x] Deploy both services automatically

**Verification**: Review automation documentation

---

### T088: Set Environment Variables in Vercel Dashboard [P1] ⏳ USER ACTION REQUIRED

**Files**:
- Vercel dashboard (remote)

**DoD**:
- [ ] Backend variables set: DATABASE_URL, SECRET_KEY, CORS_ORIGINS
- [ ] Frontend variables set: NEXT_PUBLIC_API_URL, BACKEND_URL

**Verification**:
1. Go to https://vercel.com/muhammadyaseen200s-projects/backend/settings/environment-variables
2. Add all backend variables from vercel-env-setup.txt
3. Go to https://vercel.com/muhammadyaseen200s-projects/frontend/settings/environment-variables
4. Add all frontend variables from vercel-env-setup.txt

**Alternative**: Use automated script:
```bash
# Windows
.\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://..."

# Linux/macOS
./deploy-to-vercel.sh --database-url "postgresql+asyncpg://..."
```

---

### T089: Redeploy Services with Environment Variables [P2] ⏳ PENDING

**Files**:
- Vercel deployment (remote)

**DoD**:
- [ ] Backend redeployed with environment variables
- [ ] Frontend redeployed with updated backend URL
- [ ] Production deployment fully functional

**Verification**:
```bash
# Redeploy backend
cd phase-2-web/backend && npx vercel --prod

# Redeploy frontend
cd phase-2-web/frontend && npx vercel --prod
```

---

### T090: Test Production Deployment End-to-End [P2] ⏳ PENDING

**Files**:
- Production environment (remote)

**DoD**:
- [ ] Register new user on production frontend
- [ ] Create tasks via production UI
- [ ] Verify all CRUD operations work
- [ ] Check CORS allows frontend to call backend

**Verification**:
1. Visit https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app
2. Register account: test@example.com
3. Create 3 tasks
4. Update, complete, delete tasks
5. Verify no CORS errors in browser console

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-29 | Task Orchestrator | Initial layer-based breakdown |
| 2.0.0 | 2025-12-29 | Task Orchestrator | Reorganized by user story per /sp.tasks command |
| 3.0.0 | 2025-12-31 | Backend Builder + DevOps RAG Engineer | Added Phase 12 Production Deployment (T081-T090) |

---

**End of Task List**
