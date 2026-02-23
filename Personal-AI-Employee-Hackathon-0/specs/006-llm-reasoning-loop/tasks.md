# Tasks: Multi-LLM Reasoning Loop (Ralph Wiggum Orchestrator) — Phase 3

**Feature Branch**: `006-llm-reasoning-loop`
**Spec**: `specs/006-llm-reasoning-loop/spec.md`
**Plan**: `specs/006-llm-reasoning-loop/plan.md`
**Date**: 2026-02-23
**Status**: Ready for implementation

---

## Quick Reference

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Email Triage Decision (core loop) | T013–T016 |
| US2 | P2 | Multi-LLM Provider Abstraction | T007–T012 |
| US3 | P3 | Draft Reply Generation | T017–T019 |
| US4 | P4 | Structured Prompting (Ralph Wiggum) | T020–T022 |
| US5 | P5 | Audit Trail & Observability | T023–T026 |
| US6 | P6 | Orchestrator Lifecycle | T027–T031 |

**Note on US order**: US2 (providers) is implemented before US1 (triage) because the triage loop requires a provider to call. This is an implementation dependency, not a spec priority change.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization — directories, dependencies, conftest

**Checkpoint**: `python -c "import anthropic, openai, pydantic; print('OK')"` passes; directory structure matches plan.md layout.

