# Tasks: CEO Briefing + Odoo Gold Tier

**Branch**: `010-ceo-briefing-odoo-gold` | **Date**: 2026-03-11
**Spec**: `specs/010-ceo-briefing-odoo-gold/spec.md` (8 User Stories, 30 FRs, 12 SCs)
**Plan**: `specs/010-ceo-briefing-odoo-gold/plan.md` (Phases A–L)
**ADRs**: 0016 (Odoo protocol), 0017 (Social MCP arch), 0018 (Ralph Wiggum), 0019 (LLM fallback)
**Working Directory**: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0` ← ONLY VALID DIR

---

## Governance (Pre-Implementation Checklist)

```
[X] 1. loop-controller gate: spec.md (30 FRs, 12 SCs) + plan.md + ADRs 0016-0019 COMPLETE
[X] 2. path-warden: invoke after every new file write
[X] 3. qa-overseer: invoke after Phase 5 MVP (US1 daily briefing working)
[ ] 4. security-scan skill: before every commit — no hardcoded tokens
[ ] 5. Constitution check: all 10 principles PASS (see plan.md)
```

## Agent Team Assignment

```
Lead (main session)
├── @loop-controller      → Phase gate enforcer (FIRST on every phase)
├── @path-warden          → After every file write
├── @qa-overseer          → After Phase 5 (US1 MVP)
├── @security-scan skill  → Before every commit
│
├── teammate-1: backend-builder  → Phase 1 + Phase 2 (Setup + Odoo MCP)
├── teammate-2: backend-builder  → Phase 3 + Phase 4 (Facebook/Instagram + Twitter MCPs) [parallel with teammate-1]
├── teammate-3: backend-builder  → Phase 5 + Phase 6 (Daily Briefing + Weekly Audit)
└── teammate-4: backend-builder  → Phase 7 + Phase 8 + Phase 9 + Phase 10 (Skills + Polish + QA)
```

**Spawn command** (in tmux, agent teams enabled):
```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude
# Team name: phase6-gold | Spawn order: teammate-1 first, teammate-2 parallel,
# teammate-3 after teammate-1 done, teammate-4 after Phase 6 MVP qa-overseer PASS
```

---

## Phase 1: Setup (T001–T009)

**Purpose**: Initialize all new directories, dependencies, vault config, and gitignore additions.
Unblocked — start immediately.

- [X] T001 Create MCP server directories: `mcp_servers/odoo/`, `mcp_servers/facebook/`, `mcp_servers/twitter/`, `tests/unit/`, `tests/integration/`, `tests/contract/`, `docs/` using `mkdir -p`
- [X] T002 Create `__init__.py` placeholders: `mcp_servers/odoo/__init__.py`, `mcp_servers/facebook/__init__.py`, `mcp_servers/twitter/__init__.py`
- [X] T003 Add to `.gitignore`: tokens `facebook_token.json`, `twitter_token.json`; social config `vault/Config/social_keywords.md`; verify with `grep -n "facebook_token" .gitignore`
- [X] T004 Add `tweepy>=4.14.0` to `requirements.txt` — the only new pip dependency (Odoo uses plain httpx; Meta Graph API uses plain httpx)
- [X] T005 Add new env var templates to `.env.example`: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_PAGE_ID, FACEBOOK_PAGE_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID, TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET, TWITTER_BEARER_TOKEN, CRON_BRIEFING_TIME, CRON_WEEKLY_AUDIT_DAY
- [X] T006 Create `vault/Config/social_keywords.md` with DM monitoring keywords: job, hire, freelance, client, project, collaboration, collab, urgent, contract, offer, opportunity, payment, invoice, business
- [X] T007 [P] Create MCP contract JSON schemas: `tests/contract/odoo-mcp-tools.json`, `tests/contract/facebook-mcp-tools.json`, `tests/contract/twitter-mcp-tools.json` — each documenting tool name, input schema, output schema
- [X] T008 [P] Update `specs/overview.md`: Phase 6 status `NOT_STARTED` → `IN_PROGRESS`; add Phase 6 deliverables list
- [X] T009 Verify directory guard in all new orchestrator scripts: `PROJECT_ROOT` must start with `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`

**Checkpoint**: ✅ COMPLETE — All directories exist, deps updated, vault config seeded.

---

## Phase 2: Foundational — Odoo MCP Server (T010–T026)

**Purpose**: Build the Odoo JSON-RPC MCP server. Blocks US1 (daily briefing), US2 (weekly audit), and US5 (Odoo financial data). Must be complete before Phase 5.

**US mapping**: Foundational (no story label) — feeds US1, US2, US5.

> **TDD required** (Constitution Principle V): Contract tests MUST be written RED before `server.py` is implemented.

- [X] T010 Create `mcp_servers/odoo/models.py` — Pydantic v2 models: `GLSummary(by_type: dict[str, float])`, `ARPartner(name: str, amount: float, days_overdue: int)`, `ARAgingResult(current: float, overdue_30_60: float, overdue_61_90: float, bad_debt_90plus: float, partners: list[ARPartner])`, `InvoiceResult(invoice_id: int, partner_name: str, amount: float, due_date: str, days_remaining: int)`, `OdooHealthResult(healthy: bool, odoo_version: str, db_name: str, error: str | None)`
- [X] T011 Create `mcp_servers/odoo/auth.py` — session singleton: `OdooAuthError(Exception)`, `get_odoo_session() -> str` (POST `/web/session/authenticate` → returns session_id cookie), `reset_session_cache()`, in-memory singleton (not disk — sessions live ~1h); env vars: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD
- [X] T012 Create `mcp_servers/odoo/client.py` — async httpx JSON-RPC adapter: `_rpc_payload(model, method, domain, fields) -> dict`, `async def get_gl_summary() -> dict`, `async def get_ar_aging() -> dict`, `async def get_invoices_due(days: int = 7) -> list`, `async def health_check_odoo() -> dict`; URL: `{ODOO_URL}/web/dataset/call_kw`; 401 triggers `reset_session_cache()` + one retry; raises `OdooConnectionError` on network failure
- [X] T013 [P] Write contract tests RED in `tests/unit/test_odoo_mcp.py` (12 tests total): `test_get_gl_summary_success`, `test_get_gl_summary_groups_by_type`, `test_get_ar_aging_four_buckets`, `test_get_ar_aging_odoo_down`, `test_get_invoices_due_success`, `test_get_invoices_due_filters_7_days`, `test_health_check_healthy`, `test_health_check_unreachable`, `test_health_check_auth_error`, `test_gl_summary_graceful_on_401`, `test_all_tools_return_dict_not_raise`, `test_session_resets_on_401` — ✅ 12/12 GREEN
- [X] T014 [P] Write integration test skeleton in `tests/integration/test_odoo_live.py` — 3 tests marked `@pytest.mark.integration` (skipped unless `ODOO_LIVE=1`): `test_live_gl_summary`, `test_live_ar_aging`, `test_live_health_check`
- [X] T015 Create `mcp_servers/odoo/server.py` — FastMCP server (mirrors `mcp_servers/linkedin/server.py` pattern): 4 tools `@mcp.tool()`: `get_gl_summary`, `get_ar_aging`, `get_invoices_due(days_ahead: int = 7)`, `health_check`; each returns `{"content": json.dumps(...)}` or `{"isError": True, "content": json.dumps({"error": "..."})}` on failure
- [X] T016 Run `pytest tests/unit/test_odoo_mcp.py` — ✅ 12/12 tests GREEN
- [X] T017 Create `specs/010-ceo-briefing-odoo-gold/data-model.md` — document: GL account types (income/expense/asset/liability), AR aging bucket definitions, invoice lifecycle states (draft→posted→paid/cancelled), Odoo session auth flow diagram
- [X] T018 Update `ai-control/MCP.md` — `odoo_mcp` row added to Project-Custom MCP Servers table (#6)
- [X] T019 Add `odoo_mcp` config block to `~/.claude.json` — registered via `claude mcp add` (human verified 2026-03-12)
- [X] T020 Verify Odoo MCP via `/mcp` command — `odoo_mcp` appears in connected servers list (human verified 2026-03-12)

**Checkpoint**: ✅ COMPLETE — Odoo MCP server live with 12/12 passing tests.

---

## Phase 3: US3 — Facebook + Instagram MCP + Social Poster (T021–T034)

**User Story**: US3 — Facebook + Instagram: Post and Summarise (P2)
**Goal**: Both platforms can receive HITL-approved posts and return recent post summaries for the CEO briefing.
**Independent Test**: `python3 -c "from mcp_servers.facebook.server import health_check; import asyncio; print(asyncio.run(health_check()))"` — returns structured result (healthy or auth error, never raises).
**Blocked on**: HT-014 (Facebook Page + Developer App) and HT-015 (Instagram Business Account) for live testing. Unit tests with mocks run immediately.

> **TDD required**: Contract tests RED before server.py.

- [X] T021 [P] [US3] Create `mcp_servers/facebook/models.py` — Pydantic v2: `FacebookPostInput(text: str, visibility: Literal["EVERYONE","FRIENDS"] = "EVERYONE")`, `InstagramMediaInput(caption: str, image_url: str | None = None)`, `PostResult(success: bool, post_id: str | None, url: str | None, platform: str, error: str | None)`, `RecentPost(post_id: str, message: str, created_time: str, platform: str)`, `RecentPostsResult(success: bool, posts: list[RecentPost], error: str | None)`, `FacebookHealthResult(healthy: bool, page_reachable: bool, token_valid: bool, error: str | None)`
- [X] T022 [P] [US3] Create `mcp_servers/facebook/client.py` — async httpx Meta Graph API adapter: `GRAPH_API_BASE = "https://graph.facebook.com"`, `async def post_to_facebook(text: str) -> dict` (POST `/{PAGE_ID}/feed`), `async def post_to_instagram(caption: str, image_url: str | None) -> dict` (2-step: POST `/{IG_ACCOUNT_ID}/media` → `/{IG_ACCOUNT_ID}/media_publish`), `async def get_recent_facebook_posts(limit: int = 10) -> list`, `async def health_check_meta() -> bool`; auth via `FACEBOOK_PAGE_ACCESS_TOKEN` env var; character limit enforcement (FR-021): Facebook ≤63206, Instagram ≤2200
- [X] T023 [P] [US3] Write contract tests RED in `tests/unit/test_facebook_mcp.py` (14 tests) — ✅ 14/14 GREEN
- [X] T024 [US3] Create `mcp_servers/facebook/server.py` — FastMCP with 5 tools: `post_update`, `post_facebook_only`, `post_instagram_only`, `get_recent_posts`, `health_check`
- [X] T025 [US3] Run `pytest tests/unit/test_facebook_mcp.py` — ✅ 14/14 GREEN
- [X] T026 [US3] Create `orchestrator/social_poster.py` — cross-platform posting workflow extending `linkedin_poster.py` pattern; JSONL logging to `vault/Logs/social_posts.jsonl`; character limit enforcement per platform
- [X] T027 [US3] `facebook_mcp` added to `ai-control/MCP.md` Project-Custom table (#7)
- [X] T028 [US3] Add `facebook_mcp` config block to `~/.claude.json` — DONE: HT-017 completed (2026-03-13)

**Checkpoint**: ✅ PARTIAL — Facebook/Instagram MCP + social poster functional (14/14 mocked tests pass). Live testing blocked on HT-017.

---

## Phase 4: US4 — Twitter/X MCP + Social Poster Extension (T029–T040)

**User Story**: US4 — Twitter/X: Post and Summarise (P2)
**Goal**: Tweets can be drafted, HITL-approved, and published; recent tweets summarised in briefing.
**Independent Test**: `python3 -c "from mcp_servers.twitter.server import health_check; import asyncio; print(asyncio.run(health_check()))"` — returns structured result.
**Blocked on**: HT-016 (Twitter/X Developer App) for live testing. Unit tests run immediately.
**Parallel with**: Phase 3 (teammate-2 runs both).

> **TDD required**: Contract tests RED before server.py.

- [X] T029 [P] [US4] Create `mcp_servers/twitter/models.py` — Pydantic v2: `TweetInput(text: str)` with validator `len(text) <= 280`, `TweetResult(success: bool, tweet_id: str | None, url: str | None, error: str | None)`, `RecentTweet(tweet_id: str, text: str, created_at: str)`, `RecentTweetsResult(success: bool, tweets: list[RecentTweet], error: str | None)`, `TwitterHealthResult(healthy: bool, token_valid: bool, api_reachable: bool, error: str | None)`
- [X] T030 [P] [US4] Create `mcp_servers/twitter/client.py` — tweepy Twitter API v2 adapter: OAuth 1.0a singleton, `async def post_tweet(text: str) -> dict`, `async def get_recent_tweets(max_results: int = 10) -> list`, `async def health_check_twitter() -> bool`; 429 rate limit → structured `{"rate_limited": True, "retry_after": seconds}`; 403 Forbidden → log gracefully
- [X] T031 [P] [US4] Write contract tests RED in `tests/unit/test_twitter_mcp.py` (12 tests) — ✅ 12/12 GREEN
- [X] T032 [US4] Create `mcp_servers/twitter/server.py` — FastMCP with 3 tools: `post_tweet`, `get_recent_tweets`, `health_check`
- [X] T033 [US4] Run `pytest tests/unit/test_twitter_mcp.py` — ✅ 12/12 GREEN
- [X] T034 [US4] Extend `orchestrator/social_poster.py` to support Twitter/X: `platforms=["twitter"]` option, 280-char limit, tweet-specific HITL notification format
- [X] T035 [US4] Add `twitter_mcp` to `~/.claude.json` — DONE: HT-018 completed (2026-03-13)

**Checkpoint**: ✅ PARTIAL — All 3 social MCP servers built and tested (12/12 Twitter tests GREEN). Live testing blocked on HT-018.

---

## Phase 5: US1 — Daily CEO Briefing (MVP) (T036–T063)

**User Story**: US1 — Daily CEO Briefing Delivered to Owner (P1)
**Goal**: Daily briefing auto-generated at 07:00, written to vault, WhatsApp HITL sent, email delivered on approval.
**Independent Test**: `python3 orchestrator/ceo_briefing.py --now` → `vault/CEO_Briefings/YYYY-MM-DD.md` created with all 7 mandatory sections; WhatsApp HITL notification sent.
**Depends on**: Phase 2 (Odoo MCP) — must be complete first.

> **TDD required**: Contract tests RED before briefing generator implemented.

### Tests for US1

- [X] T036 [US1] Write contract tests RED in `tests/unit/test_ceo_briefing.py` (14 base tests + additions from T050–T059) — ✅ 19/19 GREEN

### Implementation for US1

- [X] T037 [US1] Create `orchestrator/run_until_complete.py` — Ralph Wiggum loop utility (FR-029/FR-030, ADR-0018): per-step retry with backoff `2^(attempt-1)` seconds; logs every attempt to `vault/Logs/audit.jsonl`
- [X] T038 [P] [US1] Write unit tests RED in `tests/unit/test_run_until_complete.py` (8 tests) — ✅ 8/8 GREEN
- [X] T039 [US1] Create `orchestrator/ceo_briefing.py` — daily briefing orchestrator with 7 data collectors, LLM draft + template fallback (ADR-0019), idempotent vault write, HITL notification (≤500 chars), email delivery on approval
- [X] T040 [US1] Wire `run_until_complete()` into `run_daily_briefing()` with all 7 steps; `on_exhausted` sends WhatsApp HITL failure notification
- [X] T041 [US1] `_log_event()` added to `orchestrator/ceo_briefing.py` — JSONL logging to `vault/Logs/ceo_briefing.jsonl`
- [X] T042 [US1] Run `pytest tests/unit/test_ceo_briefing.py tests/unit/test_run_until_complete.py` — ✅ 19/19 + 8/8 = 27 tests GREEN
- [X] T043 [US1] Create `specs/010-ceo-briefing-odoo-gold/quickstart.md` — end-to-end setup walkthrough created ✅
- [ ] T044 [US1] Smoke test: `python3 orchestrator/ceo_briefing.py --now` — PENDING: HT-019 (requires live Odoo container + WhatsApp bridge)

**US1 Checkpoint**: ✅ PARTIAL — Daily briefing MVP coded and tested (27/27 unit tests GREEN). Live smoke test blocked on HT-019.

---

## Phase 6: US2 — Weekly Business + Accounting Audit (T045–T060)

**User Story**: US2 — Weekly Business + Accounting Audit (P1)
**Goal**: Full weekly audit written to `week-YYYY-WNN.md` within 120s; GL + AR + invoices + 7-day social/email rollup.
**Independent Test**: `python3 orchestrator/weekly_audit.py --weekly` → `vault/CEO_Briefings/week-YYYY-WNN.md` with all audit sections.
**Depends on**: Phase 2 (Odoo MCP) + Phase 5 (briefing framework patterns).

- [X] T045 [US2] Write unit tests RED in `tests/unit/test_weekly_audit.py` (10 tests) — ✅ 10/10 GREEN
- [X] T046 [US2] Create `orchestrator/weekly_audit.py` — deeper variant of `ceo_briefing.py` with full GL/AR/invoice collectors, 7-day social + email rollups, LLM + template fallback (ADR-0019), ISO week vault file format
- [X] T047 [US2] Wire `run_until_complete()` into `run_weekly_audit()` with 8 steps including HITL notification
- [X] T048 [US2] Run `pytest tests/unit/test_weekly_audit.py` — ✅ 10/10 GREEN
- [X] T049 [US2] Write integration test in `tests/integration/test_briefing_e2e.py` — mock all MCPs, run `run_daily_briefing()` + `run_weekly_audit()` end-to-end — ✅ 2/2 GREEN

**US2 Checkpoint**: ✅ COMPLETE — Weekly audit functional with 10/10 tests GREEN. Full financial data from Odoo (GL + AR + invoices) in audit file.

---

## Phase 7: US5 — Odoo Financial Data Integration Verification (T050–T054)

**User Story**: US5 — Odoo Financial Snapshot in Daily Briefing (P2)
**Goal**: Daily briefing financial section shows overdue invoices only; Odoo down → graceful "unavailable" message.
**Note**: US5 is primarily verified through US1 tests already. These tasks harden the Odoo integration.

- [X] T050 [US5] Verify `collect_odoo_section("daily")` returns only overdue invoices (filter: `days_remaining < 0`); `test_odoo_daily_shows_only_overdue_invoices` added to `test_ceo_briefing.py` ✅
- [X] T051 [US5] Verify empty Odoo list → section shows "No overdue invoices — all clear"; test added to `test_ceo_briefing.py` ✅
- [X] T052 [US5] Verify `OdooConnectionError` caught gracefully; returns `{"status": "unavailable"}` without propagating; test added ✅
- [X] T053 [US5] `test_odoo_demo_data_detected_note` — zero GL balances → "Demo data detected" note; added to `test_ceo_briefing.py` ✅
- [ ] T054 [US5] Live Odoo smoke test — PENDING: HT-019 (requires live Odoo Docker container)

**US5 Checkpoint**: ✅ PARTIAL — Odoo financial integration verified via unit tests (T050–T053). Live smoke test blocked on HT-019.

---

## Phase 8: US6 + US7 — Email Triage + Calendar in Briefing (T055–T060)

**User Story**: US6 — Email Triage Summary in Briefing (P2) | US7 — Calendar Highlights (P3)
**Goal**: Email and calendar sections reliably populate in daily/weekly briefings.
**Note**: Both sections use existing orchestrator log files and existing Calendar MCP — no new MCPs needed.

- [X] T055 [US6] Verify `collect_email_summary()` reads `vault/Logs/` correctly; `test_email_section_counts_by_priority` and `test_email_section_no_emails_message` added to `test_ceo_briefing.py` ✅
- [X] T056 [US6] Verify `collect_7day_email_rollup()` covers 7-day window; `test_email_7day_rollup_date_range` added to `test_weekly_audit.py` ✅
- [X] T057 [US7] Verify `collect_calendar_section("daily")` formats chronologically; `test_calendar_section_chronological_order` and `test_calendar_unavailable_graceful_message` added ✅
- [X] T058 [US7] Verify `collect_calendar_section("weekly")` returns full week events; `test_calendar_weekly_full_week_range` added ✅
- [X] T059 [US6] `test_no_emails_processed_message` added — 24h empty → "No emails processed" (not error) ✅
- [X] T060 [US7] Run `pytest tests/unit/test_ceo_briefing.py tests/unit/test_weekly_audit.py` — ✅ ALL GREEN (19 + 10 = 29 tests)

**US6/US7 Checkpoint**: ✅ COMPLETE — Email and calendar sections verified with both data and empty/unavailable states.

---

## Phase 9: US8 — Agent Skills for All AI Capabilities (T061–T072)

**User Story**: US8 — Agent Skills for All AI Capabilities (P2)
**Goal**: 4 skills created at `~/.claude/skills/`, each loadable via Skill tool with structured workflow.
**Independent Test**: `Skill tool → skill: "ceo-briefing"` loads without error and contains workflow steps.

- [ ] T061 Read existing skills for format reference BEFORE creating any new skills: `~/.claude/skills/security-scan/SKILL.md`, `~/.claude/skills/phase-execution-controller/SKILL.md` — understand YAML frontmatter format (name + description only) and body structure (≤500 lines)
- [ ] T062 [US8] Create `~/.claude/skills/ceo-briefing/SKILL.md` — frontmatter: `name: ceo-briefing`, `description: Generate structured daily CEO briefing...`; body: persona, trigger conditions, data collection steps (Odoo → Calendar → Email → Social), LLM draft → HITL → email delivery; invocation examples; error handling reference
- [ ] T063 [US8] Create `~/.claude/skills/ceo-briefing/references/briefing-format.md` — CEO briefing markdown template with all 7 sections: Email Triage, Financial Alert, Calendar (48h), Social Media Activity, LinkedIn, Pending HITL Actions, System Health
- [ ] T064 [US8] Create `~/.claude/skills/ceo-briefing/references/data-sources.md` — what each source provides, how to call each MCP tool, graceful degradation per source
- [ ] T065 [US8] Create `~/.claude/skills/ceo-weekly-audit/SKILL.md` — frontmatter: `name: ceo-weekly-audit`; body: weekly audit workflow (deeper than daily — full GL/AR/invoice), triggers, sections, output format; invocation examples
- [ ] T066 [US8] Create `~/.claude/skills/ceo-weekly-audit/references/odoo-queries.md` — GL query patterns via Odoo MCP (`get_gl_summary` output structure), AR aging bucket definitions, `get_invoices_due` filter logic
- [ ] T067 [US8] Create `~/.claude/skills/ceo-weekly-audit/references/audit-format.md` — `week-YYYY-WNN.md` template with all audit sections and field definitions
- [ ] T068 [US8] Create `~/.claude/skills/social-post/SKILL.md` — frontmatter: `name: social-post`; body: cross-platform post workflow (draft → privacy gate → HITL → platform routing → publish → log); platform selector (facebook, instagram, twitter, linkedin); invocation examples
- [ ] T069 [US8] Create `~/.claude/skills/social-post/references/platform-limits.md` — character limits per platform (Twitter: 280, Instagram: 2200, Facebook: 63206, LinkedIn: 3000), API tool to call per platform, rate limit notes
- [ ] T070 [US8] Create `~/.claude/skills/social-post/references/hitl-flow.md` — HITL approval message format per platform, vault file naming convention, approval/rejection handling
- [ ] T071 [US8] Create `~/.claude/skills/odoo-financial-summary/SKILL.md` — frontmatter: `name: odoo-financial-summary`; body: interpret GL/AR/invoice data in natural language; when to escalate (bad debt >90 days, overdue >30 days); invocation examples
- [ ] T072 [US8] Create `~/.claude/skills/odoo-financial-summary/references/gl-accounts.md` — account type groupings (income/expense/asset/liability), Odoo account code ranges, how to interpret zero balances (demo data flag)

**US8 Checkpoint**: All 4 skills loadable via Skill tool. Each has SKILL.md + references/ with domain knowledge.

---

## Phase 10: Polish — Ralph Loop, DM Monitor, Cron, Audit Log, Docs, QA (T073–T110)

**Purpose**: Cross-cutting concerns, security hardening, comprehensive audit logging, architecture docs, full test suite.

### Ralph Wiggum Loop Hardening (T073–T077)

- [ ] T073 Run `pytest tests/unit/test_run_until_complete.py` — verify all 8 tests pass after Phase 5 integration; add `test_run_until_complete_used_by_briefing` (mocked) and `test_run_until_complete_used_by_weekly_audit` (mocked)
- [ ] T074 Verify `audit.jsonl` written by `run_until_complete._log_audit()` after each workflow run; add `test_every_step_logged_to_audit_jsonl` — grep `vault/Logs/audit.jsonl` after test run, verify entry count = steps × attempts
- [ ] T075 Wire `run_until_complete()` into `orchestrator/social_poster.py` for Facebook, Instagram, Twitter posting steps — same retry pattern as briefing workflow
- [ ] T076 Verify `on_exhausted` callback sends WhatsApp notification; add `test_on_exhausted_sends_whatsapp_notification` using GoBridge mock
- [ ] T077 Add `test_run_until_complete_social_poster_integration` to `tests/unit/test_social_poster.py`

### Social DM Monitoring (T078–T082) — P3

- [ ] T078 Create `watchers/social_dm_monitor.py` — polling monitor: `async def load_keywords() -> list[str]` (reads `vault/Config/social_keywords.md`), `async def check_facebook_dms() -> list[dict]` (GET `/{page_id}/conversations` — requires page token), `async def check_instagram_mentions() -> list[dict]` (GET `/{ig_id}/mentions`), `async def check_twitter_dms() -> list[dict]` (Twitter elevated access: gracefully returns `[]` + logs warning if 403), `async def should_escalate(text: str, keywords: list[str]) -> bool`, `async def notify_owner(platform: str, sender: str, snippet: str) -> None` (GoBridge.send with job/client/urgent context)
- [ ] T079 Write unit tests in `tests/unit/test_social_dm_monitor.py` (8 tests): `test_load_keywords_from_file`, `test_keyword_match_detected`, `test_no_keyword_no_escalation`, `test_twitter_403_returns_empty_gracefully`, `test_facebook_dm_escalation_sends_whatsapp`, `test_instagram_mention_escalation`, `test_all_platforms_checked_independently`, `test_dm_monitor_logged_to_audit_jsonl`
- [ ] T080 Add DM monitor to orchestrator polling loop in `orchestrator/orchestrator.py` — every 15-min cycle checks all 3 platforms; imports `watchers.social_dm_monitor`
- [ ] T081 Add `test_dm_monitor_integrated_in_orchestrator_loop` — verify `check_facebook_dms()` and `check_twitter_dms()` called during orchestrator cycle (mocked)
- [ ] T082 Run `pytest tests/unit/test_social_dm_monitor.py` — all 8 tests GREEN

### Cron Update (T083–T087)

- [ ] T083 Update `scripts/setup_cron.sh` — add 2 new H0_CRON_MANAGED entries (total = 4 after Phase 6): `BRIEFING_ENTRY="0 7 * * * cd $PROJECT_ROOT && export $(grep -v '^#' .env | xargs) && $PYTHON orchestrator/ceo_briefing.py --now >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"` and `WEEKLY_ENTRY="0 7 * * 1 cd $PROJECT_ROOT && export $(grep -v '^#' .env | xargs) && $PYTHON orchestrator/weekly_audit.py --weekly >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"`; idempotency: strip ALL H0_CRON_MANAGED lines → re-add 4
- [ ] T084 Update `tests/test_cron_scripts.sh` — add SC-010 test: "3x run → exactly 4 H0_CRON_MANAGED entries"; run test: `bash scripts/setup_cron.sh && bash scripts/setup_cron.sh && bash scripts/setup_cron.sh && crontab -l | grep -c H0_CRON_MANAGED` must equal 4
- [ ] T085 Run `bash tests/test_cron_scripts.sh` — all cron tests PASS including new SC-010 test
- [ ] T086 Verify cron entry paths are absolute and use correct Python path: `which python3` substituted; no relative paths
- [ ] T087 Dry-run smoke test: `python3 orchestrator/ceo_briefing.py --now` with all real MCPs but `DRY_RUN=1` env var — verify no actual posts published, vault file created

### Comprehensive Audit Logging (T088–T091)

- [ ] T088 Verify `vault/Logs/audit.jsonl` is written by ALL autonomous action paths: `run_until_complete` (every step attempt), `social_poster.py` (every post published/failed), `ceo_briefing.py` (briefing generated/failed/delivered), `weekly_audit.py` (audit generated/failed/delivered); add `test_every_autonomous_action_in_audit_jsonl`
- [ ] T089 Verify `audit.jsonl` entry format: `{"ts": "ISO8601Z", "action": "workflow.step", "agent": "module_name", "attempt": N, "outcome": "success|error|fallback", "error": ""}` — add format validation test
- [ ] T090 HITL violation grep check (SC-008): `grep -rn "post_to_" orchestrator/ | grep -v "hitl\|pending\|approval"` → must return 0 lines (all posts go through vault approval before API call)
- [ ] T091 Add `test_zero_hitl_violations` — verify no direct API post calls exist outside HITL approval workflow

### Architecture Documentation (T092–T096)

- [ ] T092 Create `docs/architecture.md` — Section 1: System Overview ASCII data flow diagram (watcher → vault → orchestrator → HITL → MCP → external); Section 2: Agent Team Architecture (command team + build team); Section 3: MCP Server Registry table (all 8 custom servers: whatsapp, gmail, calendar, linkedin, odoo, facebook, twitter + postgres from Silver)
- [ ] T093 Add to `docs/architecture.md` — Section 4: Data Flow detail (briefing pipeline with component names); Section 5: ADR Index table (ADR-0001 through ADR-0019, each with title and one-line decision summary)
- [ ] T094 Add to `docs/architecture.md` — Section 6: Known Weaknesses and Mitigations (from spec clarifications: Instagram text-only limitation, Twitter free tier DM restrictions, Odoo demo data detection, LLM credit dependency); Section 7: Lessons Learned (phases 0–6 retrospective: what worked, what to do differently)
- [ ] T095 Verify `docs/architecture.md` exists and covers all required sections; `ls docs/architecture.md` must succeed (SC-012)

### Full Test Suite + Coverage Gate (T096–T105)

- [ ] T096 Run full test suite: `pytest tests/ -v --tb=short 2>&1 | tee reports/phase6-test-run.txt` — review output; all non-integration tests must pass
- [ ] T097 Coverage gate (SC-009): `pytest tests/unit/ --cov=mcp_servers/odoo --cov=mcp_servers/facebook --cov=mcp_servers/twitter --cov=orchestrator/ceo_briefing --cov=orchestrator/weekly_audit --cov=orchestrator/social_poster --cov=orchestrator/run_until_complete --cov-report=term-missing --cov-fail-under=80` — must pass ≥80%
- [ ] T098 Security scan via `/security-scan` skill: verify no hardcoded tokens in new files (`mcp_servers/odoo/`, `mcp_servers/facebook/`, `mcp_servers/twitter/`, `orchestrator/ceo_briefing.py`, `orchestrator/weekly_audit.py`, `orchestrator/social_poster.py`); all tokens from `os.environ.get()` only
- [ ] T099 Verify gitignore coverage: `grep "facebook_token\|twitter_token\|social_keywords" .gitignore` — must return matches for all 3
- [ ] T100 Verify no real credentials in any tracked file: `grep -rn "@gmail\|+92\|AKIA\|sk-\|xoxb" mcp_servers/ orchestrator/ watchers/` — must return 0 matches
- [ ] T101 qa-overseer final gate: invoke `@qa-overseer` agent — validate all 12 SCs against implementation; SC-001 through SC-012 each must have a passing verification method

### Final Documentation Updates (T102–T106)

- [ ] T102 Update `ai-control/MCP.md` — move `odoo_mcp`, `facebook_mcp`, `twitter_mcp` from "Needed" to "Project-Custom MCP Servers" table; verify all 8 custom servers listed
- [ ] T103 Update `specs/overview.md` — Phase 6 status: `IN_PROGRESS` → `COMPLETE`; add Phase 6 deliverables checklist with ✅ for each completed item
- [ ] T104 Update `ai-control/HUMAN-TASKS.md` — mark HT-014/HT-015/HT-016 as DONE after live social credentials are added and tested
- [ ] T105 Create `reports/phase6-implementation-report.md` — summary: tasks completed, tests passing, SCs verified, human tasks remaining, Phase 7 blockers

### Commit and PR (T106–T110)

- [ ] T106 Run `security-scan` skill final pass — clean report required before commit
- [ ] T107 Run `deployment-preflight-check` skill — verify all env vars documented, no missing dependencies, cron entries valid
- [ ] T108 Stage and commit all Phase 6 files: `git add` specific files (never `git add -A`); commit message: `feat(phase-6): Gold Tier CEO briefing + Odoo + social MCPs + agent skills`
- [ ] T109 Create PHR for implementation phase at `history/prompts/ceo-briefing-odoo-gold/004-phase6-gold-implement.misc.prompt.md`
- [ ] T110 Create PR from `010-ceo-briefing-odoo-gold` to `main` with full description of Phase 6 deliverables, SC verification results, human tasks completed/pending

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup):       T001–T009    → no deps, start immediately
Phase 2 (Foundational):T010–T020    → after Phase 1; BLOCKS Phase 5, Phase 6, US5
Phase 3 (US3 Facebook):T021–T028    → after Phase 1; parallel with Phase 4
Phase 4 (US4 Twitter): T029–T035    → after Phase 1; parallel with Phase 3
Phase 5 (US1 Briefing):T036–T044    → after Phase 2 (needs Odoo MCP); MVP GATE
Phase 6 (US2 Audit):   T045–T049    → after Phase 5 (reuses briefing framework)
Phase 7 (US5 Odoo):    T050–T054    → after Phase 2 + Phase 5
Phase 8 (US6+US7):     T055–T060    → after Phase 5 (briefing framework exists)
Phase 9 (US8 Skills):  T061–T072    → after Phase 5 + Phase 6 (need workflow reference)
Phase 10 (Polish):     T073–T110    → after all US phases; QA gate
```

