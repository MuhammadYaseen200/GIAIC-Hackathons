---
id: "002"
title: "Phase 6.5 Spec Clarifications Complete"
stage: spec
date: 2026-04-11
surface: agent
model: claude-sonnet-4-6
feature: full-comms-automation
branch: 011-full-comms-automation
user: m-y-j
command: /sp.clarify phase 6.5
labels: ["spec","clarify","hitl","whatsapp","linkedin","gmail","contacts","model-choice"]
links:
  spec: specs/011-full-comms-automation/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/011-full-comms-automation/spec.md
tests:
  - none (spec phase)
---

## Prompt

/sp.clarify — 5 questions asked and answered across HITL behavior, WhatsApp Business, Gmail auto-reply strategy, LinkedIn DM API, and cross-platform contact linking. User also confirmed model switch from Claude credits to free/cheap models for development.

## Response snapshot

5/5 questions resolved:
1. HITL = non-blocking, indefinite queue, daily briefing reminders
2. WhatsApp Business = family member's account for dev/test; personal is primary
3. Gmail auto-reply = pre-written templates + rule-based classifier (no LLM for greetings)
4. LinkedIn DMs = apply for partner API; defer to Phase 7 if rejected
5. Contacts = explicit CEO-request linking only; ContactRecord stores all identifiers

Model switch saved to memory: use free models (Gemini Flash, Qwen, Mistral) for routine tasks.

## Outcome

- ✅ Impact: All 5 critical ambiguities resolved. Spec has zero unresolved markers. Ready for /sp.plan.
- 🧪 Tests: None (spec phase)
- 📁 Files: specs/011-full-comms-automation/spec.md (updated — Clarifications section + FR-012, FR-020, FR-038, ContactRecord, HITLRequest, Risks, Assumptions)
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: User's pushback on Option B (AI-generated replies) was correct — rule-based classifier saves tokens on zero-value emails. Model routing strategy is an ADR candidate for /sp.plan.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): 0 unresolved placeholders, 5 clarification bullets confirmed
- Prompt variant (if applicable): none
- Next experiment (smallest change to try): /sp.plan to generate architecture decisions