- [X] T001 Add Phase 3 dependencies to `requirements.txt`: `anthropic>=0.40.0`, `openai>=1.50.0`, `pydantic>=2.0.0`, `pytest-asyncio>=0.23.0`
- [X] T002 Install requirements: `pip install -r requirements.txt` in project `.venv`
- [X] T003 Create `orchestrator/` package skeleton (empty `__init__.py` + `providers/` subdirectory) per `specs/006-llm-reasoning-loop/plan.md` Section 11 layout
- [X] T004 [P] Create `tests/unit/` and `tests/integration/` directories with `__init__.py` and shared `tests/conftest.py` (pytest fixtures: `tmp_vault_dir`, `mock_email_file`, `mock_llm_response`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic data models and provider interface — required by ALL user stories before any can begin.

**Checkpoint**: `pytest tests/unit/test_orchestrator_models.py -v` — all model validation tests pass. `from orchestrator.providers.base import LLMProvider` imports without error.

- [X] T005 Implement `orchestrator/models.py`: define `DecisionType` (Literal enum: draft_reply, needs_info, archive, urgent, delegate), `LLMDecision` (Pydantic BaseModel with decision, confidence 0.0–1.0, reasoning, reply_body Optional), `EmailContext` (sender, subject, body, message_id, classification, priority, date_received), `DraftReply` (type, status, source_message_id, to, subject, drafted_by, drafted_at, reply_body), `OrchestratorState` (processed_ids set, error_counts dict, decision_counts dict, last_run Optional), `DecisionLogEntry` (timestamp, event, provider, model, email_message_id, email_subject, decision, confidence, reasoning, tokens_input, tokens_output, latency_ms, iteration, severity)
- [X] T006 [P] Implement `orchestrator/providers/base.py`: define abstract `LLMProvider` ABC with `async def complete(system_prompt, user_message, temperature=0.3, max_tokens=1024) -> tuple[str, int, int]`, `def provider_name() -> str`, `def model_name() -> str` per `specs/006-llm-reasoning-loop/plan.md` Section 5.2.1
- [X] T007 Write `tests/unit/test_orchestrator_models.py`: test DecisionType all 5 values; LLMDecision valid construction; LLMDecision rejects invalid decision; LLMDecision rejects confidence <0 or >1; LLMDecision rejects missing required fields; OrchestratorState serialization round-trip; DecisionLogEntry serialization; EmailContext construction; DraftReply construction (~18 tests)

---

## Phase 3: US2 — Multi-LLM Provider Abstraction

**Story**: As a developer, I want to switch between LLM providers by changing only my `.env` file, so I am never locked into a single vendor.

**Checkpoint**: `pytest tests/unit/test_providers.py -v` — all 15 provider tests pass. `LLM_PROVIDER=anthropic python -c "from orchestrator.providers.registry import create_provider; p = create_provider(); print(p.provider_name())"` prints `anthropic`.

- [X] T008 [US2] Implement `orchestrator/providers/anthropic_adapter.py`: `AnthropicAdapter(LLMProvider)` using `anthropic.AsyncAnthropic(api_key=...)`, implementing `complete()` using `client.messages.create()` with dedicated `system` parameter, returning `(response.content[0].text, usage.input_tokens, usage.output_tokens)`. Default model `claude-sonnet-4-20250514`. Per plan.md Section 5.2.2.
- [X] T009 [P] [US2] Implement `orchestrator/providers/openai_compatible_adapter.py`: `OpenAICompatibleAdapter(LLMProvider)` using `openai.AsyncOpenAI(api_key=api_key, base_url=base_url)`, implementing `complete()` using `client.chat.completions.create()` with system role message, returning `(choices[0].message.content, usage.prompt_tokens, usage.completion_tokens)`. Parameterized by `base_url`, `api_key`, `model`, `provider_key`. Per plan.md Section 5.2.3.
- [X] T010 [US2] Implement `orchestrator/providers/registry.py`: define `PROVIDER_REGISTRY` dict mapping provider keys to adapter config (adapter type, api_key_env, default_model, base_url) for all 7 providers: anthropic, openai, gemini (`https://generativelanguage.googleapis.com/v1beta/openai/`), openrouter, qwen, glm, goose. Implement `create_provider() -> LLMProvider` that reads `LLM_PROVIDER` + `LLM_MODEL` from env, validates, and instantiates correct adapter. Raise `ValueError` with list of supported providers for unsupported key. Raise `ValueError` with "LLM_PROVIDER is set to [X] but [X_API_KEY] is not configured" for missing key. Per plan.md Section 5.2.4.
- [X] T011 [P] [US2] Update `orchestrator/__init__.py`: re-export `create_provider`, `LLMProvider`, `LLMDecision`, `EmailContext`, `OrchestratorState` for clean public API
- [X] T012 [US2] Write `tests/unit/test_providers.py`: AnthropicAdapter.complete() returns correct tuple with mocked AsyncAnthropic; OpenAICompatibleAdapter.complete() returns correct tuple with mocked AsyncOpenAI; create_provider() with LLM_PROVIDER=anthropic + ANTHROPIC_API_KEY; create_provider() with LLM_PROVIDER=gemini + GEMINI_API_KEY (verify base_url); create_provider() with missing LLM_PROVIDER; create_provider() with unsupported provider; create_provider() with missing API key env var; API key NOT in provider_name/model_name return values; LLM_MODEL override works; default model fallback per provider (~15 tests)

---

## Phase 4: US1 — Email Triage Decision (Core Loop)

**Story**: As a solo founder/CEO, I want my AI employee to read each actionable email and make an intelligent triage decision, so I spend zero time reading routine emails.

**Note**: US4 (Structured Prompting) implementation is architecturally inseparable from US1 — the JSON schema, correction prompt, and retry loop are all required for a working triage loop. US4-specific acceptance criteria are fully covered by implementing prompts.py and the retry mechanism here.

**Checkpoint**: Place a mock `.md` file with `status: pending` in `vault/Needs_Action/tmp_test.md`, run one poll cycle with mocked LLM response, verify: (1) frontmatter `status` changes, (2) `decision` field appears, (3) log entry in `vault/Logs/`. `pytest tests/unit/test_prompts.py tests/unit/test_vault_ops.py tests/unit/test_orchestrator.py -v` passes.

- [X] T013 [US1] Implement `orchestrator/prompts.py`: `build_system_prompt(decision_types: list[str]) -> str` — Ralph Wiggum system prompt defining agent role, 5 decision types with descriptions, EXACT JSON output schema (decision, confidence 0.0–1.0, reasoning, reply_body?), financial safety rule (payment/invoice/billing → urgent or needs_info NEVER archive), instruction to respond ONLY with JSON; `build_user_message(ctx: EmailContext) -> str` — formats email metadata + body for LLM input; `build_correction_prompt(original_response: str, error: str) -> str` — correction prompt for invalid JSON with original response included; `estimate_tokens(text: str) -> int` — approximate token count (chars/4); `truncate_body(body: str, max_tokens: int = 3000) -> str` — truncate with notice "[EMAIL TRUNCATED: original was N tokens]". Per plan.md Section 5.3.
- [X] T014 [P] [US1] Implement `orchestrator/vault_ops.py`: `scan_pending_emails(vault_path: Path) -> list[Path]` — glob `vault/Needs_Action/*.md`, parse YAML frontmatter, return paths with `status: pending`; `read_email_context(filepath: Path) -> EmailContext` — parse frontmatter + body into EmailContext; `update_frontmatter(filepath: Path, updates: dict) -> None` — load file, update YAML frontmatter fields (sort_keys=False to preserve order), atomic_write; `append_to_body(filepath: Path, text: str) -> None` — append text block to file body, atomic_write; `move_to_done(filepath: Path, vault_path: Path) -> Path` — move file to `vault/Done/`, return new path; `ensure_directory(dirpath: Path) -> None` — create directory if not exists; `write_draft_reply(vault_path: Path, draft: DraftReply) -> Path` — write draft markdown to `vault/Drafts/draft_{message_id}.md` with YAML frontmatter + reply body. Import `atomic_write`, `FileLock` from `watchers/utils.py`. Per plan.md Section 5.4.
- [X] T015 [US1] Implement `orchestrator/orchestrator.py`: `RalphWiggumOrchestrator` extending `BaseWatcher` from `watchers/base_watcher.py`. Implement: `validate_prerequisites()` — check LLM_PROVIDER, API key, vault dirs exist, create vault/Drafts/ if absent; `_load_state() / _save_state()` — OrchestratorState JSON to `vault/Logs/orchestrator_state.json`; `poll()` — override BaseWatcher poll: scan_pending_emails, skip already-processed IDs, call process_item for each; `process_item(filepath: Path)` — read email context, truncate body if needed, build prompts, call LLM, parse JSON into LLMDecision with Pydantic, apply decision (all 5 types: draft_reply → write draft + update status; needs_info → append note + update status; archive → update status + move to Done; urgent → update priority + write draft + update status; delegate → append delegation note + update status), update frontmatter with decision fields (decision, decision_reason, decided_by, decided_at, iteration_count), write log entry; Ralph Wiggum retry loop (max 5 iterations for invalid JSON/decision: send correction prompt, re-parse); handle FAILED state after 5 exhausted retries; signal handlers for SIGINT/SIGTERM graceful shutdown. Per plan.md Section 5.5.
- [X] T016 [US1] Write `tests/unit/test_prompts.py`: system prompt contains JSON schema; system prompt contains financial safety rule; user message includes sender/subject/body; token estimation within 20% of known count; truncation when over budget appends notice; no truncation when under budget; correction prompt includes original response; empty body handling (~12 tests). Write `tests/unit/test_vault_ops.py`: scan finds pending files; scan skips non-pending; read_email_context parses frontmatter + body; update_frontmatter preserves body; append_to_body adds text; move_to_done moves file; write_draft_reply creates file with correct frontmatter; ensure_directory creates dir; corrupt frontmatter logs warning and returns None (~14 tests)

---

## Phase 5: US3 — Draft Reply Generation

**Story**: As a solo founder/CEO, I want my AI employee to write a suggested reply for emails that need a response, saved locally in my vault for review.

**Note**: `write_draft_reply()` is already implemented in Phase 4 (T014). This phase validates the full US3 acceptance scenarios through dedicated tests and verifies the draft context (US3-SC2: draft contains enough context for human review).

**Checkpoint**: Place a mock email requiring a reply, run orchestrator with mocked LLM returning `{"decision": "draft_reply", "confidence": 0.9, "reasoning": "...", "reply_body": "Dear..."}`, verify `vault/Drafts/draft_{message_id}.md` exists with correct frontmatter and the original email shows `draft_path` pointing to it.

- [X] T017 [US3] Write `tests/unit/test_draft_reply.py`: DraftReply model has all required frontmatter fields (type, status, source_message_id, to, subject, drafted_by, drafted_at); draft filename uses message_id slug; draft subject prefixed "Re: " if not already; draft body contains reply_body from LLMDecision; original email frontmatter updated with draft_path; draft created for urgent decision as well; draft NOT created for archive/needs_info/delegate decisions (~10 tests)
- [X] T018 [P] [US3] Write `tests/unit/test_orchestrator_decisions.py`: process_item with draft_reply → draft exists + status=pending_approval + draft_path in frontmatter; process_item with needs_info → status=needs_info + note appended; process_item with archive → status=done + file moved to Done/; process_item with urgent → status=pending_approval + priority=urgent + draft exists; process_item with delegate → status=pending_approval + delegation note appended; all decisions write log entry; all decisions write decided_by/decided_at/decision fields to frontmatter (~12 tests)
- [X] T019 [US3] Verify `vault/Drafts/` auto-creation: write test confirming that if `vault/Drafts/` does not exist at startup, `validate_prerequisites()` creates it; confirm existing directory is not recreated (idempotent)

---

## Phase 6: US4 — Structured Prompting (Ralph Wiggum Principle)

**Story**: As a system architect, I want the LLM to receive structured prompts that constrain output to the exact JSON schema, so responses are predictable and parseable.

**Note**: The core structured prompting is implemented in T013 (prompts.py) and T015 (retry loop in orchestrator.py). This phase adds additional validation tests and confirms edge cases.

**Checkpoint**: Mock LLM to return invalid JSON 3 times then valid JSON on 4th attempt. Verify: (a) 3 correction prompts were sent, (b) final decision is correctly parsed, (c) log shows `iteration: 4`, (d) total retries do not exceed 5 (Ralph Wiggum limit).

- [X] T020 [US4] Write `tests/unit/test_ralph_wiggum_retry.py`: invalid JSON on first attempt → correction prompt sent; invalid JSON on all 5 attempts → email marked failed + log entry; valid JSON on 2nd attempt → success with iteration=2 in log; invalid decision value triggers retry; valid JSON with invalid decision value (e.g. "maybe") triggers retry; correction prompt includes original bad response; retry count tracked in OrchestratorState.error_counts (~10 tests)
- [X] T021 [P] [US4] Write `tests/unit/test_financial_safety.py`: system prompt contains financial safety keywords (payment, invoice, billing, subscription); system prompt explicitly states financial emails MUST be urgent or needs_info; verify build_system_prompt output includes the financial safety constraint text (~3 tests)
- [X] T022 [US4] Write `tests/unit/test_provider_normalization.py`: AnthropicAdapter and OpenAICompatibleAdapter both return identical `(text, int, int)` tuple shape; same system prompt + user message sent to both adapters (mock); both adapters' responses parse into valid LLMDecision via Pydantic; provider_name() and model_name() do NOT contain API key text (~5 tests)

---

## Phase 7: US5 — Audit Trail & Observability

**Story**: As an operator, I want every LLM decision logged with full context to `vault/Logs/`, so I can audit past decisions and debug failures.

**Note**: Log writing is already integrated into `orchestrator.py` (T015). This phase adds dedicated log format tests and state persistence verification.

**Checkpoint**: Run orchestrator for one cycle with 3 mock emails. Inspect `vault/Logs/orchestrator_YYYY-MM-DD.log` — verify 3 decision entries + 1 poll_cycle_complete entry, all parseable as JSONL. Verify `vault/Logs/orchestrator_state.json` contains processed_ids and decision_counts.

- [X] T023 [US5] Write `tests/unit/test_logging.py`: decision log entry contains all required fields (timestamp, event, provider, model, email_message_id, email_subject, decision, confidence, reasoning, tokens_input, tokens_output, latency_ms, iteration); error log entry contains severity=ERROR, error_type, error_message, retry_count; poll_cycle_complete entry contains emails_found, emails_processed, decision breakdown, total_latency_ms; log entries are valid JSONL (parseable with json.loads); API key NOT in any log field (~10 tests)
- [X] T024 [P] [US5] Write `tests/unit/test_state_persistence.py`: OrchestratorState serializes to JSON; OrchestratorState deserializes from JSON; processed_ids persisted across save/load; decision_counts incremented per decision; state file written to correct path `vault/Logs/orchestrator_state.json`; state loaded on orchestrator restart; corrupt state file handled gracefully (reset to empty state) (~8 tests)
- [X] T025 [US5] Verify log file naming `vault/Logs/orchestrator_YYYY-MM-DD.log` uses today's date; new log file created on date rollover (test with mocked datetime); poll cycles append to same daily log file; log entries are newline-delimited JSON (one JSON object per line)
- [X] T026 [P] [US5] Write `scripts/verify_llm_provider.py`: standalone script that loads `.env`, calls `create_provider()`, sends a single test message ("Say 'hello' and nothing else"), verifies response is non-empty, prints provider name + model + response + token counts. Exit 0 on success, exit 1 on error with message. This is the HT-009 verification script. Per plan.md Section 5.6.

---

## Phase 8: US6 — Orchestrator Lifecycle

**Story**: As a developer, I want the orchestrator to follow the same BaseWatcher lifecycle pattern and run alongside GmailWatcher without conflicts.

**Checkpoint**: Start orchestrator, verify it logs "Orchestrator started" + acquires lock at `vault/Logs/.orchestrator.lock`. Send SIGINT, verify it logs "Orchestrator shutdown complete" + releases lock + saves state. Attempt second instance while first is running → RuntimeError with "Another orchestrator instance is already running."

- [X] T027 [US6] Write `tests/unit/test_lifecycle.py`: start() calls validate_prerequisites() before polling; start() acquires file lock at vault/Logs/.orchestrator.lock; start() loads persisted state if state file exists; SIGINT triggers graceful shutdown (state saved + lock released + log written); SIGTERM also triggers shutdown; second instance raises RuntimeError; startup fails fast if LLM_PROVIDER not set; startup fails fast if API key missing; startup creates vault/Drafts/ if absent; startup fails if vault/Needs_Action/ does not exist (~12 tests)
- [X] T028 [US6] Write `tests/integration/test_lifecycle_integration.py`: start orchestrator with tmp vault + mocked LLM, place 2 mock emails, run one poll cycle, verify both processed + state saved; restart orchestrator (load saved state), place 1 new email, verify only new email processed (processed_ids loaded); concurrent instance prevention (acquire lock, attempt second start); watcher independence (orchestrator runs when no GmailWatcher is present)
- [X] T029 [P] [US6] Verify `orchestrator.py` extends `BaseWatcher` from `watchers/base_watcher.py`: import succeeds; RalphWiggumOrchestrator is subclass of BaseWatcher; `start()`, `stop()`, `poll()` methods present; `process_item(filepath: Path)` signature matches abstract method. Update `orchestrator/__init__.py` to export `RalphWiggumOrchestrator`.
- [X] T030 [US6] Verify GmailWatcher + orchestrator co-existence: both use SEPARATE lock files (`vault/Logs/.gmail_watcher.lock` and `vault/Logs/.orchestrator.lock`); file written by GmailWatcher to `vault/Needs_Action/` is readable by orchestrator's `scan_pending_emails()`; no circular imports between `watchers/` and `orchestrator/`
- [X] T031 [US6] Write `tests/integration/test_full_triage_cycle.py`: place 3 mock email files (1 requires reply, 1 archive, 1 needs_info) in tmp `vault/Needs_Action/`; run one poll cycle with mocked LLM returning appropriate decisions; verify: draft created in `vault/Drafts/`, archive moved to `vault/Done/`, needs_info frontmatter updated, 3 decision log entries + 1 poll_cycle_complete entry in `vault/Logs/orchestrator_YYYY-MM-DD.log`

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Integration coverage, error handling edge cases, full test suite run.

**Checkpoint**: `pytest tests/ -v --cov=orchestrator --cov-report=term-missing` — all tests pass, >85% coverage on `orchestrator/` package.

- [X] T032 Write `tests/integration/test_edge_cases.py`: Ralph Wiggum retry exhaustion (5 invalid JSON responses → status=failed + log); rate limit handling (mock 429 → backoff delay + resume); network timeout (mock 30s timeout → retry 3x with backoff → leave status=pending); corrupt YAML frontmatter → skip + warning log + next email processed; email body >4000 tokens → truncated + notice appended; financial email with `archive` decision → mocked LLM returns `archive`, verify orchestrator processes it (financial safety is a PROMPT constraint, not a post-hoc filter); state file save error → graceful log to stderr
- [X] T033 [P] Run full test suite and fix any failures: `pytest tests/ -v --cov=orchestrator --cov-report=term-missing --asyncio-mode=auto`; verify >85% coverage; verify 0 test failures; document any acceptable coverage gaps (e.g. __main__ block, signal handlers)
- [X] T034 [P] Final review: verify no hardcoded API keys in any file (`grep -r "sk-" orchestrator/ tests/`); verify `.env` variables documented in `README` or `ai-control/HUMAN-TASKS.md`; verify `vault/Drafts/.gitkeep` exists (directory committed but empty); verify `orchestrator/` has `__init__.py` at package root
- [X] T035 Update `ai-control/HUMAN-TASKS.md`: mark HT-009 DONE if not already (anthropic SDK installed globally, ANTHROPIC_API_KEY in .env); add HT-010 "Run verify_llm_provider.py to confirm LLM connectivity: `python scripts/verify_llm_provider.py`"

---

## Dependencies Graph

```
Phase 1 (Setup)
    └── Phase 2 (Foundational: models + provider ABC)
            ├── Phase 3 (US2: Provider adapters + registry)
            │       └── Phase 4 (US1: Prompts + VaultOps + Orchestrator core)
            │               ├── Phase 5 (US3: Draft reply tests + validation)
            │               ├── Phase 6 (US4: Retry + financial safety tests)
            │               ├── Phase 7 (US5: Logging + state persistence)
            │               └── Phase 8 (US6: Lifecycle + integration)
            │                       └── Phase 9 (Polish: full integration + coverage)
            └── (Phase 4 can start after Phase 3 AND Phase 2)
```

**Story dependencies**:
- US2 → must complete before US1 (triage needs a provider to call)
- US1 → enables US3, US4, US5, US6 (all share orchestrator.py)
- US3, US4, US5, US6 → independent of each other (different files/tests), can be verified in any order after US1

**Parallel opportunities** (same phase, different files):
- T003 + T004: directory setup, both in Phase 1
- T006 + T007: providers/base.py + test_orchestrator_models.py
- T008 + T009: AnthropicAdapter + OpenAICompatibleAdapter
- T013 + T014: prompts.py + vault_ops.py (Phase C, no inter-dependency)
- T017 + T018: test_draft_reply.py + test_orchestrator_decisions.py
- T020 + T021 + T022: retry + financial + normalization tests
- T023 + T024: logging + state persistence tests
- T026 + T029: verify_llm_provider.py + orchestrator export
- T033 + T034: test run + security scan

---

## Implementation Strategy (MVP First)

**MVP = US1 + US2** (Phases 1–4): An orchestrator that reads pending emails and makes triage decisions using configurable LLM providers.

**MVP verification**: After T016, run:
```bash
# Set up env
echo "LLM_PROVIDER=anthropic" >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# Run verify script
python scripts/verify_llm_provider.py

# Place test email
cp vault/Needs_Action/some_email.md /tmp/test_email.md

# Run one cycle (manual test)
python -m orchestrator
```

**Incremental delivery after MVP**:
1. MVP: Email triage working (US1+US2) → **demonstrable value**
2. + Draft replies (US3) → highest-value output, saves real time
3. + Retry robustness (US4) → system reliability
4. + Full audit trail (US5) → operational visibility
5. + Lifecycle polish (US6) → production-ready alongside GmailWatcher

---

## Test Coverage Summary

| Phase | Test File | Count | Tests |
|-------|-----------|-------|-------|
| 2 | `tests/unit/test_orchestrator_models.py` | ~18 | Pydantic model validation |
| 3 | `tests/unit/test_providers.py` | ~15 | Provider adapters + factory |
| 4 | `tests/unit/test_prompts.py` | ~12 | Prompt construction |
| 4 | `tests/unit/test_vault_ops.py` | ~14 | Vault file operations |
| 5 | `tests/unit/test_draft_reply.py` | ~10 | Draft generation |
| 5 | `tests/unit/test_orchestrator_decisions.py` | ~12 | All 5 decision types |
| 6 | `tests/unit/test_ralph_wiggum_retry.py` | ~10 | Retry loop |
| 6 | `tests/unit/test_financial_safety.py` | ~3 | Financial constraint |
| 6 | `tests/unit/test_provider_normalization.py` | ~5 | Cross-provider schema |
| 7 | `tests/unit/test_logging.py` | ~10 | Log format + content |
| 7 | `tests/unit/test_state_persistence.py` | ~8 | State save/load |
| 8 | `tests/unit/test_lifecycle.py` | ~12 | Start/stop/lock |
| 8 | `tests/integration/test_lifecycle_integration.py` | ~4 | Integration lifecycle |
| 8 | `tests/integration/test_full_triage_cycle.py` | ~1 | End-to-end cycle |
| 9 | `tests/integration/test_edge_cases.py` | ~8 | Error paths |
| **Total** | **15 test files** | **~142 tests** | |

**Coverage target**: >85% on `orchestrator/` package
**Acceptable gaps**: `__main__` block, signal handler registration, `scripts/verify_llm_provider.py`

---

## Format Validation

All 35 tasks confirmed to follow strict checklist format:
- ✅ `- [ ]` checkbox prefix
- ✅ T001–T035 sequential IDs
- ✅ `[P]` markers on parallelizable tasks
- ✅ `[USN]` labels on all user story phase tasks (Phases 3–8)
- ✅ Exact file paths in every description
- ✅ Setup/Foundational phases have NO story labels
- ✅ Polish phase has NO story labels
