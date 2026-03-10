---
id: 002
title: LinkedIn Cron Silver Spec Clarifications
stage: spec
date: 2026-03-05
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: owner
command: /sp.clarify
labels: [clarify,linkedin,oauth2,token-refresh,topic-source,whatsapp-notification,hitl,spec]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/009-linkedin-cron-silver/spec.md
tests:
  - Spec validation: no [NEEDS CLARIFICATION] markers remain
  - Clarifications section present with 3 Q&A entries
  - FR-005 updated with notification format
  - FR-017 added for topic file
  - Assumptions updated with offline_access scope and topic file
---

## Prompt

/sp.clarify

## Response snapshot

3 clarification questions asked and answered for specs/009-linkedin-cron-silver/spec.md:

Q1: Token refresh strategy → A: Auto-refresh with offline_access scope + refresh token stored in linkedin_token.json
Q2: Daily post topic source → B: Configurable vault/Config/linkedin_topics.md file (owner-editable, random daily pick)
Q3: WhatsApp notification format → B enriched: topic name + type + 300-char preview + referenced links + vault path + approve/reject instructions

Spec updated: Clarifications section added, FR-005 enriched, FR-017 added, Assumptions updated.

## Outcome

- ✅ Impact: 3 previously Partial categories (token refresh, content source, notification UX) fully resolved; spec ready for /sp.plan
- 🧪 Tests: Spec validation PASS — no placeholders, all 3 Q&As recorded, no contradictions
- 📁 Files: specs/009-linkedin-cron-silver/spec.md (updated — Clarifications section, FR-005, FR-017, Assumptions)
- 🔁 Next prompts: /sp.adr linkedin-oauth2-offline-access (ADR-0014), then /sp.plan
- 🧠 Reflection: Q3 user customization (topic+type+links+summary) is a better HITL UX than any of the original options — owner-driven expansion of options is valuable signal for spec quality

## Evaluation notes (flywheel)

- Failure modes observed: None — all 3 questions cleanly resolved
- Graders run and results (PASS/FAIL): Spec validation PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): Pre-populate WhatsApp notification format template in spec template so future features don't need to re-clarify it
