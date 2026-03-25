# Implementation Plan: CEO Briefing + Odoo — Gold Tier

**Branch**: `010-ceo-briefing-odoo-gold` | **Date**: 2026-03-11
**Spec**: [spec.md](spec.md) | **Clarify**: [002-clarify PHR](../../history/prompts/ceo-briefing-odoo-gold/002-phase6-gold-clarify-social-ralph.clarify.prompt.md)

---

## Summary

Phase 6 Gold Tier delivers the Autonomous Employee: a CEO-level daily+weekly briefing system
combining Odoo ERP financial data, full cross-platform social media (Facebook, Instagram, Twitter/X,
LinkedIn), email/calendar summaries, and a Ralph Wiggum `run_until_complete()` loop for self-healing
multi-step task execution. All AI capabilities are packaged as reusable Agent Skills. Three new
custom MCP servers (Odoo, Facebook/Instagram, Twitter/X) follow the established FastMCP pattern.

---

## Technical Context

**Language/Version**: Python 3.13+ (existing)
**Primary Dependencies**: FastMCP, Pydantic v2, httpx, anthropic SDK, python-dotenv (all existing)
  — NEW: `tweepy` (Twitter/X OAuth 1.0a), no new deps needed for Odoo or Meta Graph API
**Storage**: Obsidian vault (markdown + JSONL) + Neon PostgreSQL (reads via postgres MCP)
**Testing**: pytest, pytest-asyncio, unittest.mock (existing stack)
**Target Platform**: WSL2 Ubuntu (Phase 7: Oracle VM)
**Performance Goals**:
  - Daily briefing: ≤60s (SC-001)
  - Weekly audit: ≤120s (SC-002)
  - HITL notification: ≤90s after briefing file written (SC-003)
  - Social post published: ≤60s after approval (SC-006)
**Constraints**: No Odoo write operations (read-only Phase 6), all env vars from .env only,
  80%+ test coverage (SC-009), 4 H0_CRON_MANAGED entries post-install (SC-010)
**Scale/Scope**: Single owner, 3 social platforms + LinkedIn, daily+weekly cadence

---

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven | spec.md + clarify complete, 0 markers, this plan approved | ✅ PASS |
| II. Local-First Privacy | All tokens gitignored; social credentials in .env only; no cloud sync | ✅ PASS |
| III. HITL for Sensitive Actions | Every social post, briefing email → Pending_Approval → WhatsApp → approve → publish | ✅ PASS |
| IV. MCP-First External Actions | Odoo, Facebook, Instagram, Twitter called ONLY through MCP tools | ✅ PASS |
| V. Test-Driven Quality | Contract tests RED before every MCP server; unit tests RED before poster; >80% coverage | ✅ PASS |
| VI. Watcher Architecture | Briefing generator + social poster = workflow scripts, not watchers; no BaseWatcher needed | ✅ PASS |
| VII. Phase-Gated | Phase 5.5 exit criteria met 2026-03-08; all HT-006/007 done | ✅ PASS |
| VIII. Reusable Intelligence | 4 new Agent Skills packaged; ADRs 0016–0019 suggested | ✅ PASS |
| IX. Security by Default | Social tokens gitignored, HITL enforced, security-scan pre-push | ✅ PASS |
| X. Graceful Degradation | run_until_complete max_retries=3 + escalate; each MCP has structured error return | ✅ PASS |

---

## Reusable Intelligence Map

| What to Reuse | Source | How |
|---------------|--------|-----|
| FastMCP tool pattern | `mcp_servers/linkedin/server.py` | Mirror for Odoo, Facebook, Twitter MCP servers |
| Auth singleton pattern | `mcp_servers/linkedin/auth.py` | Mirror for Twitter OAuth 1.0a; Odoo session auth |
| httpx async adapter pattern | `mcp_servers/linkedin/client.py` | Mirror for Odoo JSON-RPC client, Meta Graph client |
| Pydantic v2 models | `mcp_servers/linkedin/models.py` | All new MCPs use same pattern |
| HITL vault workflow | `orchestrator/hitl_manager.py` | Reuse approve/reject detection for briefings |
| Privacy Gate | `watchers/privacy_gate.py` | Call before every social post draft |
| GoBridge WhatsApp send | `mcp_servers/whatsapp/bridge.py` | Briefing HITL notifications |
| atomic_write, sanitize_filename | `watchers/utils.py` | All vault file writes |
| render_yaml_frontmatter | `watchers/utils.py` | CEO briefing + audit vault files |
| update_frontmatter, move_to_done | `orchestrator/vault_ops.py` | Briefing status transitions |
| JSONL logging pattern | `orchestrator/linkedin_poster.py:_log_event()` | audit.jsonl + social_posts.jsonl |
| Cron idempotency | `scripts/setup_cron.sh` | Add 2 new cron entries (daily briefing, weekly audit) |
| FileLock single-instance | `watchers/utils.py` | Prevent concurrent briefing runs |
| `_count_today_posts()` pattern | `orchestrator/linkedin_poster.py` | Rate limiting per platform |
| test RED-GREEN pattern | `tests/unit/test_linkedin_mcp.py` | All Phase 6 MCP contract tests |
| `build_system_prompt()` | `orchestrator/prompts.py` | Briefing LLM prompt builder |

---

## Agent Team Architecture

