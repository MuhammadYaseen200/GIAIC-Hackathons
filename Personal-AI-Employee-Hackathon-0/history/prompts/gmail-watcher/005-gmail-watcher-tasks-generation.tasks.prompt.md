---
id: 005
title: Gmail Watcher Tasks Generation
stage: tasks
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.tasks
labels: ["tasks", "gmail-watcher", "phase-2", "tdd", "dependency-order"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: history/adr/0001-watcher-base-class-design.md, history/adr/0002-async-integration-pattern-for-sync-sdks.md, history/adr/0003-local-file-based-data-persistence.md, history/adr/0004-keyword-heuristic-email-classification.md
  pr: null
files:
  - specs/005-gmail-watcher/tasks.md
tests:
  - N/A (documentation-only task)
---

## Prompt

you have constitution, spec, adr and plan to generate specs/005-gmail-watcher/tasks.md with dependency-ordered implementation tasks
create claude agent team instance, use skills, sub-agents, mcps, plugins, hooks

Current session: 82% used | Resets in 3 hr 38 min
first let me know if its possible in remaning ?

## Response snapshot

Generated `specs/005-gmail-watcher/tasks.md` with 105 dependency-ordered tasks across 8 phases:

- Phase 1: Setup (5 tasks) -- directory structure, requirements, package init
- Phase 2: Foundational (24 tasks) -- models.py, utils.py, conftest.py with TDD tests
- Phase 3: US2 BaseWatcher (22 tasks) -- lifecycle, retry, state, logging with TDD
- Phase 4: US3 OAuth2 (12 tasks) -- authentication flow with TDD
- Phase 5: US1 Email-to-Vault (24 tasks) -- parse, classify, render, route with TDD (MVP)
- Phase 6: US4 Routing Compliance (4 tasks) -- Ralph Wiggum compatibility verification
- Phase 7: US5 Observability (5 tasks) -- Dataview-parseable logging verification
- Phase 8: Integration & Polish (9 tasks) -- full-cycle tests, coverage validation

Key design decisions:
- US2 (P2 priority) implemented BEFORE US1 (P1 priority) due to architectural dependency (GmailWatcher extends BaseWatcher)
- US3 (OAuth2) implemented before US1 because auth is a prerequisite for email fetching
- 40+ tasks marked [P] for parallel execution
- TDD mandated by Constitution V: tests written first per story
- Session strategy: tasks.md this session, implementation continues next session

## Outcome

- Impact: Complete implementation roadmap for 13 files with 105 ordered tasks
- Tests: N/A (documentation task)
- Files: specs/005-gmail-watcher/tasks.md
- Next prompts: /sp.implement to begin TDD implementation starting Phase 1
- Reflection: User story business priority (P1>P2>P3) differs from implementation order (US2>US3>US1) due to architectural dependencies. Documenting this clearly prevents confusion.

## Evaluation notes (flywheel)

- Failure modes observed: None -- all inputs (spec, plan, ADRs, constitution) were available
- Graders run and results (PASS/FAIL): Format validation PASS (all tasks have checkbox + ID + file path), Clustering PASS (organized by user story), Dependency check PASS (no circular deps)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Track actual implementation time per phase to calibrate future estimates
