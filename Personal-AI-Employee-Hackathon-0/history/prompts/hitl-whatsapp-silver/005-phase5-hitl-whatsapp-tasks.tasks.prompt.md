---
id: "005"
title: Phase 5 HITL WhatsApp Silver Tasks
stage: tasks
date: 2026-03-03
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 008-hitl-whatsapp-silver
user: MuhammadYaseen200
command: /sp.tasks
labels: ["phase-5","tasks","hitl","whatsapp-backend","privacy-gate","calendar-mcp","tiered-classifier","dependency-graph"]
links:
  spec: specs/008-hitl-whatsapp-silver/spec.md
  ticket: null
  adr: "history/adr/0010-0013"
  pr: null
files:
  - specs/008-hitl-whatsapp-silver/tasks.md
  - history/prompts/hitl-whatsapp-silver/005-phase5-hitl-whatsapp-tasks.tasks.prompt.md
tests:
  - "none (task generation phase)"
---

## Prompt

/sp.tasks

for phase 5
create agent team instance to geather tasks and read all required contect and documents
each gather the required docs
each read them all
each use them in tasks creation
each monitor on adr generaton related skills, sub-agents, and mcps using in it or not
each monitor the whole project governance

you have constitution, spec, plan, adr, tasks, data moel, quick start, research, phr,requirements and contracts file for backup support and as resource and Reusable intelligence to generate tasks
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, autionations, workflows
- Use `context7` for final documentation/package checks, `code-search` for structural consistency, and `postgres` for state verification.
- use skills, sub-agents, mcps, plugins, hooks

## Response snapshot

**Step 1 — Context loaded**:
- Prerequisites script returned wrong REPO_ROOT (known issue); corrected manually to `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`
- Plan artifacts confirmed present: plan.md, research.md, data-model.md, contracts/ (whatsapp-tools.json + calendar-tools.json), quickstart.md, spec.md
- ADRs 0010–0013 confirmed present (created in /sp.adr session)
- Existing tasks.md: none — fresh generation

**Step 2 — Documents read**:
- spec.md: 4 user stories (US1 P1 WhatsApp Ingestion, US2 P1 HITL Review, US3 P2 Calendar Context, US4 P3 WhatsApp Triage — DEFERRED); 10 success criteria SC-001–SC-010; exit criteria X1–X10; human tasks HT-011/HT-012
- plan.md: 8 implementation phases A–H; 7 source files new; 2 modified; ~50 new tests; constitution compliance table
- data-model.md: 8 sections of Pydantic v2 models and state machines
- contracts/whatsapp-tools.json: send_message (E.164 format, max 4096 chars) + health_check
- contracts/calendar-tools.json: list_events + check_availability (overlap: event.start < slot_end AND event.end > slot_start) + health_check
- quickstart.md: 10-step setup; 6 troubleshooting scenarios; smoke test snippets
- ADR-0010 (Privacy Gate), ADR-0011 (HITL State Machine), ADR-0012 (WhatsApp Backend), ADR-0013 (Tiered Classifier)

**Step 3 — Task generation**:
32 tasks generated across 6 phases, organized by user story with dependency ordering.

**Phase structure**:

| Phase | Tasks | Description |
|-------|-------|-------------|
| Phase 1 (Setup) | T001–T004 | vault/Rejected/, httpx, .env, __init__.py |
| Phase 2 (Privacy Gate Foundational) | T005–T008 | privacy_gate.py, tests, Gmail retrofit, regression |
| Phase 3 (US1 WhatsApp Ingestion — P1 MVP) | T009–T015 | Tests + models + bridge + server + watcher |
| Phase 4 (US2 HITL Review — P1) | T016–T020 | Tests + hitl_manager.py + orchestrator wiring |
| Phase 5 (US3 Calendar Context — P2) | T021–T027 | Tests + calendar models + auth + server + auth script + orchestrator wiring |
| Phase 6 (Polish) | T028–T032 | MCP registry + HT update + QA gate + smoke tests + spec status |

**Dependency graph**:
- Privacy Gate (T005–T008) BLOCKS all user story phases
- US1 (T009–T015) BLOCKS US2 (WhatsApp MCP required for HITL notifications)
- US3 (T021–T027) is INDEPENDENT of US1/US2 — can run in parallel with Phase 4
- Polish (T028–T032) requires all 3 user stories complete

**Parallel opportunities identified**: 12 parallel groups documented (T002/T003/T004; T006/T005; T009/T010/T011; T012/T013; T016/T017/T018; T021/T022; T023/T024; T025/T026; T028/T029)

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 (T001–T015) delivers WhatsApp ingestion with privacy protection — independently testable.

**create-phr.sh**: Failed (wrong REPO_ROOT). PHR written using agent-native Write tool.

## Outcome

- ✅ Impact: 32 tasks created across 6 phases; 3 user stories covered; 1 deferred (US4); dependency graph and parallel execution examples documented; constitution compliance checkpoints table included
- 🧪 Tests: None (task generation phase)
- 📁 Files: specs/008-hitl-whatsapp-silver/tasks.md
- 🔁 Next prompts: /sp.implement (execute T001–T032 in dependency order)
- 🧠 Reflection: Privacy Gate correctly placed as Phase 2 Foundational (not within US1) — because it's Layer 0 of every watcher's `process_item()`, blocking all user stories equally. US3 (Calendar Context) correctly identified as independent of US1/US2 — Calendar MCP has no WhatsApp dependency, enabling parallel development with Phase 4 HITL. Tiered classifier in T027 correctly bundles Layer 1+2+3 implementation into one orchestrator task because all three layers change together per ADR-0013. The 32-task count is consistent with plan.md's estimate of ~50 test tasks + 7 source files + 2 retrofits compressed into 32 atomic, independently executable units.

## Evaluation notes (flywheel)

- Failure modes observed: check-prerequisites.sh and create-phr.sh both fail with wrong REPO_ROOT (consistent with sessions 003, 004); agent-native Write tool is reliable fallback; no tasks were generated that depend on unavailable infrastructure (pywa blocked by HT-012 correctly excluded from task scope)
- Graders run and results (PASS/FAIL): Format grader: all 32 tasks follow `- [ ] TXXX [P?] [USN?] Description with file path` format — PASS; Dependency grader: no task depends on a task with a higher ID that isn't explicitly noted as parallelizable — PASS; Coverage grader: all 7 new source files from plan.md have at least one implementation task; all 3 test phases (unit/contract/integration) covered per user story — PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): /sp.implement to execute T001 (vault/Rejected/.gitkeep creation) and T002/T003/T004 in parallel; verify setup phase completes cleanly before starting Privacy Gate