```
Lead (main session)
├── @loop-controller      → Phase gate enforcer (FIRST on every task)
├── @path-warden          → File placement after every write
├── @qa-overseer          → Quality gate after Phase E (MVP)
├── @security-scan skill  → Before every commit
│
├── teammate-1: backend-builder  → Phase A+B (Setup + Odoo MCP)
├── teammate-2: backend-builder  → Phase C+D (Facebook/Instagram + Twitter MCPs)
├── teammate-3: backend-builder  → Phase E+F (CEO Briefing Generator + Ralph Wiggum Loop)
└── teammate-4: backend-builder  → Phase G+H+I+J (DM Monitoring + Skills + Cron + Docs)
```

**Spawn order**:
1. Lead: loop-controller gate
2. Lead spawns teammate-1 (blocking: Odoo MCP must exist before briefing generator)
3. teammate-2 runs in parallel with teammate-1 (social MCPs independent)
4. After teammate-1 done → teammate-3 starts Phase E
5. After teammate-3 MVP done → qa-overseer → then teammate-4 runs Phase G+H+I+J
6. Final: security-scan → deployment-preflight → PHR

---

## ⚠️ Agent Creation Note (Human Action Required)

**The existing project agent team (backend-builder, qa-overseer, path-warden, loop-controller,
spec-architect) is sufficient for Phase 6. No new custom agents need to be created.**

However, if you want to instantiate teammates using Claude Code's Agent Teams feature:
```bash
# In a tmux session, run Claude Code with agent teams enabled:
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude

# Then spawn teammates via Task tool with:
# subagent_type: "backend-builder"
# name: "teammate-1"
# team_name: "phase6-gold"
```

> See `~/.claude/CLAUDE.md` → "Agent Teams" section for the full spawn protocol.

---

## New Skills to Create (Phase 6 — FR-022/FR-023)

These 4 skills are **Gold Tier exit criteria**. Create using `/skill-creator` AFTER reading
existing skill patterns in `~/.claude/skills/`.

**Install path**: `\\wsl.localhost\Ubuntu\home\m-y-j\.claude\skills\`

### Skill 1: `ceo-briefing`

```
~/.claude/skills/ceo-briefing/
├── SKILL.md              ← Core workflow + invocation examples
└── references/
    ├── briefing-format.md   ← CEO briefing markdown template + sections
    └── data-sources.md      ← What each source provides (Odoo, Calendar, Social, Email)
```

**SKILL.md frontmatter**:
```yaml
---
name: ceo-briefing
description: >
  Generate a structured daily CEO briefing for H0 Personal AI Employee project.
  Use when the user asks to generate a briefing, run the daily CEO report,
  collect data across all sources (Odoo, Calendar, Gmail, LinkedIn, social media),
  or trigger the daily 07:00 briefing workflow. Handles: data collection,
  LLM-assisted draft, HITL WhatsApp notification, email delivery on approval.
---
```

### Skill 2: `ceo-weekly-audit`

```
~/.claude/skills/ceo-weekly-audit/
├── SKILL.md              ← Weekly audit workflow (deeper than daily briefing)
└── references/
    ├── odoo-queries.md      ← GL/AR/invoice query patterns via Odoo MCP
    └── audit-format.md      ← week-YYYY-WNN.md template with all sections
```

### Skill 3: `social-post`

```
~/.claude/skills/social-post/
├── SKILL.md              ← Cross-platform post workflow: draft→privacy→HITL→publish
└── references/
    ├── platform-limits.md   ← Twitter 280, Instagram 2200, Facebook 63206, LinkedIn 3000
    └── hitl-flow.md         ← HITL approval format per platform
```

### Skill 4: `odoo-financial-summary`

```
~/.claude/skills/odoo-financial-summary/
├── SKILL.md              ← Interpret Odoo GL/AR/invoice data in natural language
└── references/
    ├── gl-accounts.md       ← Account type groupings (income/expense/asset/liability)
    └── ar-aging.md          ← AR aging bucket definitions and action thresholds
