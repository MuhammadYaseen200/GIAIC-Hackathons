---
id: "004"
title: Phase 6 Gold Tasks Generation
stage: tasks
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: m-y-j
command: sp.tasks
labels: ["phase-6","gold","tasks","tdd","agent-team","governance","ceo-briefing","odoo","social-media"]
links:
  spec: specs/010-ceo-briefing-odoo-gold/spec.md
  ticket: null
  adr: history/adr/0016-odoo-api-protocol-selection.md
  pr: null
files:
  - specs/010-ceo-briefing-odoo-gold/tasks.md
tests:
  - Format validation: all 110 tasks follow checkbox + TaskID + [P?] + [USN?] + description + file path format
  - All 8 user stories mapped to phases
  - TDD tasks (RED contract tests) appear before implementation tasks
---

## Prompt

/sp.tasks with user input:
"apply all governance and ai-control
Read project docs and mind map for Gold tier, read Constitution, Specs, Clarify, Plan, adr, requirements, checklists, contracts, and overview files
creat claude agent team instance, specify the to use sub-agents, skills, Context7, and Mcps, divide task among instance and deploye specialist sub-agents and must skills"

## Response snapshot

Generated `specs/010-ceo-briefing-odoo-gold/tasks.md` — 110 tasks (T001–T110) across 10 phases + Polish.

**Governance applied:**
- loop-controller gate checklist added at top
- Agent team assignment defined (Lead + 4 backend-builder teammates)
- Spawn command documented (CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1)
- path-warden + qa-overseer + security-scan checkpoints inline

**8 User Stories mapped to phases:**
| Phase | US | Priority | Tasks |
|-------|----|---------|-|
| Phase 2 (Foundational) | US5 data, US1/US2 blocking | P1 | T010–T020 (11) |
| Phase 3 | US3 Facebook/Instagram | P2 | T021–T028 (8) |
| Phase 4 | US4 Twitter/X | P2 | T029–T035 (7) |
| Phase 5 | US1 Daily Briefing MVP | P1 | T036–T044 (9) |
| Phase 6 | US2 Weekly Audit | P1 | T045–T049 (5) |
| Phase 7 | US5 Odoo integration | P2 | T050–T054 (5) |
| Phase 8 | US6 Email + US7 Calendar | P2/P3 | T055–T060 (6) |
| Phase 9 | US8 Agent Skills | P2 | T061–T072 (12) |
| Phase 10 | Polish + QA | cross-cutting | T073–T110 (38) |

**TDD pattern enforced:**
- T013: Odoo contract tests RED before T015 (server.py)
- T023: Facebook contract tests RED before T024 (server.py)
- T031: Twitter contract tests RED before T032 (server.py)
- T036: Briefing contract tests RED before T039 (ceo_briefing.py)
- T038: run_until_complete unit tests RED before T037 (run_until_complete.py)

**ADR references in tasks:**
- ADR-0016: T011 (Odoo JSON-RPC auth), T012 (client.py)
- ADR-0017: T021-T024 (separate Facebook/Twitter servers)
- ADR-0018: T037 (run_until_complete.py)
- ADR-0019: T039 (draft_briefing with template fallback)

**Parallel opportunities:**
- Phase 3 + Phase 4 run simultaneously (teammate-2)
- T007/T008 in Phase 1 parallel
- T010/T011/T013/T014 in Phase 2 parallel
- US8 skills T062–T072 all in parallel (independent skill files)

**Human blockers documented:**
- T028 live test: HT-014 (Facebook)
- T028 live test: HT-015 (Instagram)
- T035 live test: HT-016 (Twitter/X)
- T039 LLM draft: Anthropic credits

**MVP scope:** Phases 1+2+5 (T001-T020, T036-T044) → US1 daily briefing live at 07:00. Satisfies SC-001, SC-003, SC-005, SC-007, SC-011.

## Outcome

- ✅ Impact: 110 tasks generated, all user stories mapped, TDD enforced, governance applied
- 🧪 Tests: Format validation — all 110 tasks follow strict checklist format; 8 US phases mapped
- 📁 Files: specs/010-ceo-briefing-odoo-gold/tasks.md (new — 110 tasks)
- 🔁 Next prompts: `/sp.implement` — run Phase 1 + Phase 2 + Phase 5 for MVP; then social MCPs after HT credentials
- 🧠 Reflection: US5 (Odoo in daily briefing) is not an independent phase — it's verified through US1 tests. Separating it as Phase 7 clarifies that US5's independent test validates the integration, not duplicates US1.

## Evaluation notes (flywheel)

- Failure modes observed: None — all 8 user stories had clear file path targets; no ambiguous tasks
- Graders run and results (PASS/FAIL): Format validation PASS (all tasks: checkbox + ID + optional P + optional US + description + path); TDD sequence PASS (RED before GREEN on all 5 major modules)
- Prompt variant (if applicable): User added governance/agent team context to standard /sp.tasks
- Next experiment (smallest change to try): Run /sp.implement for Phases 1+2+5 MVP — verify Odoo MCP + daily briefing end-to-end before tackling social MCPs
