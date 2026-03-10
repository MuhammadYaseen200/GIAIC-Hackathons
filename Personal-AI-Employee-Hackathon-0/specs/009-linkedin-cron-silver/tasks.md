# Tasks: LinkedIn Auto-Poster + Cron Scheduling

**Input**: Design documents from `specs/009-linkedin-cron-silver/`
**Branch**: `009-linkedin-cron-silver` | **Date**: 2026-03-05
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Organization**: Tasks grouped by user story for independent implementation and testing.
**Tests**: Included per SC-008 (>80% coverage required by spec).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared state dependencies)
- **[Story]**: Maps to User Story in spec.md (US1=P1, US2=P2 daily, US3=P2 cron, US4=P3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create LinkedIn MCP directory structure, verify dependencies, prepare vault directories.

- [X] T001 Create `mcp_servers/linkedin/` directory with empty `__init__.py`
- [X] T002 [P] Add `linkedin_token.json` to `.gitignore` (alongside `token.json` and `calendar_token.json`)
- [X] T003 [P] Verify `httpx>=0.27.0` in `requirements.txt` — add if missing
- [X] T004 [P] Create `vault/Config/` directory (vault setup for topic file — empty dir with `.gitkeep`)

**Checkpoint**: Directory structure exists, .gitignore updated, dependencies confirmed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: LinkedIn MCP models, OAuth2 auth module, API client, and auth setup script. All User Stories depend on these.

**⚠️ CRITICAL**: No User Story work can begin until this phase is complete.

- [X] T005 Implement `mcp_servers/linkedin/models.py` — Pydantic v2 models: `PostUpdateInput(text: str, visibility: Literal["PUBLIC","CONNECTIONS"]="PUBLIC")`, `PostUpdateResult`, `ProfileResult`, `HealthCheckResult` per `contracts/linkedin_mcp_tools.md`
- [X] T006 Implement `mcp_servers/linkedin/auth.py` — OAuth2 token lifecycle: `load_token()`, `save_token()` (atomic via `watchers/utils.atomic_write`), `refresh_token()` (POST `/oauth/v2/accessToken` with `grant_type=refresh_token`), `get_credentials()` singleton (module-level `_credentials` cache), `reset_credentials_cache()` for test isolation; raise `AuthRequiredError` if refresh fails (ADR-0014)
- [X] T007 [P] Implement `mcp_servers/linkedin/client.py` — `LinkedInClient` class: `post_update(text, visibility)` → `POST /v2/ugcPosts` (UGC Posts API), `get_profile()` → `GET /v2/me`, both use `httpx.AsyncClient` with `Authorization: Bearer` header; auto-refresh on `401` by calling `auth.refresh_token()` then retrying once; raise `LinkedInAPIError` on non-2xx after retry
- [X] T008 Create `scripts/linkedin_auth.py` — OAuth2 Authorization Code flow: build auth URL with scopes `r_liteprofile w_member_social offline_access`, open browser (`webbrowser.open`), start local HTTP server on port 8765 to capture `code`, exchange code for tokens via `POST /v2/accessToken`, fetch `GET /v2/me` for person_urn, save `linkedin_token.json` with `{access_token, refresh_token, expires_at, token_type, person_urn}`; print `✅ Saved linkedin_token.json. person_urn: urn:li:person:...`

**Checkpoint**: Foundation ready — `mcp_servers/linkedin/` has 4 modules with auth and client implemented.

---

## Phase 3: User Story 1 — LinkedIn Post Drafted and Approved via WhatsApp (Priority: P1) 🎯 MVP

**Goal**: Owner triggers a draft → Privacy Gate checks content → AI drafts post → WhatsApp approval notification → owner replies "approve" → published to LinkedIn within 60s; or "reject"/24h timeout → moved to Rejected/.

**Independent Test**: Run `python3 orchestrator/linkedin_poster.py --draft "building AI agents"`, receive WhatsApp notification with topic+preview+path, reply "approve", verify entry in `vault/Logs/linkedin_posts.jsonl` with `status=published` within 60s.

### Contract Tests for User Story 1

> **Write tests FIRST — verify they FAIL before implementation (T011)**

- [X] T009 [P] [US1] Write contract tests `tests/test_linkedin_mcp.py`: mock `httpx.AsyncClient` — test all 6 `post_update` cases + 3 `get_profile` cases + 4 `health_check` cases from `contracts/linkedin_mcp_tools.md`; include auto-refresh test (mock 401 → mock refresh success → mock post success)
- [X] T010 [P] [US1] Write unit tests `tests/test_linkedin_poster.py`: mock PrivacyGate, HITLManager, linkedin_mcp tools — test state transitions: `drafted`, `approved`, `rejected`, `expired`, `privacy_blocked`, `rate_limited`; verify HITL invariant (no publish without approve)

### Implementation for User Story 1

- [X] T011 [US1] Implement `mcp_servers/linkedin/server.py` — FastMCP server: `@mcp.tool() async def post_update(text, visibility)`, `get_profile()`, `health_check()`; each calls `LinkedInClient`; returns success dict or `{"isError": true, "content": json.dumps({...})}`; `if __name__ == "__main__": mcp.run()` (mirrors `mcp_servers/calendar/server.py` pattern, ADR-0005)
- [X] T012 [US1] Implement `orchestrator/linkedin_poster.py` core — `draft_and_queue(topic: str)` function: (1) `PrivacyGate().check(topic)` → if blocked log `privacy_blocked` to `linkedin_posts.jsonl`, return; (2) call orchestrator LLM to draft 150-300 word professional post; (3) `PrivacyGate().check(post_text)` → if blocked log, return; (4) check daily rate limit via `linkedin_posts.jsonl` (count `status=published` entries for today) → if ≥1 log `rate_limited`, send WhatsApp queue notice, return
- [X] T013 [US1] Implement `orchestrator/linkedin_poster.py` vault write — after rate limit check passes: write `vault/Pending_Approval/<date>_linkedin_<slug>.md` with YAML frontmatter per `data-model.md` LinkedInDraft schema (type, topic, visibility, status=pending, created, expires=+24h, content_hash, agent=linkedin_poster); log `event=drafted` to `vault/Logs/linkedin_posts.jsonl`
- [X] T014 [US1] Implement `orchestrator/linkedin_poster.py` WhatsApp notification — after vault write: call `mcp_servers/whatsapp` bridge `send_message()` with enriched format (FR-005): `"[LinkedIn Draft]\nTopic: {topic}\nType: linkedin_post\n\nPreview:\n{text[:300]}...\n\nLinks: {links or 'None'}\nFull draft: vault/Pending_Approval/{filename}\n\nReply 'approve' or 'reject'"`; handle `MCPUnavailableError` gracefully (draft stays pending, log warning)
- [X] T015 [US1] Implement `orchestrator/linkedin_poster.py` approval processing — `process_approved(draft_file: Path)` function: read draft file, call `linkedin_mcp.post_update(text, visibility)` via `orchestrator/mcp_client.py`; on success: log `event=published` with `post_urn` to `linkedin_posts.jsonl`, move draft file to `vault/Done/`; on failure: log `event=failed`, send WhatsApp error notification
- [X] T016 [US1] Implement `orchestrator/linkedin_poster.py` rejection/expiry — `process_rejected(draft_file, reason)` function: update frontmatter `status=rejected/expired`, move to `vault/Rejected/`, log `event=rejected/expired` to `linkedin_posts.jsonl`; add expiry check: if `expires < now()` and status still pending → call `process_rejected(..., "expired")`
- [X] T017 [US1] Add `--draft "topic"` CLI entrypoint to `orchestrator/linkedin_poster.py` — `if __name__ == "__main__": argparse` with `--draft TOPIC` arg; calls `draft_and_queue(topic)`; `--process-approvals` arg for checking pending vault files (called by orchestrator every 15min)
- [X] T018 [US1] Verify T009/T010 tests now PASS with implementation complete; fix any failures

**Checkpoint**: `python3 orchestrator/linkedin_poster.py --draft "test"` → WhatsApp notification received → "approve" → published. SC-001 ✅ SC-002 ✅ SC-003 ✅

---

## Phase 4: User Story 2 + 3 — Daily Auto-Draft + Orchestrator Cron (Priority: P2)

### US2 — Daily LinkedIn Post Drafted Automatically

**Goal**: LinkedIn post drafted once per day from topic file, sent for approval, no manual trigger required.

**Independent Test**: Set `CRON_LINKEDIN_TIME` to 2 minutes from now, wait for WhatsApp notification with auto-drafted post, verify `vault/Pending_Approval/` contains the draft file.

- [X] T019 [P] [US2] Write unit test for `--auto` mode in `tests/test_linkedin_poster.py`: mock topic file read, mock random.choice, verify `draft_and_queue()` called with correct topic; mock missing topic file → verify fallback to 4 defaults
- [X] T020 [US2] Create `vault/Config/linkedin_topics.md` with 6 default topics (AI learning, web dev, freelance, hackathons, Python automation, Personal AI Employee lessons) per `research.md` D4 format
- [X] T021 [US2] Implement `--auto` mode in `orchestrator/linkedin_poster.py`: read `vault/Config/linkedin_topics.md` (parse `-` prefixed lines as topics), `random.choice(topics)` for today's topic; if file missing → use 4 built-in defaults (FR-017); calls `draft_and_queue(topic)`
- [X] T022 [US2] Implement daily rate limit guard in `draft_and_queue()`: before drafting, count `linkedin_posts.jsonl` entries where `status=published` AND `date == today (UTC date)`; if ≥1 → log `event=rate_limited`, send WhatsApp notice "Daily LinkedIn post already published today. Next slot: tomorrow at {CRON_LINKEDIN_TIME}.", return without drafting

### US3 — Orchestrator Runs on Cron Every 15 Minutes

**Goal**: Cron daemon runs orchestrator every 15 min and LinkedIn drafter daily; lock file prevents overlap.

**Independent Test**: Run `scripts/setup_cron.sh` three times, verify `crontab -l | grep H0_CRON_MANAGED | wc -l` == 2. Place test item in `vault/Needs_Action/`, verify processed within 15 min.

- [X] T023 [P] [US3] Write bash smoke test `tests/test_cron_scripts.sh`: run `setup_cron.sh` 3x → assert 2 H0_CRON_MANAGED entries; run `remove_cron.sh` → assert 0 entries; verify setup_cron.sh completes in <5s (SC-006, SC-007)
- [X] T024 [US3] Create `scripts/setup_cron.sh` — idempotent cron installer per `research.md` D6: detect `PROJECT_ROOT` via `$(cd "$(dirname "$0")/.." && pwd)`, load `CRON_LINKEDIN_TIME` from `.env` (default `0 9`), build orchestrator and linkedin drafter crontab entries with `# H0_CRON_MANAGED` suffix, replace all existing H0_CRON_MANAGED entries atomically with `(crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED"; echo "$ORCH"; echo "$LINKEDIN") | crontab -`; print `✅ Cron entries installed.`
- [X] T025 [US3] Create `scripts/remove_cron.sh` — one-liner: `(crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED") | crontab -`; print `✅ H0 cron entries removed.`; `chmod +x` both scripts
- [X] T026 [US3] Add lock file guard to `orchestrator/orchestrator.py` (3 lines at top of `main()`): `import fcntl; _lock = open("/tmp/h0_orchestrator.lock", "w"); fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)` wrapped in `try/except BlockingIOError: sys.exit(0)` — prevents duplicate concurrent runs (edge case 6 in spec)
- [X] T027 [US3] Wire `orchestrator/orchestrator.py` to call `linkedin_poster.py --process-approvals` at end of each orchestrator run — checks pending LinkedIn drafts in `vault/Pending_Approval/` for expired items and processes any owner-approved files
- [X] T028 [US3] Verify bash smoke tests pass: run T023 tests → `setup_cron.sh` idempotency confirmed (SC-007), entries format correct

**Checkpoint**: `./scripts/setup_cron.sh && crontab -l` shows 2 H0_CRON_MANAGED entries. `--auto` drafts from topic file. SC-005 ✅ SC-006 ✅ SC-007 ✅

---

## Phase 5: User Story 4 — Vault-Triggered LinkedIn Post from Needs_Action (Priority: P3)

**Goal**: Any component writes `type: linkedin_post` to `vault/Needs_Action/`; orchestrator routes through LinkedIn HITL workflow within 15 minutes.

**Independent Test**: Write `vault/Needs_Action/test_linkedin.md` with `type: linkedin_post` and `content: "milestone reached"` frontmatter. Wait ≤15 minutes. Verify WhatsApp approval request received and trigger file moved to `vault/Done/`.

- [X] T029 [P] [US4] Write unit test in `tests/test_linkedin_poster.py`: mock vault item with `type=linkedin_post` → verify `draft_and_queue()` called with correct content topic; mock `#linkedin` tag → verify same routing
- [X] T030 [US4] Extend `orchestrator/orchestrator.py` classifier to detect `type: linkedin_post` in `vault/Needs_Action/` item YAML frontmatter → route to `linkedin_poster.draft_and_queue(item.content)` → move trigger file to `vault/Done/` after queuing
- [X] T031 [US4] Extend `orchestrator/orchestrator.py` classifier to detect `#linkedin` tag in item body → same routing as T030; add test coverage for both detection paths

**Checkpoint**: Vault item routing works end-to-end. SC-005 verified with vault trigger path. US4 independently testable.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: MCP registry update, security verification, coverage gate, documentation.

- [X] T032 Update `ai-control/MCP.md` — move `linkedin_mcp` row from "Needed MCP Servers" table to "Project-Custom MCP Servers" table; add: server=linkedin_mcp, purpose, tools=post_update/get_profile/health_check, path=mcp_servers/linkedin/server.py, health_check command, phase=5.5
- [X] T033 [P] Run security scan: verify `linkedin_token.json` in `.gitignore`, no tokens present in `vault/Logs/linkedin_posts.jsonl` entries, no credentials in cron.log output; run `grep -r "access_token\|refresh_token\|client_secret" vault/` → expect 0 matches (FR-009, SC-009)
- [X] T034 Run `pytest tests/test_linkedin_mcp.py tests/test_linkedin_poster.py --cov=mcp_servers/linkedin --cov=orchestrator/linkedin_poster --cov-report=term-missing` → verify coverage >80% (SC-008) — ACHIEVED 99% as of 2026-03-10
- [X] T035 [P] Update `specs/overview.md` Phase 5.5 SDD Cycle Status: mark spec ✅, clarifications ✅, ADRs ✅, plan ✅, tasks ✅ (implementation and QA marked after /sp.implement completes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1, T001-T004)**: No dependencies — start immediately
- **Foundational (Phase 2, T005-T008)**: Depends on Phase 1 — blocks all User Stories
- **US1 (Phase 3, T009-T018)**: Depends on Phase 2 — implements core HITL workflow (MVP)
- **US2+US3 (Phase 4, T019-T028)**: Depends on Phase 2; US2 builds on US1 `draft_and_queue()`; US3 independent
- **US4 (Phase 5, T029-T031)**: Depends on Phase 3 US1 (reuses `draft_and_queue()`)
- **Polish (Phase 6, T032-T035)**: Depends on all User Stories complete

### User Story Dependencies

- **US1 (P1)**: Foundational complete → implements core MCP + poster workflow → MVP
- **US2 (P2)**: US1 complete (reuses `draft_and_queue()`), adds topic file + auto mode
- **US3 (P2)**: Foundational complete, independent of US1/US2 (cron scripts are separate)
- **US4 (P3)**: US1 complete (reuses `draft_and_queue()`), adds vault classifier routing

### Within Each Phase

- Contract/unit tests FIRST → verify they FAIL → implement → verify they PASS
- Models (T005) → Auth (T006) → Client (T007) → Server (T011)
- Server (T011) → Poster draft (T012-T013) → Notification (T014) → Approval (T015-T016)
- Commit after each logical group (T011, T012-T014, T015-T017, etc.)

### Parallel Opportunities

- T002, T003, T004 parallel with T001 (different files)
- T007 parallel with T006 (client.py independent of auth.py at write-time; imports auth at runtime)
- T009, T010 parallel (different test files; can write before implementation)
- T019, T023 parallel (different test files)
- T020, T024, T025 parallel (different files: topic file, cron scripts)
- T033, T035 parallel in Polish phase

---

## Parallel Example: User Story 1 (MVP Sprint)

```bash
# Round 1 — write tests first (parallel):
Task A: "Write contract tests tests/test_linkedin_mcp.py"    [T009]
Task B: "Write unit tests tests/test_linkedin_poster.py"      [T010]

# Round 2 — implement server (after T005-T008 foundation):
Task: "Implement mcp_servers/linkedin/server.py"              [T011]

# Round 3 — implement poster workflow (parallel blocks):
Task A: "Implement draft_and_queue() core logic"              [T012]
Task B: "Implement vault write + frontmatter"                 [T013]

# Round 4 — sequential (each depends on previous):
Task: "Implement WhatsApp notification"                        [T014]
Task: "Implement approval processing"                          [T015]
Task: "Implement rejection/expiry"                             [T016]
Task: "Add --draft CLI entrypoint"                             [T017]
```

---

## Implementation Strategy

### MVP First (User Story 1 Only — Phase 1+2+3)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005–T008) — BLOCKS all stories
3. Complete Phase 3: US1 HITL workflow (T009–T018)
4. **STOP and VALIDATE**: `python3 orchestrator/linkedin_poster.py --draft "test"` → WhatsApp → approve → published
5. Run `pytest tests/test_linkedin_mcp.py tests/test_linkedin_poster.py` → all PASS
6. **MVP DONE**: LinkedIn posting with HITL approval works

### Incremental Delivery

1. Setup + Foundational → LinkedIn MCP server testable
2. US1 → Core HITL workflow → **Demo-ready** (manual trigger + approval)
3. US2 → Topic file + daily auto-draft → Fully automated posting
4. US3 → Cron scripts → Truly autonomous (no manual trigger needed)
5. US4 → Vault trigger → Extensible (any component can request a post)
6. Polish → Production-ready with coverage + registry + security check

---

## Notes

- **HT-013b** (human task): Run `scripts/linkedin_auth.py` after T008 to generate `linkedin_token.json` — required before any LinkedIn API calls
- `[P]` tasks = different files, no shared state conflicts at write time
- `[Story]` label maps each task to spec.md user story for traceability
- Commit after each phase checkpoint at minimum
- HITL invariant (SC-003): zero posts without explicit "approve" — enforced at `process_approved()` level, never bypassed
- All LinkedIn API calls MUST go through `mcp_servers/linkedin/server.py` tools (Constitution Principle IV)