```

**Creation steps** (for each skill, AFTER reading Anthropic skill docs):
1. Read 2-3 existing skills for format reference: `security-scan`, `phase-execution-controller`, `mcp-builder`
2. Create skill dir at `~/.claude/skills/<skill-name>/`
3. Write `SKILL.md` (YAML frontmatter + body ≤500 lines)
4. Write `references/` files for domain knowledge
5. Test by invoking: `Skill tool → skill: "<skill-name>"`

---

## New MCP Servers to Register in `~/.claude.json`

**Register path**: `\\wsl.localhost\Ubuntu\home\m-y-j\.claude.json`

After building each server, add to `~/.claude.json` under `"mcpServers"`:

### odoo_mcp
```json
"odoo_mcp": {
  "command": "python3",
  "args": ["/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/odoo/server.py"],
  "env": {
    "ODOO_URL": "http://localhost:8069",
    "ODOO_DB": "h0_odoo",
    "ODOO_USER": "admin",
    "ODOO_PASSWORD": "<from .env>",
    "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
  }
}
```

### facebook_mcp
```json
"facebook_mcp": {
  "command": "python3",
  "args": ["/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/facebook/server.py"],
  "env": {
    "FACEBOOK_PAGE_ID": "<from .env>",
    "FACEBOOK_PAGE_ACCESS_TOKEN": "<from .env>",
    "INSTAGRAM_BUSINESS_ACCOUNT_ID": "<from .env>",
    "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
  }
}
```

### twitter_mcp
```json
"twitter_mcp": {
  "command": "python3",
  "args": ["/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/twitter/server.py"],
  "env": {
    "TWITTER_API_KEY": "<from .env>",
    "TWITTER_API_SECRET": "<from .env>",
    "TWITTER_ACCESS_TOKEN": "<from .env>",
    "TWITTER_ACCESS_TOKEN_SECRET": "<from .env>",
    "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
  }
}
```

> After adding each entry → restart Claude Code → verify with `/mcp`.

---

## Project Structure

### Documentation (this feature)

```text
specs/010-ceo-briefing-odoo-gold/
├── spec.md              # Feature requirements (complete — 30 FRs, 12 SCs)
├── plan.md              # This file
├── data-model.md        # Phase B output: entity schemas + state transitions
├── quickstart.md        # Phase E output: end-to-end setup walkthrough
├── contracts/
│   ├── odoo-mcp-tools.md         # Odoo MCP tool contracts
│   ├── facebook-mcp-tools.md     # Facebook/Instagram MCP contracts
│   └── twitter-mcp-tools.md      # Twitter/X MCP contracts
└── tasks.md             # Generated by /sp.tasks (NOT created here)
```

### Source Code

```text
mcp_servers/
├── odoo/
│   ├── __init__.py
│   ├── server.py        # FastMCP: get_gl_summary, get_ar_aging, get_invoices_due, health_check
│   ├── client.py        # JSON-RPC adapter (httpx, /web/dataset/call_kw, session auth)
│   ├── auth.py          # Odoo session token singleton (login → sid → reuse)
│   └── models.py        # Pydantic v2: GLSummary, ARAgingResult, InvoiceResult, HealthCheckResult
│
├── facebook/
│   ├── __init__.py
│   ├── server.py        # FastMCP: post_update, post_facebook_only, post_instagram_only,
│   │                    #          get_recent_posts, health_check
│   ├── client.py        # Meta Graph API adapter (httpx, Page Access Token)
│   └── models.py        # Pydantic v2: PostInput, PostResult, RecentPostsResult
│
└── twitter/
    ├── __init__.py
    ├── server.py        # FastMCP: post_tweet, get_recent_tweets, health_check
    ├── client.py        # Twitter API v2 adapter (tweepy or httpx + OAuth 1.0a)
    └── models.py        # Pydantic v2: TweetInput, TweetResult, RecentTweetsResult

orchestrator/
├── ceo_briefing.py      # Daily CEO briefing workflow (FR-001–FR-008)
├── weekly_audit.py      # Weekly business + accounting audit (FR-002)
├── social_poster.py     # Cross-platform posting (Facebook, Instagram, Twitter)
│                        # (extends linkedin_poster.py pattern)
└── run_until_complete.py # Ralph Wiggum loop utility (FR-029/FR-030)

watchers/
└── social_dm_monitor.py # DM/comment monitoring + HITL escalation (FR-028)

scripts/
├── setup_cron.sh        # UPDATE: add daily briefing + weekly audit entries (→ 4 total)
├── remove_cron.sh       # Unchanged
└── facebook_auth.py     # One-time Page Access Token verification helper

vault/
├── CEO_Briefings/       # Already exists (HT-001)
│   ├── YYYY-MM-DD.md    # Daily briefings
│   └── week-YYYY-WNN.md # Weekly audits
├── Logs/
│   ├── ceo_briefing.jsonl    # Briefing events
│   ├── social_posts.jsonl    # Cross-platform post log (FR-020)
│   └── audit.jsonl           # Comprehensive autonomous action log (FR-024)
└── Config/
    └── social_keywords.md    # DM monitoring keywords: job, client, collaboration, urgent, hire

tests/
├── unit/
│   ├── test_odoo_mcp.py       # Contract tests (RED before Odoo server)
│   ├── test_facebook_mcp.py   # Contract tests (RED before Facebook server)
│   ├── test_twitter_mcp.py    # Contract tests (RED before Twitter server)
│   ├── test_ceo_briefing.py   # Unit tests (RED before briefing generator)
│   ├── test_weekly_audit.py   # Unit tests
│   ├── test_social_poster.py  # Unit tests
│   └── test_run_until_complete.py  # Unit tests for Ralph Wiggum loop
├── integration/
│   └── test_briefing_e2e.py   # End-to-end (mock Odoo + Calendar + social)
└── contract/
    ├── odoo-mcp-tools.json    # Odoo MCP tool contracts (input/output schemas)
    ├── facebook-mcp-tools.json
    └── twitter-mcp-tools.json

docs/
└── architecture.md      # Phase 6 exit criterion (FR-025, SC-012)
```

---

## Phase A: Setup (T001–T006)

### T001 — Directory structure

Create:
```bash
mkdir -p mcp_servers/odoo mcp_servers/facebook mcp_servers/twitter
mkdir -p tests/contract
touch mcp_servers/odoo/__init__.py mcp_servers/facebook/__init__.py mcp_servers/twitter/__init__.py
mkdir -p docs
```

### T002 — .gitignore additions

Append (check for duplicates first):
```
# Phase 6 social media tokens
facebook_token.json
twitter_token.json
vault/Config/social_keywords.md   # Contains owner preferences — gitignore sensitive config
```

### T003 — .env additions (template — DO NOT commit)

Document required new env vars (add to `.env.example`):
```bash
# Odoo (HT-007 DONE — fill actual values)
ODOO_URL=http://localhost:8069
ODOO_DB=h0_odoo
ODOO_USER=admin
ODOO_PASSWORD=

