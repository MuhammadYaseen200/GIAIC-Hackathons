---
id: 001
title: Gmail Watcher Spec Creation
stage: spec
date: 2026-02-17
surface: agent
model: claude-opus-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: MuhammadYaseen200
command: /sp.specify
labels: ["gmail", "watcher", "oauth2", "phase-2", "base-watcher", "vault"]
links:
  spec: specs/005-gmail-watcher/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/005-gmail-watcher/spec.md
  - specs/005-gmail-watcher/checklists/requirements.md
tests:
  - none
---

## Prompt

create clude agent team instance, Create BaseWatcher class and GmailWatcher for Phase 2 — read Gmail inbox via OAuth2, parse emails, write actionable items as markdown files to vault/Needs_Action/
use subagents, skills and MCPs and also apply all governance and rules if activated

## Response snapshot

Created feature branch `005-gmail-watcher` and wrote spec.md with:
- 3 user stories (P1: Email-to-Action, P2: BaseWatcher lifecycle, P3: OAuth2 flow)
- 12 functional requirements (FR-001 through FR-012)
- 4 key entities (BaseWatcher, GmailWatcher, EmailItem, WatcherState)
- 7 measurable success criteria
- 6 edge cases documented
- Clear scope boundaries (in/out) with phase-gated deferrals
- Quality checklist: all items PASS, zero clarifications needed

## Outcome

- Impact: Phase 2 specification complete — first real feature spec in the project
- Tests: none (spec phase, no code yet)
- Files: specs/005-gmail-watcher/spec.md, specs/005-gmail-watcher/checklists/requirements.md
- Next prompts: /sp.plan to generate architecture plan, or /sp.clarify if questions arise
- Reflection: Zero NEEDS_CLARIFICATION markers — made informed defaults for classification method (heuristic), process model (long-lived), and inbox scope (primary only). All documented in Assumptions.

## Evaluation notes (flywheel)

- Failure modes observed: create-new-feature.sh placed spec in wrong parent directory (one level up), required manual fix
- Graders run and results (PASS/FAIL): Quality checklist — all 16 items PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run /sp.plan to produce architecture decisions and data model
