---
id: "003"
title: Phase 6 Gold ADR Architectural Decisions
stage: misc
date: 2026-03-11
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: m-y-j
command: sp.adr
labels: ["phase-6","gold","adr","odoo","social-media","ralph-wiggum","llm-fallback","mcp-architecture"]
links:
  spec: specs/010-ceo-briefing-odoo-gold/spec.md
  ticket: null
  adr: history/adr/0016-odoo-api-protocol-selection.md
  pr: null
files:
  - history/adr/0016-odoo-api-protocol-selection.md
  - history/adr/0017-social-media-mcp-architecture.md
  - history/adr/0018-ralph-wiggum-loop-implementation.md
  - history/adr/0019-ceo-briefing-llm-fallback-strategy.md
tests:
  - Significance test: all 4 ADRs pass (cross-cutting, alternatives listed, long-term impact)
  - No conflicts with existing ADRs 0001-0015
---

## Prompt

/sp.adr (user confirmed: "if plan complete, so now i give you command for adr??")

## Response snapshot

Ran `/sp.adr` for `010-ceo-briefing-odoo-gold`. Scanned existing ADRs 0001–0015, verified no
conflicts. Applied 3-part significance test to all 4 candidates from plan.md — all passed.
Created 4 ADRs:

**ADR-0016 — Odoo API Protocol Selection** (`0016-odoo-api-protocol-selection.md`):
- Decision: JSON-RPC via `/web/dataset/call_kw` + `/web/session/authenticate` session auth
- Alternatives rejected: XML-RPC (deprecated/sync), REST API (incomplete Community coverage), `odoorpc` library (sync wrapper)
- Key insight: Plain `httpx.AsyncClient` — zero new dependencies; mirrors LinkedIn auth singleton (ADR-0014)

**ADR-0017 — Social Media MCP Architecture** (`0017-social-media-mcp-architecture.md`):
- Decision: 3 separate FastMCP servers (facebook+instagram share one server, twitter separate)
- Alternatives rejected: Unified social MCP (single failure domain), platform-agnostic base class (FastMCP registration incompatible with inheritance)
- Key insight: Facebook + Instagram share one server because they share one Page Access Token; Twitter is structurally separate (OAuth 1.0a + tweepy)

**ADR-0018 — Ralph Wiggum Loop Implementation** (`0018-ralph-wiggum-loop-implementation.md`):
- Decision: New `run_until_complete()` per-workflow-step retry wrapper in `orchestrator/run_until_complete.py`
- Alternatives rejected: 15-min polling only (15-min retry violates SC-001), Temporal/Celery (massive dependency), `tenacity` decorator (scattered config, no HITL escalation callback)
- Key insight: Outer loop (15-min orchestrator) + inner loop (per-step retry) coexist; they serve different purposes

**ADR-0019 — CEO Briefing LLM Fallback Strategy** (`0019-ceo-briefing-llm-fallback-strategy.md`):
- Decision: Two-tier — LLM primary, template fallback on any API exception; `[TEMPLATE MODE]` flag in WhatsApp notification
- Alternatives rejected: Hard-fail (violates SC-001), cached stale briefing (misleading), local LLM (GPU overhead), split commands
- Key insight: Data collection is fully independent of LLM — all sections collected before draft step; credit failure only affects narrative quality, not data delivery

## Outcome

- ✅ Impact: 4 ADRs created, all significant decisions documented before implementation begins
- 🧪 Tests: Significance test 4/4 PASS; no conflicts with ADRs 0001–0015
- 📁 Files: history/adr/0016–0019 (4 new ADRs)
- 🔁 Next prompts: `/sp.tasks` to generate tasks.md (T001–T110)
- 🧠 Reflection: ADR-0017 revealed that Facebook+Instagram sharing one server is architecturally sound because they share one credential (Page Access Token), not just for convenience. ADR-0019 makes explicit that the template fallback is NOT a degraded state — it delivers the same data, just without LLM narrative synthesis.

## Evaluation notes (flywheel)

- Failure modes observed: None — all 4 ADR candidates from plan were genuinely significant; no over-granular ADRs created
- Graders run and results (PASS/FAIL): Significance test 4/4 PASS; clustering check PASS (no atomic single-library ADRs)
- Prompt variant (if applicable): User confirmed ADR step via natural language ("if plan complete, so now i give you command for adr??")
- Next experiment (smallest change to try): Run /sp.tasks to generate dependency-ordered tasks.md before /sp.implement