# Facebook + Instagram (HT-014/HT-015 — PENDING)
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
FACEBOOK_PAGE_ID=
FACEBOOK_PAGE_ACCESS_TOKEN=
INSTAGRAM_BUSINESS_ACCOUNT_ID=

# Twitter/X (HT-016 — PENDING)
TWITTER_API_KEY=
TWITTER_API_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_BEARER_TOKEN=

# Briefing schedule (optional overrides)
CRON_BRIEFING_TIME="0 7"        # Daily briefing: 07:00
CRON_WEEKLY_AUDIT_DAY="1"       # Monday = 1 (ISO weekday)
```

### T004 — pip dependencies

Add to `requirements.txt`:
```
tweepy>=4.14.0        # Twitter/X OAuth 1.0a + API v2
```
No new deps for Odoo (JSON-RPC = plain httpx) or Meta Graph API (plain httpx).

### T005 — vault/Config/social_keywords.md

```markdown
# Social DM/Comment Monitoring Keywords

Categories monitored for HITL escalation (FR-028):

- job
- hire
- freelance
- client
- project
- collaboration
- collab
- urgent
- contract
- offer
- opportunity
- payment
- invoice
- business
```

### T006 — MCP contract JSON files

Create `tests/contract/odoo-mcp-tools.json`, `facebook-mcp-tools.json`, `twitter-mcp-tools.json`
with input/output schemas for each tool (mirrors `specs/008-hitl-whatsapp-silver/contracts/`).

---

## Phase B: Odoo MCP Server (T007–T018)

### Architecture: Odoo JSON-RPC Authentication

Odoo 18 uses session-based auth via JSON-RPC:
```
POST /web/dataset/call_kw HTTP/1.1
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "model": "account.move",
    "method": "search_read",
    "args": [domain],
    "kwargs": {"fields": [...], "limit": 100}
  }
}
```

Authentication: First call `POST /web/session/authenticate` → get session `id` (cookie) → reuse.

### T007 — mcp_servers/odoo/models.py

Pydantic v2 models:
- `GLSummary`: `by_type: dict[str, float]` (income, expense, asset, liability)
- `ARAgingResult`: `current: float`, `overdue_30_60: float`, `overdue_61_90: float`, `bad_debt_90plus: float`, `partners: list[ARPartner]`
- `InvoiceResult`: `invoice_id: int`, `partner_name: str`, `amount: float`, `due_date: str`, `days_remaining: int`
- `HealthCheckResult`: `healthy: bool`, `odoo_version: str`, `db_name: str`, `error: str | None`

### T008 — mcp_servers/odoo/auth.py

Singleton session token — mirrors `mcp_servers/linkedin/auth.py`:
- `OdooAuthError(Exception)` — raised when login fails
- `get_odoo_session()` → `str` (session_id cookie)
- `reset_session_cache()` — force re-login
- Login: `POST /web/session/authenticate` with `{db, login, password}`
- Session stored in memory (not disk — Odoo sessions live ~1h)

### T009 — mcp_servers/odoo/client.py

```python
# Key functions:
async def get_gl_summary() -> dict          # account.account search_read
async def get_ar_aging() -> dict            # account.move.line search + age buckets
async def get_invoices_due(days: int=7) -> list  # account.move due date filter
async def health_check_odoo() -> dict      # session/authenticate ping
```

JSON-RPC payload builder:
```python
def _rpc_payload(model: str, method: str, domain: list, fields: list) -> dict:
    return {
        "jsonrpc": "2.0", "method": "call",
        "params": {"model": model, "method": method,
                   "args": [domain], "kwargs": {"fields": fields}}
    }
```

Error handling: `OdooConnectionError` for network failures; all tools return structured dict.

### T010 — Contract tests RED (test_odoo_mcp.py)

Write 12 tests covering all 4 tools before implementing `server.py`. All must FAIL.

### T011 — mcp_servers/odoo/server.py

FastMCP server exposing 4 tools (FR-009):
```python
@mcp.tool()
async def get_gl_summary() -> dict: ...

@mcp.tool()
async def get_ar_aging() -> dict: ...

@mcp.tool()
async def get_invoices_due(days_ahead: int = 7) -> dict: ...

@mcp.tool()
async def health_check() -> dict: ...
```

### T012 — data-model.md (Odoo entities)

Document: GL account types, AR aging buckets, invoice lifecycle states, session auth flow.

### T013–T018 — Unit tests GREEN, integration tests, MCP.md + claude.json update

- All 12 contract tests GREEN
- `ai-control/MCP.md` updated: odoo_mcp added to Project-Custom table
- `~/.claude.json` updated: odoo_mcp block added (requires Claude Code restart)

---

## Phase C: Facebook/Instagram MCP Server (T019–T030)

### Architecture: Meta Graph API

```
# Facebook Page post:
POST https://graph.facebook.com/{PAGE_ID}/feed
  ?message={text}&access_token={PAGE_TOKEN}

# Instagram Business post (2-step):
1. POST https://graph.facebook.com/{IG_ACCOUNT_ID}/media
     ?image_url={url}&caption={text}&access_token={PAGE_TOKEN}
   → returns: {id: "container_id"}

2. POST https://graph.facebook.com/{IG_ACCOUNT_ID}/media_publish
     ?creation_id={container_id}&access_token={PAGE_TOKEN}

# Get recent posts:
GET https://graph.facebook.com/{PAGE_ID}/posts
     ?fields=id,message,created_time&limit=10&access_token={PAGE_TOKEN}
