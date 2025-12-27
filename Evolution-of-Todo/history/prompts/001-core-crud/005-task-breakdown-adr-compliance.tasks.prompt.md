---
id: 005
title: Task Breakdown with ADR Compliance Validation
stage: tasks
date: 2025-12-27
surface: agent
model: claude-opus-4-5-20251101
feature: 001-core-crud
branch: 001-core-crud
user: MuhammadYaseen200
command: /sp.task
labels: ["tasks", "adr-compliance", "verification", "phase1", "implementation-roadmap"]
links:
  spec: specs/001-core-crud/spec.md
  ticket: null
  adr: history/adr/
  pr: null
files:
  - specs/001-core-crud/tasks.md
  - history/prompts/001-core-crud/005-task-breakdown-adr-compliance.tasks.prompt.md
tests:
  - none (task planning phase)
---

## Prompt

/sp.task @agent-task-orchestrator @agent-path-warden @agent-qa-overseer @agent-imperator @agent-loop-controller @task-orchestrator @path-warden @qa-overseer @imperator @loop-controller @qa-check

**Context:**
We have a frozen Architecture Plan (`specs/001-core-crud/plan.md`) and validated ADRs (`history/adr/`) for **Phase I (Greenfield)**. We are ready to define the implementation roadmap.

**Objective:**
Generate a dependency-ordered Task List (`specs/001-core-crud/tasks.md`) that translates the architectural plan into atomic, agent-executable steps.

**Task Breakdown Strategy (Strict SDD):**
1. **Setup:** Project initialization, venv/uv setup, directory creation.
2. **Domain Layer:** Implementation of `Task` model (Data Class).
3. **Data Layer:** Implementation of `TodoRepository` (In-Memory Logic).
4. **Service Layer:** Implementation of `TodoService` (Business Logic & Validation).
5. **Presentation Layer:** Implementation of `main.py` (CLI REPL).
6. **Verification:** Unit tests for Service/Repo and manual verification steps for CLI.

**Constraints & Validation:**
* **Atomic Units:** Each task must be small enough for a single `/sp.implement` cycle.
* **ADR Compliance:** Ensure no tasks violate ADR-003 (e.g., DO NOT create tasks for file I/O or JSON saving).
* **Test-First:** Implementation tasks must include a sub-step to "Verify" or "Test".

## Response snapshot

Enhanced existing tasks.md with comprehensive ADR compliance validation:

**ADR Compliance Matrix Added:**
- ADR-001: Service-Repository Pattern → Tasks follow layered architecture
- ADR-002: Python stdlib CLI only → T-005 uses input()/print()
- ADR-003: No file I/O → Explicit guards on every task

**Task Enhancements:**
1. Added **ADR Compliance** column to summary table
2. Added **Verification Step** with executable bash commands for each task
3. Added **ADR Guards** explicitly stating what NOT to implement
4. Added **ADR-003 Validation Test** in T-007 integration tests
5. Added **ADR-003 Verification** manual step in T-008
6. Added **ADR Violation Detection** section at end

**8 Tasks Validated:**
| ID | Task | ADR Compliance |
|----|------|----------------|
| T-001 | Setup Project Structure | ADR-001 |
| T-002 | Implement Task Model | ADR-001, ADR-003 |
| T-003 | Implement TodoRepository | ADR-001, ADR-003 |
| T-004 | Implement TodoService | ADR-001 |
| T-005 | Implement CLI REPL | ADR-002 |
| T-006 | Write Unit Tests | ADR-001 |
| T-007 | Write Integration Tests | ALL |
| T-008 | Manual Verification | ALL |

**Compliance Status**: ALL TASKS PASS

## Outcome

- Impact: Tasks validated against all 3 ADRs with explicit guards preventing violations
- Tests: none (task planning phase - no code yet)
- Files: 1 file updated (tasks.md with ADR compliance enhancements)
- Next prompts: `/sp.implement` to begin code generation starting with T-001
- Reflection: Added proactive violation detection to prevent ADR-003 breaches during implementation

## Evaluation notes (flywheel)

- Failure modes observed: None - existing tasks already well-structured
- Graders run and results (PASS/FAIL):
  - ADR-001 Compliance: 8/8 PASS (all tasks follow Service-Repository pattern)
  - ADR-002 Compliance: 1/1 PASS (T-005 uses stdlib only)
  - ADR-003 Compliance: 8/8 PASS (no file I/O in any task)
  - Atomic Unit Check: PASS (each task is single /sp.implement cycle)
  - Verification Steps: PASS (all tasks have executable verification)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Execute T-001 and verify uv project setup
