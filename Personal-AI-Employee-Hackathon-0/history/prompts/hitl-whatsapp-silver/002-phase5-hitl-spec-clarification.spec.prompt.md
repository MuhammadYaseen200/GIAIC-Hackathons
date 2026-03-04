---
id: "002"
title: Phase 5 HITL Spec Clarification
stage: spec
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 008-hitl-whatsapp-silver
user: owner
command: /sp.clarify
labels: ["phase-5","whatsapp","hitl","calendar","clarification","spec"]
links:
  spec: specs/008-hitl-whatsapp-silver/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/008-hitl-whatsapp-silver/spec.md
  - ai-control/HUMAN-TASKS.md
  - history/prompts/hitl-whatsapp-silver/002-phase5-hitl-spec-clarification.spec.prompt.md
tests:
  - "none (spec phase)"
---

## Prompt

/sp.clarify if you want to clarify something confusing, or explain me any thing you can ask
and explain me about this phase what we are going to do in it, for my understanding and clarify so if i have any question i will ask you

[User also provided mid-session answers and design input:]
- HT-011: calendar.readonly scope already added; asked if credentials.json re-download needed
- HT-012: asked about WHATSAPP_VERIFY_TOKEN origin
- Q1 answer: Go bridge first, pywa as fallback
- Q2 answer: yes (7 days suggested)
- Q3 answer: A (capture only, no WhatsApp auto-drafting in Phase 5)
- Q4 answer: Cap at 5 + batch summary message idea (name/email, subject, priority tag)
- Q5: left decision to agent — tiered classifier chosen

## Response snapshot

Explained Phase 5 to user in plain language (3 components: WhatsApp Watcher, HITL Manager, Calendar MCP). Answered practical questions:
- credentials.json: NO re-download needed; just run calendar_auth.py to get calendar_token.json
- WHATSAPP_VERIFY_TOKEN: user-created string, pasted into both .env and Meta Developer Console (deferred — Go bridge first)
- .env update: WHATSAPP_BACKEND=go_bridge, WHATSAPP_BRIDGE_URL, OWNER_WHATSAPP_NUMBER, Calendar paths, HITL timeout vars

5 clarification questions asked and answered:
1. WhatsApp backend → Go bridge primary, pywa fallback [spec updated]
2. Calendar look-ahead window → 7 days default [FR-022 updated]
3. WhatsApp auto-drafting scope → Capture only; US4 deferred [US4 marked DEFERRED]
4. Concurrent draft handling → Cap 5 + batch summary message with priority tags [FR-014 redesigned as FR-014/FR-014a/FR-014b; SC-002 updated to 2min]
5. Priority classification → Tiered: Layer 1 spam filter (0 tokens) + Layer 2 keyword heuristic (0 tokens) + Layer 3 LLM only for ambiguous (~20-30% of emails) [FR-025 updated]

## Outcome

- ✅ Impact: 5 clarification questions resolved + mandatory Privacy Gate added (FR-031–FR-039, SC-009–SC-010); spec covers batch notification, tiered classifier, Go bridge primary, 7-day calendar window, US4 deferred, and full sensitive content protection policy
- 🧪 Tests: None (spec phase)
- 📁 Files: specs/008-hitl-whatsapp-silver/spec.md (Clarifications section added, FR-014/FR-014a/FR-014b/FR-022/FR-025 updated, US4 marked DEFERRED, Assumptions updated), ai-control/HUMAN-TASKS.md (HT-011 IN_PROGRESS, HT-012 DEFERRED)
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: The batch notification + tiered classifier were user-driven design improvements that significantly changed the HITL UX. Letting users shape UX decisions while agent handles token-cost tradeoffs worked well.

## Evaluation notes (flywheel)

- Failure modes observed: create-phr.sh script failed (exit 1) — used agent-native Write fallback
- Graders run and results (PASS/FAIL): spec Clarifications section validates; all 5 Q&A bullets present; no contradictory text
- Prompt variant (if applicable): user requested explanation first, then clarification — dual-mode session
- Next experiment (smallest change to try): /sp.plan to formalize the tiered classifier and batch notification as architectural components