```

Note: Instagram text-only posts (no image) require Reels API on newer Meta versions.
For simplicity: Instagram posts always include a generated image or the same post text
treated as a caption with a default branded image.

### T019–T021 — models + client + contract tests RED

- `FacebookPostInput`: `text: str` (≤63206), `visibility: Literal["EVERYONE","FRIENDS"]`
- `InstagramMediaInput`: `caption: str` (≤2200), `image_url: str | None`
- Client: `async def post_to_facebook(text)`, `async def post_to_instagram(caption, image_url=None)`
- 15 contract tests RED

### T022–T025 — server.py GREEN

Tools: `post_update`, `post_facebook_only`, `post_instagram_only`, `get_recent_posts`, `health_check`

Character limit enforcement BEFORE API call (FR-021).

### T026–T030 — social_poster.py extension

Extend `orchestrator/social_poster.py` to handle Facebook/Instagram workflow:
- Same pattern as `linkedin_poster.py` (draft → privacy gate → HITL → publish)
- HITL notification includes platform + preview
- JSONL logging to `vault/Logs/social_posts.jsonl`
- Register `facebook_mcp` in `~/.claude.json`

---

## Phase D: Twitter/X MCP Server (T031–T040)

### Architecture: Twitter API v2 (tweepy)

```python
# Auth: OAuth 1.0a (write access)
import tweepy
client = tweepy.Client(
    consumer_key=TWITTER_API_KEY,
    consumer_secret=TWITTER_API_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
)
response = client.create_tweet(text="Hello Twitter/X!")

# Get recent tweets:
response = client.get_users_tweets(id=user_id, max_results=10)
```

### T031–T033 — models + client + contract tests RED

- `TweetInput`: `text: str` (enforced ≤280 chars before API call, FR-021)
- `TweetResult`: `success: bool`, `tweet_id: str | None`, `url: str | None`
- 10 contract tests RED

### T034–T037 — server.py + social_poster Twitter workflow

Tools: `post_tweet`, `get_recent_tweets`, `health_check`
Rate limit handling: `429` → queue for next window + notify WhatsApp.

### T038–T040 — Register + MCP.md update

- Register `twitter_mcp` in `~/.claude.json`
- Add to `ai-control/MCP.md` Project-Custom table

---

## Phase E: CEO Briefing Generator (T041–T058) [MVP]

### Architecture: orchestrator/ceo_briefing.py

The briefing generator collects data from ALL sources, degrades gracefully when any is unavailable,
drafts with LLM assistance, writes to vault, and routes through HITL.

```python
# orchestrator/ceo_briefing.py — key functions:

async def collect_email_summary() -> dict:
    """Read vault/Logs/ for yesterday's orchestrator decisions."""

async def collect_calendar_section() -> dict:
    """Calendar MCP: next 48h events (daily) or full week (weekly)."""

async def collect_odoo_section(period: str) -> dict:
    """Odoo MCP: overdue invoices only (daily) or full GL+AR (weekly)."""

async def collect_social_section(period: str) -> dict:
    """Read vault/Logs/social_posts.jsonl for past 24h/7d across all platforms."""

async def collect_linkedin_section(period: str) -> dict:
    """Read vault/Logs/linkedin_posts.jsonl for past 24h/7d."""

async def draft_briefing(sections: dict, period: str) -> str:
    """LLM-assisted briefing text. Falls back to template if credits empty."""

async def write_briefing_vault(content: str, period: str) -> Path:
    """Write vault/CEO_Briefings/YYYY-MM-DD.md with YAML frontmatter."""

async def send_hitl_notification(briefing_path: Path, metrics: dict) -> None:
    """WhatsApp notification ≤500 chars with key metrics (FR-004)."""

async def check_approval_and_email(briefing_path: Path) -> dict:
    """Scan vault file status; on approved → Gmail MCP send → update frontmatter."""

async def run_daily_briefing() -> dict:
    """Entry point — orchestrates all steps via run_until_complete()."""
```

### Briefing vault file format

```markdown
---
type: ceo_briefing
period: daily
generated_at: 2026-03-11T07:00:00Z
status: pending_approval
sections_collected: [email, calendar, odoo, social_linkedin, social_facebook, social_twitter]
---

# CEO Briefing — Tuesday 11 March 2026

## Email Triage (24h)
12 emails processed: 3 HIGH, 7 MED, 2 LOW. 2 items pending HITL.

## Financial Alert
⚠️ 2 invoices overdue (31+ days) — see weekly audit for details.

## Calendar (Next 48h)
- 14:00 today: Team standup
- 09:00 tomorrow: Client call — ProjectX

## Social Media Activity
- LinkedIn: 1 post published (245 views)
- Facebook: 0 posts
- Instagram: 0 posts
- Twitter/X: 0 posts

## LinkedIn Briefing
No pending drafts.
```

### T041–T058 — Implementation sequence

- T041: Contract tests RED for ceo_briefing.py
- T042: `collect_*` functions (mock MCP calls)
- T043: `draft_briefing()` with LLM + template fallback
- T044: `write_briefing_vault()` with idempotency (FR-008)
- T045: `send_hitl_notification()` (≤500 chars summary)
- T046: `check_approval_and_email()` (Gmail MCP send on approval)
- T047: `run_daily_briefing()` CLI entry: `python3 orchestrator/ceo_briefing.py --now`
- T048–T052: Tests GREEN
- T053–T058: quickstart.md, integration test (mock all MCPs), qa-overseer MVP gate

---

## Phase F: Ralph Wiggum Loop (T059–T065)

### Architecture: orchestrator/run_until_complete.py

This is a **new** utility module (not the existing 15-min orchestrator polling loop).
The constitution defines it as: "Create state → Claude works → Try exit → Check /Done? →
NO: re-inject → YES: allow exit."

Phase 6 implementation = per-workflow step retry with self-diagnosis:

```python
# orchestrator/run_until_complete.py

