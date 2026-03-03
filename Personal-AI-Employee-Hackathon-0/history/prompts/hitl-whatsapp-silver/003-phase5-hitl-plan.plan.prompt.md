---
id: "003"
title: Phase 5 HITL WhatsApp Plan
stage: plan
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 008-hitl-whatsapp-silver
user: MuhammadYaseen200
command: /sp.plan
labels: ["phase-5","whatsapp","hitl","calendar","privacy-gate","plan"]
links:
  spec: specs/008-hitl-whatsapp-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-hitl-whatsapp-silver/plan.md
  - specs/008-hitl-whatsapp-silver/research.md
  - specs/008-hitl-whatsapp-silver/data-model.md
  - specs/008-hitl-whatsapp-silver/quickstart.md
  - specs/008-hitl-whatsapp-silver/contracts/whatsapp-tools.json
  - specs/008-hitl-whatsapp-silver/contracts/calendar-tools.json
  - history/prompts/hitl-whatsapp-silver/003-phase5-hitl-plan.plan.prompt.md
tests:
  - "none (plan phase)"
---

## Prompt

/sp.plan

create agent team instance to geather and read all required contect and documents
each gather the required docs
each read them all
each use them in plan creation
each monitor on plan generaton related skills, sub-agents, and mcps using in it or not
each monitor the whole project governance
you have constitution, spec, plan, adr, tasks, data moel, quick start, research, phr,requirements and contracts file for backup support and as resource and Reusable intelligence to create
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws,   loops,   autionations, workflows
- Use `context7` for final documentation/package checks, `code-search` for structural consistency, and `postgres` for state verification.
- use skills, sub-agents, mcps, plugins, hooks

## Response snapshot

Generated all Phase 5 plan artifacts using full governance protocol:

**Context gathered** (RI sources):
- spec.md v2.0 (41 FRs, 10 SCs, 5 clarifications + Privacy Gate)
- Phase 4 plan.md + data-model.md (pattern reference)
- orchestrator/mcp_client.py (full code — subprocess JSON-RPC, call_tool, fallback protocol)
- vault/ directory structure (Rejected/ does NOT exist — created in plan)
- .specify/memory/constitution.md (all 10 principles)
- ai-control/ governance files (AGENTS.md, LOOP.md, MCP.md, SWARM.md)
- watchers/ and orchestrator/ module structure

**Artifacts generated**:

1. **research.md** — 8 key decisions:
   - Decision 1: Go bridge (primary) vs pywa (fallback) — HT-004 already done
   - Decision 2: File-system HITL state machine (vault/ as state store)
   - Decision 3: Privacy Gate as pure function module (`watchers/privacy_gate.py`)
   - Decision 4: Batch HITL notification format (single message, max 5 drafts, priority tags)
   - Decision 5: Tiered email classifier (Layer 1 spam → Layer 2 keyword → Layer 3 LLM)
   - Decision 6: Calendar MCP (read-only, 7-day default, same credentials.json as Gmail)
   - Decision 7: vault/Rejected/ directory creation in Phase 5 setup
   - Decision 8: Orchestrator wiring (new MCPClient instances + HITLManager as orchestrator attributes)

2. **data-model.md** — all Pydantic v2 models + state machines:
   - PrivacyGateResult, PrivacyLogEntry
   - RawWhatsAppMessage, WhatsApp vault note schema
   - SendMessageInput/Result, HealthCheckResult (WhatsApp MCP)
   - PendingDraft, HITLDecision, HITLManager class signature
   - Pending_Approval vault note schema (YAML frontmatter)
   - ListEventsInput, CheckAvailabilityInput, CalendarEvent, EventList, AvailabilityResult (Calendar MCP)
   - PriorityClassification, CalendarContext (orchestrator)
   - State transition diagrams: HITL draft machine, WhatsApp message processing, email priority classification
   - Vault directory structure Phase 5 additions

3. **contracts/whatsapp-tools.json** — 2 tools: send_message + health_check with full JSON schema
4. **contracts/calendar-tools.json** — 3 tools: list_events + check_availability + health_check with full JSON schema

5. **quickstart.md** — 10-step setup guide:
   - Prerequisites verification
   - New dependency installation (httpx)
   - .env update (WHATSAPP_* + CALENDAR_* + HITL_* vars)
   - Google Calendar OAuth (HT-011) instructions
   - vault/Rejected/ setup
   - Unit → contract → integration test sequence
   - Smoke tests for WhatsApp MCP + Calendar MCP
   - Troubleshooting for 6 common failure modes
   - Full env variable reference table

6. **plan.md** — main implementation plan:
   - Technical Context table (all 8 fields)
   - Constitution Check (all 10 principles PASS)
   - Project Structure (docs tree + source code tree): 5 new files, 2 modified, ~50 new tests
   - Complexity Tracking (3 justified additions)
   - 8 Implementation Phases (A-H): Setup+Privacy Gate, WhatsApp Watcher, WhatsApp MCP, HITL Manager, Calendar MCP, Orchestrator Integration, MCP Registry Update, Housekeeping+QA Gate
   - Risk Analysis (7 risks with mitigations)
   - Acceptance Criteria checklist (SC-001 through SC-010)
   - Related Artifacts table

**Governance applied**:
- loop-controller gate: Phase 4 exit criteria verified before planning
- Constitution Check: all 10 principles PASS
- RI Applied: BaseWatcher, MCPClient, FastMCP+Pydantic v2, atomic_write, ADR-0001/0005/0007/0008/0009
- SWARM Fan-Out plan from spec.md followed (Parallel A → Sequential → Parallel B → Sequential)

## Outcome

- ✅ Impact: All 6 Phase 5 plan artifacts generated (research.md, data-model.md, contracts/whatsapp-tools.json, contracts/calendar-tools.json, quickstart.md, plan.md); full governance applied; Constitution Check all PASS
- 🧪 Tests: None (plan phase)
- 📁 Files: specs/008-hitl-whatsapp-silver/research.md, specs/008-hitl-whatsapp-silver/data-model.md, specs/008-hitl-whatsapp-silver/contracts/whatsapp-tools.json, specs/008-hitl-whatsapp-silver/contracts/calendar-tools.json, specs/008-hitl-whatsapp-silver/quickstart.md, specs/008-hitl-whatsapp-silver/plan.md
- 🔁 Next prompts: /sp.tasks
- 🧠 Reflection: The Privacy Gate as a shared pure-function module was the cleanest architectural choice — it isolates the privacy invariant in one testable place and makes the Gmail watcher retrofit a single-line change. Tiered classifier + batch notification are now fully documented as implementation phases, not just spec requirements.

## Evaluation notes (flywheel)

- Failure modes observed: update-agent-context.sh failed (script reads wrong REPO_ROOT — known issue from previous sessions); worked around by writing plan artifacts directly without script dependency
- Graders run and results (PASS/FAIL): Constitution Check all 10 PASS; all NEEDS CLARIFICATION from spec resolved in research.md; no contradictions between plan.md and spec.md
- Prompt variant (if applicable): resumed from previous session after context compaction; all RI re-gathered from source files
- Next experiment (smallest change to try): /sp.tasks to generate the atomic task list with dependency ordering; expected ~20 tasks (T00-T20)
