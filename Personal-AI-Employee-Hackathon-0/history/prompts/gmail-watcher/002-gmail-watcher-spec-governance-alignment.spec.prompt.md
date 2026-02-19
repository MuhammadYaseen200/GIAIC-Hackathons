---
id: 002
title: Gmail Watcher Spec Governance Alignment Review
stage: spec
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: spec-architect review and enhance
labels: ["spec", "governance", "gmail-watcher", "phase-2", "constitution-alignment"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-gmail-watcher/spec.md
  - specs/005-gmail-watcher/checklists/requirements.md
tests:
  - N/A (spec phase, no implementation tests yet)
---

## Prompt

You are the spec-architect agent. Your task is to review and enhance the Gmail Watcher spec for Phase 2 of the H0 Personal AI Employee project. Read all governance files (constitution, mind map, AGENTS.md, LOOP.md, SKILLS.md, SWARM.md, MCP.md, HUMAN-TASKS.md), then rewrite the spec to align with all governance documents, incorporate watcher architecture details from the mind map, ensure MCP fallback protocols, LOOP.md enforcement, and HUMAN-TASKS.md dependencies are properly cited. Keep it business-focused (WHAT not HOW) per the spec template guidelines. Maintain all existing good content.

## Response snapshot

Rewrote `specs/005-gmail-watcher/spec.md` with comprehensive governance alignment. Key additions: (1) Governance Alignment table mapping all 6 control documents to spec sections, (2) Phase 2 entry/exit criteria per Constitution Principle VII, (3) Constraints-first section with NOT Supported list, performance limits, security boundaries, and technical debt, (4) Human-Dependent Prerequisites table citing HT-001, HT-002, HT-005, (5) Two new user stories (P4: vault file routing/Ralph Wiggum compatibility, P5: observability/health reporting), (6) Five new functional requirements (FR-013 through FR-017), (7) MCP Integration and Fallback Protocol section, (8) Enforcement Loop Integration section mapping Loops 1, 2, and 4, (9) NFR section (performance, scalability, security, observability), (10) Agent Assignments from AGENTS.md/SWARM.md, (11) Enhanced Dependencies section with upstream/downstream/external. Also updated the requirements checklist.

## Outcome

- Impact: Spec now fully aligned with all 6 governance documents and 9 constitution principles
- Tests: N/A (spec phase)
- Files: 2 files modified (spec.md, checklists/requirements.md)
- Next prompts: /sp.plan for architecture decisions, then /sp.tasks for implementation breakdown
- Reflection: Original spec was solid on user stories and core FRs but lacked governance traceability, phase gating, MCP fallback protocol, enforcement loop integration, and forward compatibility with Ralph Wiggum loop

## Evaluation notes (flywheel)

- Failure modes observed: None - all governance documents were consistent and non-contradictory
- Graders run and results (PASS/FAIL): Manual checklist review PASS (all items checked)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.plan to validate spec is sufficient for architecture decisions