import asyncio, json, logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Awaitable, Any
from watchers.utils import atomic_write

VAULT_LOGS = Path(__file__).resolve().parents[1] / "vault" / "Logs"
logger = logging.getLogger("run_until_complete")


async def run_until_complete(
    workflow_name: str,
    steps: list[tuple[str, Callable[[], Awaitable[Any]]]],
    max_retries: int = 3,
    on_exhausted: Callable[[str, str, Exception], Awaitable[None]] | None = None,
) -> dict:
    """
    Execute workflow steps sequentially with per-step retry and exponential backoff.

    Args:
        workflow_name: Human-readable name for audit logging (e.g., "daily_briefing")
        steps: List of (step_name, async_callable) tuples
        max_retries: Maximum retries per step (default 3; Constitution Principle X)
        on_exhausted: Optional async callback for HITL escalation on retry exhaustion

    Returns:
        dict with status, completed_steps, failed_step (if any)
    """
    completed = []
    for step_name, step_fn in steps:
        for attempt in range(1, max_retries + 1):
            try:
                await step_fn()
                _log_audit(workflow_name, step_name, attempt, "success")
                completed.append(step_name)
                break
            except Exception as e:
                _log_audit(workflow_name, step_name, attempt, "error", str(e))
                if attempt == max_retries:
                    logger.error(f"[{workflow_name}] Step '{step_name}' exhausted {max_retries} retries: {e}")
                    if on_exhausted:
                        await on_exhausted(workflow_name, step_name, e)
                    return {"status": "failed", "completed": completed, "failed_step": step_name, "error": str(e)}
                backoff = 2 ** (attempt - 1)
                logger.warning(f"[{workflow_name}] Step '{step_name}' attempt {attempt} failed: {e}. Retry in {backoff}s.")
                await asyncio.sleep(backoff)
    return {"status": "complete", "completed": completed}


