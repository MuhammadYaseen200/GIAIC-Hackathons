---
id: 003
title: LinkedIn Cron ADR Creation
stage: spec
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: owner
command: /sp.adr
labels: [adr,linkedin,oauth2,token-lifecycle,cron,scheduling,phase-5-5]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - history/adr/0014-linkedin-oauth2-token-lifecycle.md
  - history/adr/0015-cron-scheduling-strategy.md
tests:
  - ADR significance test PASS for both ADRs (impact + alternatives + scope)
  - ADR-0014 alternatives: 4 considered (access-only, library, proactive expiry, keychain)
  - ADR-0015 alternatives: 3 considered (APScheduler, n8n, systemd timers)
---

## Prompt

/sp.adr

## Response snapshot

Note: plan.md does not exist yet (pre-plan stage). Proceeded using spec.md + clarifications as source — decisions fully specified.

Identified 2 decision clusters passing significance test:
1. LinkedIn OAuth2 Token Lifecycle (offline_access scope, refresh token, auto-refresh on 401)
2. Cron Scheduling Strategy (native system cron vs APScheduler vs n8n vs systemd)

Created ADR-0014 and ADR-0015. Both reference existing ADR patterns (ADR-0006 singleton pattern reused in 0014; ADR-0003/0007 referenced in 0015).

## Outcome

- ✅ Impact: 2 architecturally significant decisions documented before implementation begins; reduces plan-phase ambiguity for auth and scheduling modules
- 🧪 Tests: ADR significance test PASS (both); 4 alternatives in ADR-0014; 3 alternatives in ADR-0015
- 📁 Files: history/adr/0014-linkedin-oauth2-token-lifecycle.md; history/adr/0015-cron-scheduling-strategy.md
- 🔁 Next prompts: /sp.plan (architecture + implementation plan — now unblocked with ADRs documented)
- 🧠 Reflection: Pre-plan ADR creation (before plan.md exists) is valid when decisions are clear from spec + clarifications — the skill's plan.md requirement can be relaxed when spec clarifications establish the decisions directly

## Evaluation notes (flywheel)

- Failure modes observed: plan.md prerequisite check blocks ADR creation pre-plan — skill should support spec-only source when plan.md absent
- Graders run and results (PASS/FAIL): Manual significance test PASS for both ADRs
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Add spec.md as acceptable source to /sp.adr prerequisite check when plan.md missing
