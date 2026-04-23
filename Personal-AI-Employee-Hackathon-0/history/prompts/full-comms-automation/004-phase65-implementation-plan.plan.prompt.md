---
id: "004"
title: "Phase 6.5 Implementation Plan Complete"
stage: plan
date: 2026-04-11
surface: agent
model: claude-sonnet-4-6
feature: full-comms-automation
branch: 011-full-comms-automation
user: m-y-j
command: /sp.plan
labels: ["plan","phase-6.5","hitl-queue","model-routing","gmail","whatsapp","linkedin","calendar","social"]
links:
  spec: specs/011-full-comms-automation/spec.md
  ticket: null
  adr: history/adr/0020-multi-model-routing-strategy.md
  pr: null
files:
  - specs/011-full-comms-automation/plan.md
  - specs/011-full-comms-automation/research.md
  - specs/011-full-comms-automation/data-model.md
  - specs/011-full-comms-automation/quickstart.md
  - specs/011-full-comms-automation/contracts/gmail-tools.md
  - specs/011-full-comms-automation/contracts/whatsapp-tools.md
  - specs/011-full-comms-automation/contracts/calendar-tools.md
  - specs/011-full-comms-automation/contracts/linkedin-tools.md
  - specs/011-full-comms-automation/contracts/social-tools.md
tests:
  - none (plan phase — tests defined per implementation phase in plan.md)
---

## Prompt

/sp.plan

(Phase 6.5 spec fully clarified, ADR-0020 created. Generate implementation plan.)

## Response snapshot

Generated full implementation plan with 8 phases (A-H):
- Phase A: Infrastructure (HITL queue, model routing, classifiers)
- Phase B: Gmail write & triage
- Phase C: Calendar write
- Phase D: WhatsApp media & management
- Phase E: LinkedIn extension
- Phase F: Social media extension (Facebook/Instagram/Twitter)
- Phase G: Orchestrator & briefing updates
- Phase H: Tests, security & QA

Generated: plan.md, research.md (8 research areas), data-model.md (6 entities, 3 SQLite DBs), quickstart.md, 5 MCP contract files.

Constitution check: ALL 10 principles PASS.

## Outcome

- Impact: Complete implementation roadmap for Phase 6.5. All architectural decisions documented. Contract-first design prevents integration surprises.
- Tests: TDD plan defined per phase with coverage targets (90% classifiers, 80% MCP tools)
- Files: 9 new planning artifacts created
- Next prompts: /sp.tasks
- Reflection: Research agents found 3 critical corrections: (1) WhatsApp MCP is text-only — Phase D bigger than expected; (2) Gmail MCP already has write scopes + send/move/label — Phase B smaller; (3) hitl_manager.py already exists — extend not rebuild. All corrections applied to plan.md and research.md.

## Evaluation notes (flywheel)

- Failure modes observed: none — research agents confirmed bridge capabilities
- Graders run and results: Constitution check ALL PASS
- Prompt variant: none
- Next experiment: /sp.tasks to generate atomic task list
