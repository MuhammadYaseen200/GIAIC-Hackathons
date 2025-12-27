---
id: 004
title: Phase I Architecture Decision Records
stage: plan
date: 2025-12-27
surface: agent
model: claude-opus-4-5-20251101
feature: 001-core-crud
branch: 001-core-crud
user: MuhammadYaseen200
command: /sp.adr
labels: ["adr", "architecture", "decisions", "phase1", "documentation"]
links:
  spec: specs/001-core-crud/spec.md
  ticket: null
  adr: history/adr/
  pr: null
files:
  - history/adr/ADR-001-service-repository-pattern.md
  - history/adr/ADR-002-cli-standard-library-repl.md
  - history/adr/ADR-003-volatile-in-memory-persistence.md
  - specs/overview.md
  - history/prompts/001-core-crud/004-architecture-decision-records.plan.prompt.md
tests:
  - none (documentation phase)
---

## Prompt

/sp.adr @lead-architect @qa-overseer @imperator @path-warden @loop-controller

**Context:**
We have completed the architecture plan (`specs/001-core-crud/plan.md`) for **Phase I**. Before implementation, we must freeze our design decisions to ensure the "Brownfield Evolution" strategy is safe.

**Objective:**
Review the Plan and generate **Architecture Decision Records (ADRs)** in `history/adr/`.

**Decisions to Document (Phase I):**
1. **ADR-001: Service-Repository Pattern for In-Memory App**
   * *Context:* Why complicate a simple script with layers?
   * *Decision:* To decouple business logic from storage, allowing seamless swap to `SQLModel` in Phase II without rewriting the core logic.
   * *Status:* Accepted.

2. **ADR-002: Typer vs. Cmd Module for CLI**
   * *Context:* We need a robust but simple CLI.
   * *Decision:* Use Python standard library (input() + REPL loop) - no external dependencies per Constitution constraints.

3. **ADR-003: Volatile Data Persistence**
   * *Context:* How to handle data between runs?
   * *Decision:* Explicit acceptance of data loss on exit (In-Memory only) to satisfy Phase I constraints, with no file I/O (JSON/CSV) allowed to prevent scope creep.

## Response snapshot

Created 3 Architecture Decision Records documenting significant Phase I decisions:

**ADR-001: Service-Repository Pattern for In-Memory App**
- Context: Whether to use abstraction layers for simple in-memory app
- Decision: Implement layered architecture (Model → Repository → Service → CLI)
- Rationale: Enables Phase II migration (swap MemoryRepo → SQLModelRepo)
- Consequences: Added complexity justified by evolution path
- Alternatives rejected: Direct dict access, Active Record, Repository-only

**ADR-002: Python Standard Library REPL for CLI**
- Context: CLI framework selection with zero external dependencies
- Decision: Use input() + while True loop for menu-driven REPL
- Rationale: Constitution mandates no external deps for Phase I runtime
- Consequences: No type hints in CLI, but full control and portability
- Alternatives rejected: typer (external dep), click (external dep), cmd module (overkill), argparse (wrong pattern for REPL)

**ADR-003: Volatile In-Memory Persistence (No File I/O)**
- Context: Whether to persist data between runs
- Decision: Explicitly accept data loss on exit - no JSON, CSV, or SQLite
- Rationale: Prevents scope creep, no legacy migration burden for Phase II
- Consequences: Users may expect persistence, but focus is CRUD logic validation
- Alternatives rejected: JSON file, SQLite, pickle, CSV export

Updated `specs/overview.md` with ADR reference table.

## Outcome

- Impact: Design decisions frozen before implementation, enabling safe Brownfield Evolution
- Tests: none (documentation phase - no code yet)
- Files: 3 ADR files created, 1 file updated (overview.md)
- Next prompts: `/sp.implement` to begin code generation
- Reflection: All 3 decisions passed significance test (impact + tradeoffs + cross-cutting). Service-Repository is the key decision enabling Phase II evolution.

## Evaluation notes (flywheel)

- Failure modes observed: None - all decisions clustered appropriately
- Graders run and results (PASS/FAIL):
  - Significance Test: 3/3 PASS (all decisions have impact, alternatives, cross-cutting scope)
  - Clustering Check: PASS (no over-granular ADRs)
  - Alternatives Listed: PASS (all ADRs list 3+ alternatives with rejection reasons)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Execute T-001 to validate project structure setup