def _log_audit(workflow: str, step: str, attempt: int, outcome: str, error: str = "") -> None:
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "action": f"{workflow}.{step}",
        "agent": "run_until_complete",
        "attempt": attempt,
        "outcome": outcome,
        "error": error,
    }
    VAULT_LOGS.mkdir(parents=True, exist_ok=True)
    with open(VAULT_LOGS / "audit.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**Usage in ceo_briefing.py**:
```python
from orchestrator.run_until_complete import run_until_complete

result = await run_until_complete(
    workflow_name="daily_briefing",
    steps=[
        ("collect_email", collect_email_summary),
        ("collect_calendar", collect_calendar_section),
        ("collect_odoo", lambda: collect_odoo_section("daily")),
        ("collect_social", lambda: collect_social_section("daily")),
        ("draft_briefing", lambda: draft_briefing(sections, "daily")),
        ("write_vault", lambda: write_briefing_vault(content, "daily")),
        ("send_hitl", lambda: send_hitl_notification(briefing_path, metrics)),
    ],
    max_retries=3,
    on_exhausted=_escalate_to_hitl,
)
```

### T059–T065 — Implementation

- T059: Test RED for `run_until_complete` (success, retry, exhaustion, escalation)
- T060: Implement `run_until_complete.py`
- T061: Wire into `ceo_briefing.py` (replace manual try/except with `run_until_complete`)
- T062: Wire into `weekly_audit.py`
- T063: Wire into `social_poster.py` for all platforms
- T064: Tests GREEN
- T065: `audit.jsonl` verified by tests (SC-011 gate)

---

## Phase G: Social DM Monitoring (T066–T072) [P3]

### Architecture: watchers/social_dm_monitor.py

Polling watcher that checks incoming DMs/comments across platforms for keyword matches.

```python
# Core loop:
async def check_facebook_dms() -> list[dict]:
    """GET /me/conversations via Graph API. Returns unread messages."""

async def check_instagram_mentions() -> list[dict]:
    """GET /{ig_account_id}/mentions. Returns @mentions in comments."""

async def check_twitter_dms() -> list[dict]:
    """GET /2/dm_conversations (elevated access required — Twitter Free may not support)."""

async def should_escalate(message_text: str, keywords: list[str]) -> bool:
    """Keyword match check against vault/Config/social_keywords.md."""

async def notify_owner(platform: str, sender: str, snippet: str, full_text: str) -> None:
    """WhatsApp HITL notification for matched DMs (FR-028)."""
```

**Note**: Twitter/X DM monitoring requires Elevated access (Free tier may not support). Log
"DM monitoring unavailable — Elevated API access required" gracefully if 403.

### T066–T072 — Implementation

- T066: Contract tests RED for DM monitor
- T067: `load_keywords()` from `vault/Config/social_keywords.md`
- T068: `check_facebook_dms()` + `should_escalate()` + `notify_owner()`
- T069: `check_instagram_mentions()` (@ mentions in post comments)
- T070: `check_twitter_dms()` (graceful degradation if 403)
- T071: Tests GREEN
- T072: Add to cron or orchestrator loop (every 15 min, via existing `orchestrator.py` polling)

---

## Phase H: Weekly Business + Accounting Audit (T073–T082)

### Architecture: orchestrator/weekly_audit.py

Deeper variant of `ceo_briefing.py` — runs Monday 07:00:

```python
async def collect_full_gl() -> dict:
    """Odoo MCP: get_gl_summary() — all accounts grouped by type."""

async def collect_full_ar() -> dict:
    """Odoo MCP: get_ar_aging() — all 4 buckets."""

async def collect_invoices_due() -> dict:
    """Odoo MCP: get_invoices_due(days=7) — upcoming 7-day payments."""

async def collect_7day_social_rollup() -> dict:
    """Read vault/Logs/social_posts.jsonl for 7-day window across all platforms."""

async def collect_7day_email_rollup() -> dict:
    """Read vault/Logs/ for 7-day email decisions."""

async def draft_weekly_audit(sections: dict) -> str:
    """LLM-assisted audit narrative with financial interpretation."""

async def write_audit_vault(content: str) -> Path:
    """Write vault/CEO_Briefings/week-YYYY-WNN.md."""

async def run_weekly_audit() -> dict:
    """Entry point: python3 orchestrator/weekly_audit.py --weekly"""
```

### T073–T082 — Implementation

Mirror `ceo_briefing.py` structure. Use `run_until_complete()` for all steps.
Weekly audit file: `week-2026-W11.md` (ISO week number format).

---

## Phase I: Cron Update + scripts Patch (T083–T087)

### T083 — Update setup_cron.sh

Add 2 new H0_CRON_MANAGED entries (total = 4):
```bash
# New entries to add:
BRIEFING_ENTRY="0 7 * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/ceo_briefing.py --now >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
WEEKLY_ENTRY="0 7 * * 1 cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/weekly_audit.py --weekly >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
```

Idempotency: strip ALL H0_CRON_MANAGED lines, re-add 4. Run 3x → exactly 4 entries (SC-010).

### T084 — tests/test_cron_scripts.sh update

Add test: "3x run → exactly 4 H0_CRON_MANAGED entries".

### T085–T087 — Verify cron + smoke test

- `bash scripts/setup_cron.sh` → `crontab -l | grep H0_CRON_MANAGED | wc -l` = 4
- Dry-run: `python3 orchestrator/ceo_briefing.py --now` with all MCPs mocked

---

## Phase J: Agent Skills Creation (T088–T095)

Create 4 skills per FR-022/FR-023. Use `/skill-creator` workflow:

### T088 — Read existing skills for format reference

Before creating:
```bash
cat ~/.claude/skills/security-scan/SKILL.md
cat ~/.claude/skills/phase-execution-controller/SKILL.md
cat ~/.claude/skills/mcp-builder/SKILL.md
```

### T089 — Create `ceo-briefing` skill

```
~/.claude/skills/ceo-briefing/
├── SKILL.md
└── references/
    ├── briefing-format.md
    └── data-sources.md
```

### T090 — Create `ceo-weekly-audit` skill

```
~/.claude/skills/ceo-weekly-audit/
├── SKILL.md
└── references/
    ├── odoo-queries.md
    └── audit-format.md
```

### T091 — Create `social-post` skill

```
~/.claude/skills/social-post/
├── SKILL.md
└── references/
    ├── platform-limits.md
    └── hitl-flow.md
```

### T092 — Create `odoo-financial-summary` skill

```
~/.claude/skills/odoo-financial-summary/
├── SKILL.md
└── references/
    ├── gl-accounts.md
    └── ar-aging.md
```

### T093–T095 — Verify skills loadable

Test each skill: `Skill tool → skill: "ceo-briefing"` → confirm SKILL.md loads correctly.

---

## Phase K: Audit Logging + Architecture Docs (T096–T102)

### T096 — Comprehensive audit log (FR-024)

`vault/Logs/audit.jsonl` format:
```json
{"ts":"2026-03-11T07:00:01Z","action":"daily_briefing.collect_odoo","agent":"run_until_complete","attempt":1,"outcome":"success","error":""}
{"ts":"2026-03-11T07:00:15Z","action":"social_post.post_facebook","agent":"social_poster","platform":"facebook","post_id":"123","outcome":"success","error":""}
```

Every autonomous action MUST write here (SC-011). Verify with grep count in tests.

### T097–T102 — docs/architecture.md (FR-025, SC-012)

Required sections:
1. System Overview — ASCII data flow diagram
2. Agent Team Architecture — command + build team
3. MCP Server Registry — all 8 custom servers
4. Data Flow — watcher → vault → orchestrator → HITL → MCP → external
5. ADR Index — links to all 0001–0019 ADRs
6. Known Weaknesses + Mitigations (from sp.clarify Phase 6 Q&A)
7. Lessons Learned (Phase 0–6 retrospective)

---

## Phase L: QA, Security, Coverage Gate (T103–T110)

### T103 — Full test suite

```bash
pytest tests/ -v --tb=short 2>&1 | tee reports/phase6-test-run.txt
# Expected: ≥180 tests (142 existing + ~40 new Phase 6 tests)
```

### T104 — Coverage gate (SC-009)

```bash
pytest tests/unit/ \
  --cov=mcp_servers/odoo --cov=mcp_servers/facebook --cov=mcp_servers/twitter \
  --cov=orchestrator/ceo_briefing --cov=orchestrator/weekly_audit \
  --cov=orchestrator/social_poster --cov=orchestrator/run_until_complete \
  --cov-report=term-missing --cov-fail-under=80
```

### T105 — Security scan

```bash
# Run /security-scan skill — checks:
# - No hardcoded tokens in new files
# - All social token files in .gitignore
# - No real names/emails/phone numbers in tracked files
# - HITL enforcement in all external call paths
```

### T106 — Cron idempotency test

```bash
bash scripts/setup_cron.sh && bash scripts/setup_cron.sh && bash scripts/setup_cron.sh
crontab -l | grep -c H0_CRON_MANAGED  # Must = 4
```

### T107 — HITL violation check (SC-008)

Grep all new MCP client files to verify no `post_*` function calls exist without HITL gate:
```bash
grep -rn "post_to_" orchestrator/ | grep -v "hitl\|pending\|approval"
# Must return 0 lines (all posts go through vault approval)
```

### T108 — specs/overview.md update

- Phase 6 status: `NOT_STARTED` → `IN_PROGRESS` (at plan completion)
- After implementation complete: `IN_PROGRESS` → `COMPLETE`
- Add Phase 6 deliverables checklist

### T109 — ai-control/MCP.md final update

Move to Project-Custom table:
- `odoo_mcp`
- `facebook_mcp`
- `twitter_mcp`

### T110 — PHR + ADR suggestions

Create PHR for implementation phase. Suggest 4 ADRs (see below).

---

## ADR Suggestions

After plan approval, suggest creating these ADRs before implementation:

| ADR | Title | Decision |
|-----|-------|----------|
| ADR-0016 | Odoo JSON-RPC vs REST vs XML-RPC | JSON-RPC via `/web/dataset/call_kw` (same as Odoo 16+); XML-RPC deprecated; no REST API in Odoo 18 Community |
| ADR-0017 | Social MCP Unification vs Separation | 3 separate MCP servers (odoo, facebook, twitter) not 1 unified "social MCP"; separation = independent failure domains + independent token lifecycle |
| ADR-0018 | Ralph Wiggum Loop Implementation | `run_until_complete()` per-workflow step wrapper; NOT the 15-min orchestrator polling; max_retries=3; exponential backoff; HITL escalation on exhaustion |
| ADR-0019 | CEO Briefing LLM Fallback Strategy | Template-based fallback when Anthropic credits = 0; LLM only for narrative + interpretation; data collection always works regardless of credits |

---

## Acceptance Criteria Verification Map

| SC | Verification Method | Phase |
|----|--------------------|-|
| SC-001: Daily briefing ≤60s | `time python3 orchestrator/ceo_briefing.py --now` | After Phase E |
| SC-002: Weekly audit ≤120s | `time python3 orchestrator/weekly_audit.py --weekly` | After Phase H |
| SC-003: WhatsApp notification ≤90s | timestamp diff in ceo_briefing.jsonl | After Phase E |
| SC-004: Odoo data ≥95% when running | Integration test with live Odoo container | After Phase B |
| SC-005: Briefing 100% when Odoo down | Unit test: mock Odoo error → briefing still generated | After Phase E |
| SC-006: Social post ≤60s post-approval | Unit test: mock approval → time to `published` | After Phase C+D |
| SC-007: All 7 sections present | Unit test: check markdown sections | After Phase E |
| SC-008: Zero HITL violations | grep check in T107 | After Phase K |
| SC-009: ≥80% test coverage | `--cov-fail-under=80` | After Phase K |
| SC-010: 4 H0_CRON_MANAGED entries | `bash scripts/setup_cron.sh` 3x → count 4 | After Phase I |
| SC-011: Zero unlogged actions | grep audit.jsonl after each test run | After Phase F |
| SC-012: docs/architecture.md exists | `ls docs/architecture.md` | After Phase K |

---

## Implementation Order

```
Phase A (Setup):          T001–T006    [unblocked]
Phase B (Odoo MCP):       T007–T018    [unblocked, parallel with C]
Phase C (Facebook MCP):   T019–T030    [parallel with B]
Phase D (Twitter MCP):    T031–T040    [parallel with B]
Phase E (Briefing, MVP):  T041–T058    [after B complete]
Phase F (Ralph Loop):     T059–T065    [after E]
Phase G (DM Monitor):     T066–T072    [parallel with H, after C+D]
Phase H (Weekly Audit):   T073–T082    [after E+F]
Phase I (Cron):           T083–T087    [after E+H]
Phase J (Skills):         T088–T095    [after E+H (need workflow reference)]
Phase K (Audit+Docs):     T096–T102    [after all implementation]
Phase L (QA+Security):    T103–T110    [final gate]
```

**MVP scope**: Phases A+B+E+F → delivers SC-001/SC-003/SC-004/SC-005/SC-011.
Requires only Odoo credentials (HT-007 already DONE).

Social features (SC-006) blocked on HT-014/HT-015/HT-016.
Skills (SC-012 via docs) not blocked on credentials.

---

## Human Blockers Summary

| Blocker | Required For | Status |
|---------|-------------|--------|
| HT-014: Facebook Page + Developer App | Phase C (facebook_mcp) | PENDING |
| HT-015: Instagram Business Account | Phase C (facebook_mcp) | PENDING |
| HT-016: Twitter/X Developer App | Phase D (twitter_mcp) | PENDING |
| Anthropic credits top-up | LLM-assisted briefing draft (FR-005) | PENDING |

**Start immediately** (no blockers): Phase A, B, E, F, H, J, K partial.
**Start after HT**: Phase C, D, G.
