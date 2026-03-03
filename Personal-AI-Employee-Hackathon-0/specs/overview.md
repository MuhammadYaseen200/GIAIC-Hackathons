# H0 Phase Overview

## Phase Tracker

| Phase | Name | Status | Entry Criteria | Exit Criteria |
|-------|------|--------|---------------|--------------|
| 0 | Foundation & Governance | COMPLETE | Project created | Constitution ratified, ai-control/ complete, directory structure created |
| 1 | Obsidian Vault | COMPLETE | Phase 0 complete + HT-001 done | Dashboard.md functional, templates created, Dataview queries working |
| 2 | First Watcher - Bronze | COMPLETE | Phase 1 complete + HT-002 done | Gmail watcher reading emails, writing to Needs_Action/ — exited 2026-02-20 |
| 3 | Claude Reasoning Loop | COMPLETE | Phase 2 complete | Ralph Wiggum loop processing Needs_Action/ items autonomously — exited 2026-02-23 |
| 4 | MCP Integration | COMPLETE | Phase 3 complete | Gmail MCP + Obsidian MCP live, MCPClient fallback protocol, orchestrator MCP-first — exited 2026-02-25 |
| 5 | HITL + WhatsApp - Silver | IN_PROGRESS | Phase 4 complete + HT-004 done | Approval workflow functional, WhatsApp watcher running |
| 6 | CEO Briefing + Odoo - Gold | NOT_STARTED | Phase 5 complete + HT-006/007 done | Daily briefing generated, Odoo integration working |
| 7 | Always-On Cloud - Platinum | NOT_STARTED | Phase 6 complete + HT-008 done | System deployed to Oracle VM, running 24/7 |
| 8 | Polish, Testing & Demo | NOT_STARTED | Phase 7 complete | All E2E tests pass, demo rehearsed, README polished |

## Current Focus

**Phase 5: HITL + WhatsApp — Silver** | Branch: `008-hitl-whatsapp-silver` | Started: 2026-03-03

### SDD Cycle Status
- [x] spec.md — Complete (v2.0, enriched 2026-03-02)
- [x] Clarification — Complete (5 Q&A, 2026-03-02)
- [x] plan.md — Complete (8 phases A–H, 2026-03-02)
- [x] ADRs 0010–0013 — Complete (Privacy Gate, HITL State Machine, WhatsApp Backend, Tiered Classifier)
- [x] tasks.md — Complete (32 tasks, T001–T032, 2026-03-03)
- [ ] Implementation — NEXT (T001–T032, see specs/008-hitl-whatsapp-silver/tasks.md)

### Phase 5 Deliverables
- [ ] T001–T004: Setup (vault/Rejected/, httpx, .env, __init__.py)
- [ ] T005–T008: Privacy Gate (`watchers/privacy_gate.py` + Gmail retrofit)
- [ ] T009–T015: WhatsApp Watcher + MCP (US1 — MVP)
- [ ] T016–T020: HITL Manager + orchestrator wiring (US2)
- [ ] T021–T027: Calendar MCP + orchestrator tiered classifier (US3)
- [ ] T028–T032: Polish, QA gate, smoke tests

### Human Tasks Pending
- [ ] HT-011: Run `python3 scripts/calendar_auth.py` to generate `calendar_token.json` (IN_PROGRESS)
- [ ] HT-012: Configure pywa Cloud API (DEFERRED — Go bridge primary)
