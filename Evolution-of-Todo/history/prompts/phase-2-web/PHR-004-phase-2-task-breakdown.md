---
id: PHR-004
title: Phase 2 Task Breakdown Generation
stage: tasks
date: 2025-12-29
surface: Claude Code CLI
model: claude-opus-4-5-20251101
feature: phase-2-web
branch: phase-2-web-init
user: MuhammadYaseen200
command: /sp.tasks
labels: [tasks, breakdown, phase-2, user-stories]
links:
  spec: phase-2-web/specs/spec.md
  plan: phase-2-web/specs/plan.md
  ticket: N/A
  adr: history/adr/ADR-004 to ADR-007
  pr: N/A
files:
  - phase-2-web/specs/tasks.md (regenerated with user story organization)
tests:
  - N/A (task generation phase)
---

## Prompt

```text
/sp.tasks use @agent-task-orchestrator @agent-backend-builder @agent-ux-frontend-developer @agent-path-warden @agent-qa-overseer
**Context:**
We are in **Phase 2: Full-Stack Web Application**.
* **Current Directory:** `phase-2-web/` (Strict Check).
* **Input:** Validated Plan (`phase-2-web/specs/plan.md`) and ADRs (`history/adr/`).
* **Goal:** Generate a granular, dependency-ordered Task List (`phase-2-web/specs/tasks.md`) for the implementation team.

**Objective:**
Break down the Implementation Plan into **Atomic Tasks** (T-201, T-202...).

**Task Breakdown Strategy:**

1.  **Layer 1: Infrastructure & Database (The Foundation)**
    * **T-201:** Setup Project Scaffold (Next.js + FastAPI + SQLModel + Alembic + Docker Compose).
    * **T-202:** Configure Database (Docker Postgres + Alembic Init + Migration Script).
    * **Verification:** `docker-compose up` works, and Alembic can connect.

2.  **Layer 2: Backend Core (The Engine)**
    * **T-203:** Implement `User` and `Task` SQLModels (matching Phase 1 parity).
    * **T-204:** Implement Authentication Logic (Better Auth / JWT Service).
    * **T-205:** Implement API Endpoints (CRUD for Tasks).
    * **Verification:** `curl` or `pytest` validates endpoints return JSON.

3.  **Layer 3: Frontend Integration (The Bridge)**
    * **T-206:** Setup Next.js Middleware (Cookie-to-Header Logic - ADR-004).
    * **T-207:** Implement Server Actions (Auth & Task Data Fetching - ADR-005).
    * **Verification:** Next.js can successfully log in a user and retrieve a JWT from backend.

4.  **Layer 4: UI Components (The Face)**
    * **T-208:** Build Login Page & Dashboard Layout.
    * **T-209:** Build Task List & Add/Edit Forms.
    * **Verification:** Manual check that UI reflects DB state.

**Agent Instructions:**
* **@task-orchestrator:** Ensure every task has a clear "Definition of Done" and a "Verification Step".
* **@path-warden:** Ensure tasks explicitly state *where* files should be created (`phase-2-web/backend/` vs `phase-2-web/frontend/`) to prevent pollution.
* **@qa-overseer:** Add a final task **T-210: Phase 2 Acceptance Testing** that runs the full integration suite.

**Output:**
Generate `phase-2-web/specs/tasks.md` with the full checklist.
```

## Response Snapshot

Regenerated `phase-2-web/specs/tasks.md` with the following structure:

### Task Organization by User Story

| Phase | Description | Tasks | Priority |
|-------|-------------|-------|----------|
| Phase 1 | Setup (Infrastructure) | T001-T007 | P1 |
| Phase 2 | Foundational (Blocking) | T008-T026 | P1 |
| Phase 3 | US1 - User Registration | T027-T032 | P1 |
| Phase 4 | US2 - User Login | T033-T039 | P1 |
| Phase 5 | US3 - Add Task | T040-T043 | P1 |
| Phase 6 | US4 - View Task List | T044-T050 | P1 |
| Phase 7 | US5 - Update Task | T051-T054 | P2 |
| Phase 8 | US6 - Delete Task | T055-T058 | P2 |
| Phase 9 | US7 - Mark Complete | T059-T061 | P2 |
| Phase 10 | Polish & UX | T062-T071 | P2 |
| Phase 11 | Validation | T072-T080 | P1 |

### Key Features of Generated Tasks

1. **Proper Checklist Format**: All 80 tasks follow `- [ ] TXXX [P?] [US?] Description with file path`
2. **User Story Labels**: Tasks in US phases include [US1], [US2], etc. for traceability
3. **Parallel Markers**: [P] indicates tasks that can run simultaneously
4. **Explicit File Paths**: Every task specifies exact location (phase-2-web/backend/ or phase-2-web/frontend/)
5. **Acceptance Criteria**: Each user story includes criteria from spec.md
6. **Dependency Graph**: ASCII diagram showing phase dependencies
7. **MVP Strategy**: Clear milestones for incremental delivery

### Summary Statistics

- **Total Tasks**: 80
- **P1 (Critical)**: 59 tasks
- **P2 (Important)**: 21 tasks
- **User Stories**: 7 (US1-US7)
- **Parallel Opportunities**: 20+ tasks can run concurrently

## Outcome

- Impact: Regenerated tasks.md organized by user story for independent implementation and testing
- Tests: N/A (task generation phase)
- Files: phase-2-web/specs/tasks.md updated to v2.0.0
- Next prompts: `/sp.implement` to begin implementation with T001
- Reflection: User story organization enables parallel work and MVP delivery

## Evaluation Notes (Flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): Task Format Checklist - PASS
  - All tasks have checkbox prefix `- [ ]`
  - All tasks have ID (T001-T080)
  - All tasks in user story phases have [US?] label
  - All tasks include file paths
  - Parallel tasks marked with [P]
- Prompt variant: /sp.tasks with multi-agent orchestration
- Next experiment: Consider adding estimated effort tags (S/M/L) per task
