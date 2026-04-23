---
id: "006"
title: "Phase 6.5 Tasks Generated"
stage: tasks
date: 2026-04-12
surface: agent
model: claude-sonnet-4-6
feature: full-comms-automation
branch: 011-full-comms-automation
user: m-y-j
command: /sp.tasks
labels: ["tasks","hitl-queue","whatsapp","gmail","linkedin","calendar","social","phase-6.5"]
links:
  spec: specs/011-full-comms-automation/spec.md
  ticket: null
  adr: history/adr/0020-multi-model-routing-strategy.md
  pr: null
files:
  - specs/011-full-comms-automation/tasks.md
tests:
  - tests/unit/test_hitl_queue.py (TDD stub)
  - tests/unit/test_email_classifier.py (TDD stub)
  - tests/unit/test_dm_classifier.py (TDD stub)
---

## Prompt

/sp.tasks

## Response snapshot

Generated `specs/011-full-comms-automation/tasks.md` with 89 tasks across 9 phases:

- Phase 1 (Setup): T001–T005 — dirs, deps, stubs
- Phase 2 (Foundation): T006–T021 — HITL queue SQLite, classifiers, model routing config, rate limiters, TDD tests
- Phase 3 (US1 WhatsApp/P1): T022–T033 — Go bridge extensions, Python wrapper business logic, HITL integration
- Phase 4 (US2 Gmail/P2): T034–T045 — create_draft, classify_inbox, auto-reply, HITL-gated send, gmail_reply_watcher
- Phase 5 (US3 LinkedIn/P3): T046–T057 — profile write, analytics, connections, gated dm_server.py, linkedin_monitor
- Phase 6 (US4 Calendar/P4): T058–T066 — OAuth scope upgrade, create/update/delete events, conflict detection
- Phase 7 (US5 Social/P5): T067–T076 — Facebook comments/DMs, Twitter replies/analytics, spam auto-hide
- Phase 8 (Orchestrator): T077–T081 — HITL section in briefing, cross-platform summary, watcher registration
- Phase 9 (QA): T082–T089 — integration tests, security scan, coverage gate, PII audit

Key architectural decisions applied:
- ADR-0021: All outbound tasks enqueue HITL non-blocking and return immediately
- ADR-0022: Go bridge MCP tools used directly; Python wrapper adds business logic only
- ADR-0023: In-place extension to existing server.py files; dm_server.py for gated LinkedIn DMs

## Outcome

- Impact: 89 immediately executable tasks generated; MVP path clear (Phase 1→2→3); all 5 user stories independently testable
- Tests: TDD tests stub-created for Foundation phase (T018–T020); integration tests in Phase 9 (T082–T083)
- Files: specs/011-full-comms-automation/tasks.md created
- Next prompts: /sp.implement (begin Phase 1 Setup) or human tasks first (OpenRouter key, LinkedIn API application, Calendar OAuth re-auth)
- Reflection: ADR-0022 (Go bridge two-layer architecture) significantly shaped Phase 3 task structure — only 3 Go endpoints needed vs originally estimated 10+. Tasks correctly reflect the bridge-first pattern.

## Evaluation notes (flywheel)

- Failure modes observed: None — all design artifacts were complete and consistent before tasks generation
- Graders run and results: Task format validation — all 89 tasks follow [ID] [P?] [USN?] description+filepath pattern PASS
- Prompt variant: none
- Next experiment: /sp.implement Phase 1 (T001–T005 setup tasks)