### Agent Team Execution Map

```
teammate-1:  Phase 1 (T001-T009) → Phase 2 (T010-T020) → SIGNAL teammate-3 to start
teammate-2:  Phase 1 done → Phase 3 (T021-T028) ∥ Phase 4 (T029-T035) → SIGNAL teammate-3
teammate-3:  Wait for teammate-1 Phase 2 DONE → Phase 5 (T036-T044) → Phase 6 (T045-T049) → Phase 7 (T050-T054) → Phase 8 (T055-T060)
teammate-4:  Wait for Phase 5 qa-overseer PASS → Phase 9 (T061-T072) → Phase 10 (T073-T110)
```

### Within Each Phase

- Contract tests (RED) → MUST be written and confirmed FAILING before implementing the module
- Models before clients, clients before servers, servers before orchestrators
- Tests GREEN verified before moving to next phase
- `path-warden` invoked after every new file written

---

## Parallel Opportunities

```bash
# Phase 3 + 4 in parallel (teammate-2):
Task("US3: Facebook/Instagram MCP — T021-T028")
Task("US4: Twitter/X MCP — T029-T035")  # different files, no dependency

# Phase 1 parallel tasks:
Task("T007: Create contract JSON schema files")
Task("T008: Update specs/overview.md")

# Foundational parallel tasks:
Task("T010: mcp_servers/odoo/models.py")
Task("T011: mcp_servers/odoo/auth.py")
Task("T013: Write Odoo contract tests RED")
Task("T014: Write Odoo integration test skeleton")

# US8 skills in parallel (no cross-skill deps):
Task("T062-T064: ceo-briefing skill")
Task("T065-T067: ceo-weekly-audit skill")
Task("T068-T070: social-post skill")
Task("T071-T072: odoo-financial-summary skill")
```

