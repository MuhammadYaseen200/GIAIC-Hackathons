---
id: "003"
title: "ADR-0020 Multi-Model Routing Strategy"
stage: misc
date: 2026-04-11
surface: agent
model: claude-sonnet-4-6
feature: full-comms-automation
branch: 011-full-comms-automation
user: m-y-j
command: /sp.adr model-routing-strategy
labels: ["adr","model-routing","cost-optimization","openrouter","free-models","phase-6.5"]
links:
  spec: specs/011-full-comms-automation/spec.md
  ticket: null
  adr: history/adr/0020-multi-model-routing-strategy.md
  pr: null
files:
  - history/adr/0020-multi-model-routing-strategy.md
tests:
  - none (architecture decision — no tests at this stage)
---

## Prompt

/sp.adr model-routing-strategy

(Following /sp.clarify Q3: user identified token burn on greeting emails, confirmed switch from Claude-only to free models for development and routine tasks)

## Response snapshot

Created ADR-0020: Multi-Model Routing Strategy. Three-tier routing:
- Tier 0: Rule-based (zero LLM cost) — greeting detection, spam keywords, OTP flagging
- Tier 1: Free/cheap model via OpenRouter (Gemini Flash, Qwen, Mistral) — email categorization, intent classification, summarization
- Tier 2: Strong model (Anthropic claude-sonnet-4-6) — sensitive drafting, briefing synthesis, brand-voice content
Routing config in config/model_routing.yaml (no code change for tier adjustments).
Privacy constraint: Tier 1 receives only metadata, never full message body.

## Outcome

- ✅ Impact: Cost optimization architecture defined before implementation begins. Prevents token burn at scale. Extends ADR-0019 from reactive fallback to proactive cost routing.
- 🧪 Tests: None (ADR phase)
- 📁 Files: history/adr/0020-multi-model-routing-strategy.md
- 🔁 Next prompts: /sp.plan
- 🧠 Reflection: Privacy constraint (Tier 1 gets metadata only, not full body) emerged during ADR writing — important guardrail that should be in spec FR as well. Worth adding to spec before /sp.plan.

## Evaluation notes (flywheel)

- Failure modes observed: Privacy risk at Tier 1 (sending message content to third-party free models) — caught and mitigated in ADR
- Graders run and results (PASS/FAIL): Significance test — all 3 criteria PASS
- Prompt variant (if applicable): Pre-plan ADR (plan.md does not exist yet — created from clarification context)
- Next experiment (smallest change to try): Add FR-043 to spec covering Tier 1 metadata-only constraint
