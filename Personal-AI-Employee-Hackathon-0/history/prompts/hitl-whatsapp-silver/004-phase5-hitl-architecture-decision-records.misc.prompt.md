---
id: "004"
title: Phase 5 Architecture Decision Records
stage: misc
date: 2026-03-02
surface: agent
model: claude-sonnet-4-6
feature: hitl-whatsapp-silver
branch: 008-hitl-whatsapp-silver
user: MuhammadYaseen200
command: /sp.adr
labels: ["phase-5","adr","privacy-gate","hitl","whatsapp-backend","tiered-classifier","architecture"]
links:
  spec: specs/008-hitl-whatsapp-silver/spec.md
  ticket: null
  adr: "history/adr/0010-0013"
  pr: null
files:
  - history/adr/0010-privacy-gate-mandatory-pre-processing-layer.md
  - history/adr/0011-hitl-approval-workflow-and-draft-state-machine.md
  - history/adr/0012-whatsapp-backend-strategy-and-mcp-transport-abstraction.md
  - history/adr/0013-three-layer-email-priority-classifier.md
  - history/prompts/hitl-whatsapp-silver/004-phase5-hitl-architecture-decision-records.misc.prompt.md
tests:
  - "none (governance/ADR phase)"
---

## Prompt

/sp.adr

create agent team instance to geather adr and read all required contect and documents
each gather the required docs
each read them all
each use them in adr creation
each monitor on adr generaton related skills, sub-agents, and mcps using in it or not
each monitor the whole project governance
  you have constitution, spec, plan, adr, tasks, data moel, quick start, research, phr,requirements and contracts file for backup support and as resource and Reusable intelligence to generate adr
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, autionations, workflows
- Use `context7` for final documentation/package checks, `code-search` for structural consistency, and `postgres` for state verification.
- use skills, sub-agents, mcps, plugins, hooks

## Response snapshot

**Step 1 — Context loaded**:
- Prerequisites script returned wrong REPO_ROOT (known issue); corrected manually to `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`
- Plan artifacts confirmed present: plan.md, research.md, data-model.md, contracts/
- Existing ADRs scanned: 0001-0009 (all accepted, Phase 2/3/4 decisions)

**Step 2 — Decisions extracted from plan.md + research.md**:
5 candidate clusters identified:
1. Privacy Gate architecture (Layer 0, pure function, shared utility) — new
2. HITL state machine (vault filesystem, draft IDs, batch notification, timeouts) — new
3. WhatsApp backend strategy (Go bridge primary, pywa fallback, bridge.py abstraction) — new
4. Three-layer email priority classifier (extends ADR-0004) — new
5. Calendar OAuth2 reuse (same credentials.json as Gmail) — TRIVIAL → rejected

**Step 4 — Significance test applied**:
- Privacy Gate: PASS (religious+security mandate; cross-cutting; all future watchers affected)
- HITL State Machine: PASS (Silver tier core; LOOP.md compliance; vault + orchestrator + MCPs)
- WhatsApp Backend: PASS (Meta dependency decision; session persistence; long-term infra)
- Tiered Classifier: PASS (token cost implications; drives HITL UX; extends ADR-0004)
- Calendar OAuth2 Reuse: FAIL (trivial application of ADR-0006 pattern; no new alternatives)

**create-adr.sh**: Failed (wrong REPO_ROOT in script). All 4 ADRs created using agent-native Write tool from template.

**ADRs created**:

| ID | Title | Key Decision | Alternatives Rejected |
|----|-------|-------------|----------------------|
| ADR-0010 | Privacy Gate — Mandatory Pre-Processing Layer | Shared pure-function utility; regex redaction; unconditional media block; Layer 0 in all watchers | Per-watcher inline (DRY violation), post-write scanner (race condition), cloud DLP (violates local-first), LLM detection (circular) |
| ADR-0011 | HITL Approval Workflow and Draft State Machine | Vault filesystem state machine; YAML frontmatter; batch WhatsApp notification; 24h/48h timeouts; HITLManager class | SQLite/Neon DB (Phase 6+), email approval (slower UX), individual notifications (flood), Telegram/Signal (extra app) |
| ADR-0012 | WhatsApp Backend Strategy and MCP Transport Abstraction | Go bridge primary (HT-004 DONE); pywa Cloud API secondary; WHATSAPP_BACKEND env switch; bridge.py abstraction | pywa only (HT-012 blocked), whatsapp-web.js (Node/Python mismatch), Twilio (paid cloud), no abstraction (hardcoded) |
| ADR-0013 | Three-Layer Email Priority Classifier | Layer 1 spam filter (0 tokens) → Layer 2 keyword heuristic (0 tokens) → Layer 3 LLM (AMBIGUOUS ~20-30%); priority drives HITL emoji + Calendar MCP trigger | Pure LLM (costly), pure keyword (inaccurate for ambiguous), two-layer spam+LLM (wasted tokens) |

**Existing ADRs referenced** (not duplicated):
- ADR-0001 (BaseWatcher — WhatsApp watcher inherits)
- ADR-0003 (JSONL pattern — privacy_gate.jsonl, hitl_decisions.jsonl follow same format)
- ADR-0004 (keyword heuristic — extended, not replaced, by ADR-0013)
- ADR-0005 (FastMCP+Pydantic v2+stdio — WhatsApp MCP and Calendar MCP follow)
- ADR-0006 (Gmail OAuth2 — Calendar MCP auth follows same pattern)
- ADR-0007 (MCPClient fallback — HITLManager uses MCPClient for WhatsApp+Gmail calls)
- ADR-0008 (error taxonomy — all Phase 5 MCPs use same error codes)

**Conflicts**: None detected.

## Outcome

- ✅ Impact: 4 ADRs created (0010-0013); 7 existing ADRs referenced; 0 conflicts; all placeholder-free; all cross-reference plan artifacts
- 🧪 Tests: None (ADR/governance phase)
- 📁 Files: history/adr/0010-0013 (4 files)
- 🔁 Next prompts: /sp.tasks
- 🧠 Reflection: ADR-0010 (Privacy Gate) is the most novel — documents a religious+security requirement as an architectural constraint, which is unusual in standard ADR practice. Correctly clustering "HITL workflow" (state machine + batch notification + timeouts + protocol) as one ADR rather than 4 separate ADRs was the right call — these all change together. ADR-0013 explicitly extends (not supersedes) ADR-0004, preserving Phase 2 archaeology while documenting Phase 5 additions.

## Evaluation notes (flywheel)

- Failure modes observed: create-adr.sh script fails with wrong REPO_ROOT (known issue from previous sessions); ADR template was correctly read directly to fill all placeholders without script dependency
- Graders run and results (PASS/FAIL): Significance test: 4/5 candidates PASS; Calendar OAuth2 correctly rejected as trivial. Cluster grader: all 4 ADRs are decision clusters (not atomic choices) — PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): /sp.tasks to generate atomic implementation task list; expected ~20-22 tasks with dependency ordering from T00 (vault setup) through T20 (MCP registry update)
