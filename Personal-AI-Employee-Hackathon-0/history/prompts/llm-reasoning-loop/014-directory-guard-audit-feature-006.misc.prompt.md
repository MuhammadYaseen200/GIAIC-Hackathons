---
id: "014"
title: Directory Guard Audit Feature 006 LLM Reasoning Loop
stage: misc
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: llm-reasoning-loop
branch: 006-llm-reasoning-loop
user: m-y-j
command: validate file placements for 006-llm-reasoning-loop feature
labels: ["directory-guard","audit","path-warden","loop-4","file-placement","006-llm-reasoning-loop"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - orchestrator/__init__.py
  - orchestrator/models.py
  - orchestrator/orchestrator.py
  - orchestrator/prompts.py
  - orchestrator/vault_ops.py
  - orchestrator/providers/__init__.py
  - orchestrator/providers/base.py
  - orchestrator/providers/anthropic_adapter.py
  - orchestrator/providers/openai_compatible_adapter.py
  - orchestrator/providers/registry.py
  - scripts/verify_llm_provider.py
  - tests/unit/test_orchestrator_models.py
  - tests/unit/test_providers.py
  - tests/unit/test_prompts.py
  - tests/unit/test_vault_ops.py
  - tests/unit/test_draft_reply.py
  - tests/unit/test_orchestrator_decisions.py
  - tests/unit/test_ralph_wiggum_retry.py
  - tests/unit/test_financial_safety.py
  - tests/unit/test_provider_normalization.py
  - tests/unit/test_logging.py
  - tests/unit/test_state_persistence.py
  - tests/unit/test_lifecycle.py
  - tests/integration/test_lifecycle_integration.py
  - tests/integration/test_full_triage_cycle.py
  - tests/integration/test_edge_cases.py
  - vault/Drafts/.gitkeep
  - specs/006-llm-reasoning-loop/spec.md
  - specs/006-llm-reasoning-loop/plan.md
  - specs/006-llm-reasoning-loop/tasks.md
  - history/prompts/llm-reasoning-loop/
  - ai-control/AGENTS.md
  - ai-control/LOOP.md
  - ai-control/SWARM.md
  - ai-control/SKILLS.md
  - ai-control/MCP.md
  - ai-control/HUMAN-TASKS.md
  - CLAUDE.md
  - history/prompts/llm-reasoning-loop/014-directory-guard-audit-feature-006.misc.prompt.md
tests:
  - "Manual structural audit against ai-control/LOOP.md Loop 4 canonical directory map"
  - "Manual structural audit against ai-control/AGENTS.md Path-Warden governance"
---

## Prompt

Validate all file placements for the completed `006-llm-reasoning-loop` feature (Ralph Wiggum Orchestrator) in the project at `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`.

## Files to validate
Use `ai-control/LOOP.md` (Loop 4 — Directory Guard) and `ai-control/AGENTS.md` as your canonical placement authority. The canonical directory map is:

| Content Type | Correct Location |
|-------------|-----------------|
| Specs | `specs/<feature>/` |
| ADRs | `history/adr/` |
| PHRs | `history/prompts/<category>/` |
| Agent governance | `ai-control/` |
| Watchers | `watchers/` |
| Orchestrator | `orchestrator/` |
| Tests (unit) | `tests/unit/` |
| Tests (integration) | `tests/integration/` |
| Vault files | `vault/` |
| Scripts | `scripts/` |

## Files created in this feature
[36 files listed across orchestrator/, scripts/, tests/unit/, tests/integration/, vault/, specs/, history/prompts/, ai-control/, and CLAUDE.md]

Report: PASS (all correct) or FAIL (list any misplaced files with correct target path).

## Response snapshot

VERDICT: PASS

All 36 explicitly listed feature files for `006-llm-reasoning-loop` are in their canonical locations per the Loop 4 Directory Guard map in `ai-control/LOOP.md`.

Key findings:
- `orchestrator/` package (10 files): all correctly placed under `orchestrator/` and `orchestrator/providers/`
- `scripts/verify_llm_provider.py`: correct — utility scripts belong in `scripts/`
- `tests/unit/` (13 test files): all correctly placed under `tests/unit/`
- `tests/integration/` (3 test files): all correctly placed under `tests/integration/`
- `vault/Drafts/.gitkeep`: correct — vault state-machine subdirectory
- `specs/006-llm-reasoning-loop/` (spec.md, plan.md, tasks.md): all correct
- `history/prompts/llm-reasoning-loop/` (PHRs 001-013): all 13 confirmed present and correctly routed
- `ai-control/` (6 governance files): all correctly placed
- `CLAUDE.md` at root: correct per Claude Code toolchain convention

Pre-existing WARNING items (out of scope for this feature's verdict):
- `live_run.py` at root — should move to `scripts/`
- `smoke_test.py` at root — should move to `scripts/`
- `verify_bronze_exit.py` at root — should move to `scripts/`

These pre-date this feature and do not affect the PASS verdict.

## Outcome

- Impact: Full directory compliance confirmed for the 006-llm-reasoning-loop feature. Zero misplaced files. 36/36 checked files are in canonical locations.
- Tests: Manual audit cross-referencing file system state against ai-control/LOOP.md Loop 4 canonical directory map.
- Files: Audit covered orchestrator/, scripts/, tests/unit/, tests/integration/, vault/Drafts/, specs/006-llm-reasoning-loop/, history/prompts/llm-reasoning-loop/, ai-control/, CLAUDE.md.
- Next prompts: Address pre-existing root-level script misplacements (live_run.py, smoke_test.py, verify_bronze_exit.py) in a dedicated cleanup task.
- Reflection: The feature followed directory conventions rigorously throughout development. The PHR trail (001-014) is complete. The only structural noise is from earlier features, not from this one.

## Evaluation notes (flywheel)

- Failure modes observed: None for this feature. Pre-existing misplacements from prior features noted.
- Graders run and results (PASS/FAIL): Loop 4 Directory Guard — PASS
- Prompt variant (if applicable): null
- Next experiment: Automate Loop 4 compliance checks as a pre-commit hook or CI step to prevent root-level script accumulation in future features.
