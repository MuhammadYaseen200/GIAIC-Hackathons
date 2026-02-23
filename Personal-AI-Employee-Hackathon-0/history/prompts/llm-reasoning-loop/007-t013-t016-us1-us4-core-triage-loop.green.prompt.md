---
id: "007"
title: T013-T016 US1-US4 Core Triage Loop Green
stage: green
date: 2026-02-23
surface: agent
model: claude-sonnet-4-6
feature: llm-reasoning-loop
branch: 006-llm-reasoning-loop
user: MuhammadYaseen200
command: /sp.implement
labels: ["core-loop", "prompts", "vault-ops", "orchestrator", "ralph-wiggum", "green"]
links:
  spec: specs/006-llm-reasoning-loop/spec.md
  ticket: null
  adr: specs/006-llm-reasoning-loop/plan.md#adr-0006
  pr: null
files:
  - orchestrator/prompts.py
  - orchestrator/vault_ops.py
  - orchestrator/orchestrator.py
  - tests/unit/test_prompts.py
  - tests/unit/test_vault_ops.py
  - specs/006-llm-reasoning-loop/tasks.md
tests:
  - tests/unit/test_prompts.py (31 tests — 31 passed)
  - tests/unit/test_vault_ops.py (27 tests — 27 passed)
  - tests/unit/ full suite (241 tests — 241 passed, 0 regressions)
---

## Prompt

T013–T016 (Phase 4: US1+US4 — Email Triage Core Loop)

you have constitution, spec, adr, plan, tasks, research and phr file for backup support and as resource and Reusable intelligence to start implementation
- create claude agent team instance
- apply all governance and control
- use skills, sub-agents, mcps, plugins, hooks

when complete then we move to next phase, if found bug and error or if work in wrong directory instead of
/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0, stop and get the correct directory

AGENT STACK (Mobilized):
- Command Team: @qa-overseer, @loop-controller, @imperator, @path-warden
- Build Team: @modular-ai-architect, @ux-frontend-developer, @spec-architect
- Skills: building-mcp-servers, scaffolding-openai-agents, streaming-llm-responses, deployment-preflight-check, security-scan, env-validator, spec-driven-development, skill-creator
- MCP Servers: context7, code-search, postgres

## Response snapshot

Implemented T013–T016 (Phase 4: US1+US4 — Email Triage Core Loop):

**T013** — `orchestrator/prompts.py`:
- `build_system_prompt()` → 400-token Ralph Wiggum prompt with 5 decision types, JSON schema, financial safety constraint (payment/invoice/billing → NEVER archive), RESPOND ONLY WITH JSON instruction
- `build_user_message(ctx, truncated_body)` → formatted email metadata + body
- `build_correction_prompt(error, original_response)` → retry prompt capped at 500 chars of original
- `estimate_tokens(text)` → `len(text) // 4` heuristic (FR-022)
- `truncate_body(body, remaining_budget_tokens)` → returns (text, was_truncated) with TRUNCATED notice
- `prepare_body_for_context(system, meta, body)` → full 4-step budget pipeline

**T014** — `orchestrator/vault_ops.py`:
- `scan_pending_emails(dir)` → glob *.md, regex-split frontmatter, check status: pending; skips corrupt files silently
- `read_email_context(path)` → parses `from:` → sender, body after `---`, raises ValueError on missing message_id
- `update_frontmatter(path, updates)` → atomic_write, preserves body exactly
- `append_to_body(path, text)` → atomic_write with newline separator
- `write_draft_reply(drafts_dir, draft)` → creates vault/Drafts/draft_{id}.md with YAML frontmatter + reply_body
- `move_to_done(path, done_dir)` → shutil.move, creates done_dir if absent
- `ensure_directory(path)` → mkdir(parents=True, exist_ok=True)

**T015** — `orchestrator/orchestrator.py`:
- `RalphWiggumOrchestrator(BaseWatcher)` — name="orchestrator", poll_interval=120
- `validate_prerequisites()` → checks LLM_PROVIDER env, vault/Needs_Action/, vault/Done/, auto-creates vault/Drafts/
- `poll()` → scan_pending_emails → read_email_context per path → filter processed_ids → return list[EmailContext]
- `process_item(ctx)` → `_call_llm_with_retry()` → `_apply_decision()` → update frontmatter → log JSONL entry
- `_call_llm_with_retry()` → Ralph Wiggum loop: LLM call → JSON parse → Pydantic validate → correction on failure → max_iterations → MaxIterationsExceeded → status: failed
- `_apply_decision()` → 5 decision branches: draft_reply (write draft + pending_approval), needs_info (append note), archive (update + move to Done), urgent (priority=urgent + write draft), delegate (append delegation note)
- `_write_decision_log()` → DecisionLogEntry → BaseWatcher._log() JSONL
- `_save_orch_state()` / `_load_orch_state()` → OrchestratorState to vault/Logs/orchestrator_extended_state.json

**Test results**: 58 new tests (58 passed). Full suite: 241/241 passed.

## Outcome

- ✅ Impact: US1 + US4 complete — the full triage core loop is implemented. Ralph Wiggum retry pattern, financial safety constraint in prompt, all 5 decision types with vault file mutations, audit JSONL logging.
- 🧪 Tests: 58 new tests (31 prompts + 27 vault_ops). 241/241 full suite. 0 regressions.
- 📁 Files: 5 files created in orchestrator/ and tests/unit/
- 🔁 Next prompts: T017–T019 (Phase 5: US3 Draft Reply validation tests), or T020–T022 (Phase 6: US4 retry + financial safety tests)
- 🧠 Reflection: T013 and T014 written in parallel (independent). T015 uses `prepare_body_for_context()` for token budget, delegates all vault I/O to vault_ops, delegates all logging to BaseWatcher._log(). Extended state (OrchestratorState) kept separate from WatcherState to avoid BaseWatcher conflicts.

## Evaluation notes (flywheel)

- Failure modes observed: None — 241/241 green on first run.
- Graders run and results (PASS/FAIL): `pytest tests/unit/test_prompts.py tests/unit/test_vault_ops.py -v` → 58 PASSED. Full: 241 PASSED.
- Prompt variant (if applicable): sp.implement T013-T016 Phase 4 US1+US4
- Next experiment: Write live connectivity test with real Anthropic key — `python scripts/verify_llm_provider.py` — then run T017-T022 for draft/retry/financial tests
