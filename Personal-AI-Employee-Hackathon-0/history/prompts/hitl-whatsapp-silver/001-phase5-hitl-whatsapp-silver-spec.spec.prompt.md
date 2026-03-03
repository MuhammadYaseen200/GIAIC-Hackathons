---
id: "001"
title: Phase 5 HITL WhatsApp Silver Spec
stage: spec
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 008-hitl-whatsapp-silver
user: MuhammadYaseen200
command: /sp.specify
labels: ["phase-5","whatsapp","hitl","calendar","silver-tier","spec"]
links:
  spec: Personal-AI-Employee-Hackathon-0/specs/008-hitl-whatsapp-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-hitl-whatsapp-silver/spec.md
  - specs/008-hitl-whatsapp-silver/checklists/requirements.md
  - ai-control/HUMAN-TASKS.md
  - history/prompts/hitl-whatsapp-silver/001-phase5-hitl-whatsapp-silver-spec.spec.prompt.md
tests:
  - "none (spec phase)"
---

## Prompt

Phase 5: HITL + WhatsApp Silver tier — Build a WhatsApp watcher reads incoming messages and writes them to
  vault/Needs_Action/. Build HITL approval workflow: when orchestrator drafts a reply it writes to
  vault/Pending_Approval/, then sends a WhatsApp notification to me asking approve/reject, waits for my WhatsApp reply,
  and if approved sends the email via gmail_mcp. Also integrate Google Calendar MCP for context.
- Use pywa for WhatsApp, context7 for documentation

create an agent team instance and divide tasks upon them too

## Response snapshot

**v2.0 — Full governance enrichment applied.**

Created `008-hitl-whatsapp-silver` branch and generated `specs/008-hitl-whatsapp-silver/spec.md` (v2.0.0) with complete governance, RI, agent team, and SWARM plan.

Spec covers:
- **US1 (P1)**: WhatsApp message ingestion → vault/Needs_Action/ within 30s
- **US2 (P1)**: HITL approval workflow: vault/Pending_Approval/ → WhatsApp notify → approve/reject → Gmail MCP send
- **US3 (P2)**: Google Calendar MCP context for scheduling-related email drafts
- **US4 (P3)**: WhatsApp as a full triage channel (bonus)

30 functional requirements (FR-001–FR-030), 8 measurable success criteria (SC-001–SC-008).

**Governance enrichment applied**:
- Governance Alignment table (AGENTS.md, LOOP.md, MCP.md, SWARM.md, SKILLS.md, HUMAN-TASKS.md)
- Agent Team Instance with 7 agents + SWARM Fan-Out execution plan
- Phase 5 Entry Criteria (E1–E6) + Exit Criteria (X1–X10)
- Reusable Intelligence table: BaseWatcher, FastMCP, MCPClient, atomic_write, ADR-0001/0005/0007/0008/0009
- Constitution Compliance Check (all 10 principles)
- Human Tasks HT-011 (Calendar OAuth) + HT-012 (pywa Cloud API) added to HUMAN-TASKS.md
- Two ADR suggestions: HITL state machine + WhatsApp backend selection
- MCP Servers table + Skills & Hooks table

**RI sources consulted**: constitution.md, specs/007 spec+plan+data-model, ADR-0001/0005/0007/0008/0009, base_watcher.py, orchestrator.py, MCP.md, LOOP.md, AGENTS.md, SWARM.md, HUMAN-TASKS.md, pywa docs (WebSearch), Google Calendar API docs (WebSearch).

Checklist updated with v2.0 governance validation section: all items PASS.

## Outcome

- ✅ Impact: Phase 5 spec v2.0 fully drafted with governance, RI, agent team, SWARM, Constitution compliance check
- 🧪 Tests: None (spec phase)
- 📁 Files: specs/008-hitl-whatsapp-silver/spec.md (v2.0.0), checklists/requirements.md (v2.0), ai-control/HUMAN-TASKS.md (HT-011/HT-012 added)
- 🔁 Next prompts: /sp.clarify (optional) → /sp.plan → /sp.tasks → /sp.implement
- 🧠 Reflection: Go bridge (HT-004 DONE) removes the Meta Developer Account blocker for core testing; pywa Cloud API (HT-012) can be deferred. Calendar OAuth (HT-011) is needed before Calendar MCP live run.

## Evaluation notes (flywheel)

- Failure modes observed: spec created at wrong parent dir (/mnt/e/M.Y/GIAIC-Hackathons instead of project root) — fixed with mv; fetching-library-docs skill script not found at expected path — worked around with WebSearch
- Graders run and results (PASS/FAIL): checklist all-PASS (both content quality + governance validation sections)
- Prompt variant (if applicable): user requested full governance enrichment after initial v1.0 was generated without specialized agents
- Next experiment (smallest change to try): /sp.clarify to confirm HITL timeout behavior (24h vs 48h) and draft ID format before /sp.plan