---

## Implementation Strategy

### MVP First (US1 Daily Briefing Only — Phases 1+2+5)

1. Complete Phase 1: Setup (T001–T009)
2. Complete Phase 2: Odoo MCP (T010–T020) — CRITICAL blocking phase
3. Complete Phase 5: US1 Daily Briefing (T036–T044)
4. **STOP AND VALIDATE**: Run `python3 orchestrator/ceo_briefing.py --now`, verify vault file and WhatsApp notification
5. This MVP satisfies SC-001, SC-003, SC-004 (partial), SC-005, SC-007, SC-011

### Incremental Delivery

1. MVP (Phases 1+2+5) → Daily briefing live at 07:00
2. Add US2 (Phase 6) → Weekly audit on Mondays
3. Add US3+US4 (Phases 3+4) → Social posting on all platforms (requires HT-014/015/016)
4. Add US8 (Phase 9) → All AI capabilities as Agent Skills
5. Add Phase 10 Polish → Full QA gate, coverage ≥80%, security clean

### Human Blockers (Cannot unblock without human action)

| Task | Blocker | Unblocked By |
|------|---------|-------------|
| T028: facebook_mcp live test | HT-014: Facebook Page + Developer App | Human creates FB Page + App |
| T028: instagram live test | HT-015: Instagram Business Account | Human links IG to FB Page |
| T035: twitter_mcp live test | HT-016: Twitter/X Developer App | Human creates X developer app |
| T039: LLM briefing draft | Anthropic credits needed | Human tops up credits |

**Start unblocked**: Phases 1, 2, 3 (mocked), 4 (mocked), 5, 6, 7, 8, 9 all run without live social credentials.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks — run in parallel
- [USN] = maps to user story N from spec.md
- Contract tests MUST fail before implementation (RED-GREEN TDD — Constitution Principle V)
- Run `path-warden` after every file write
- Mark tasks `[X]` as each is completed
- Commit after each phase or logical group (not individual tasks)
- Total tasks: **T001–T110** (110 tasks)
- Test coverage: 22 (US1) + 10 (US2) + 15 (US3) + 12 (US4) + 8 (Ralph) + 8 (DM Monitor) + scattered additions ≈ **85+ tests** targeting ≥80% coverage
