---
id: 005
title: LinkedIn Cron Silver Tasks Generation
stage: tasks
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: owner
command: /sp.tasks
labels: [tasks,linkedin,cron,mcp,hitl,silver-tier,phase-5-5,tdd]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: specs/009-linkedin-cron-silver/tasks.md
  adr: null
  pr: null
files:
  - specs/009-linkedin-cron-silver/tasks.md
tests:
  - All 35 tasks follow checklist format (checkbox, ID, [P?], [Story?], description + file path)
  - All 10 SC mapped to at least one task checkpoint
  - Contract tests written before implementation tasks (Red-Green order)
---

## Prompt

/sp.tasks

## Response snapshot

Generated specs/009-linkedin-cron-silver/tasks.md with 35 tasks across 6 phases:

Phase 1 Setup (T001-T004): directory structure, .gitignore, dependencies, vault/Config/
Phase 2 Foundational (T005-T008): models.py, auth.py, client.py, linkedin_auth.py
Phase 3 US1/P1 (T009-T018): contract tests, server.py, linkedin_poster.py full HITL workflow, --draft CLI
Phase 4 US2+US3/P2 (T019-T028): topic file, --auto mode, rate limit, cron scripts, lock file, orchestrator wiring
Phase 5 US4/P3 (T029-T031): vault classifier routing (type=linkedin_post + #linkedin tag)
Phase 6 Polish (T032-T035): MCP registry, security scan, coverage gate, overview.md update

MVP scope: T001-T018 (Phases 1-3). All 10 SC covered. HT-013b (run linkedin_auth.py) flagged in Notes.

## Outcome

- ✅ Impact: 35 executable tasks ready for /sp.implement; MVP (T001-T018) delivers SC-001/002/003/004 fully; cron (T019-T028) delivers SC-005/006/007
- 🧪 Tests: T009/T010 contract+unit tests before implementation (Red-Green); T023 bash smoke tests; T034 coverage gate (>80%)
- 📁 Files: specs/009-linkedin-cron-silver/tasks.md
- 🔁 Next prompts: /sp.implement (execute T001-T035 in order)
- 🧠 Reflection: US2 (daily auto-draft) and US3 (cron scripts) are cleanly separable — US3 needs only Foundational, not US1. This enables parallel implementation by two agents.

## Evaluation notes (flywheel)

- Failure modes observed: None — all design artifacts were complete, tasks generated cleanly
- Graders run and results (PASS/FAIL): Format validation PASS (all 35 tasks: checkbox + ID + [P?] + [Story?] + file path)
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add explicit "FAIL before implement" marker next to T009/T010 to enforce Red-Green cycle at task level
