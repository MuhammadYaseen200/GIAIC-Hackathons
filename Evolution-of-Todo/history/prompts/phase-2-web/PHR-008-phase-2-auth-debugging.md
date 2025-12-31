---
id: PHR-008
title: Phase 2 Auth Debugging Session
stage: green
date: 2025-12-30
surface: claude-code
model: claude-sonnet-4-5-20250929
feature: phase-2-web
branch: phase-2-recovery
user: PCW
command: /sp.analyze
labels: [debugging, auth, react, cors, sqlite]
links:
  spec: phase-2-web/specs/spec.md
  ticket: null
  adr: ADR-004, ADR-005
  pr: null
files:
  - phase-2-web/frontend/components/auth/RegisterForm.tsx
  - phase-2-web/frontend/components/auth/LoginForm.tsx
  - phase-2-web/backend/app/core/config.py
  - phase-2-web/backend/app/core/database.py
  - phase-2-web/backend/app/main.py
  - phase-2-web/backend/pyproject.toml
  - phase-2-web/backend/.env
  - phase-2-web/frontend/app/icon.svg
tests:
  - manual: Registration form submission
  - manual: Login form submission
  - manual: Dashboard redirect after login
---

## Prompt

```
/sp.analyze

at registration i got this: Unable to connect to the server. Please try again.
and this: favicon.ico:1 Failed to load resource: the server responded with a status of 404 (Not Found)

nextjs giving this: ReactDOM.useFormState has been renamed to React.useActionState.
Please update RegisterForm to use React.useActionState.

Use @agent-ux-frontend-developer @agent-backend-builder @qa-check

**Context:**
We are debugging Phase 2: Authentication.
* Current Directory: phase-2-web/ (Strict Check).
* Issues Identified:
    1. React Breaking Change: useFormState is deprecated in our Next.js version
    2. Connection Failure: "Unable to connect to server". Likely CORS mismatch

**Objective:**
Refactor the Frontend Forms and update Backend CORS to enable successful Registration (T027) and Login (T033).
```

## Response snapshot

### Issues Identified and Fixed

1. **React Hook Deprecation (useFormState → useActionState)**
   - Files: `RegisterForm.tsx`, `LoginForm.tsx`
   - Change: `import { useFormState } from 'react-dom'` → `import { useActionState } from 'react'`
   - Hook signature now returns `[state, formAction, isPending]` - removed need for `useFormStatus`

2. **CORS Configuration (Port 3002 not allowed)**
   - File: `backend/app/core/config.py`
   - Added ports 3000, 3001, 3002 for both localhost and 127.0.0.1

3. **Database Connection (Docker not running)**
   - Issue: `asyncpg.exceptions.InvalidPasswordError` - No PostgreSQL available
   - Solution: Added SQLite fallback for development
   - Files Modified:
     - `database.py`: Added `_is_sqlite_url()` and `_create_engine_for_url()` for dual-driver support
     - `pyproject.toml`: Added `aiosqlite>=0.19.0`
     - `main.py`: Added `lifespan` context manager to auto-create tables on startup
     - Created `.env` with SQLite configuration

4. **Missing Favicon**
   - Created `frontend/app/icon.svg` with checkmark icon

### Verification Results

| Test | Result |
|------|--------|
| Backend Health (`/health`) | `{"status":"healthy"}` |
| Registration Form | Account created successfully |
| Login Form | Redirected to /dashboard (404 expected - not implemented yet) |
| httpOnly Cookie | Set correctly per ADR-004 |

## Outcome

- Impact: Authentication flow fully functional (US1 + US2 complete)
- Tests: Manual verification passed for register/login
- Files: 8 files modified/created
- Next prompts: `/sp.implement` for User Story 3 (Dashboard/Task CRUD)
- Reflection: SQLite fallback significantly improves DX when Docker unavailable

## Evaluation notes (flywheel)

- Failure modes observed: React 19 breaking changes in Next.js 15+; asyncpg requires PostgreSQL
- Graders run and results (PASS/FAIL): Manual Chrome DevTools verification - PASS
- Prompt variant (if applicable): Multi-agent orchestration with @backend-builder and @ux-frontend-developer
- Next experiment: Implement dashboard page to complete User Story 3
