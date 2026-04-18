# Research: Full Communication Automation (Phase 6.5)

**Branch**: `011-full-comms-automation` | **Date**: 2026-04-11

---

## 1. WhatsApp MCP — Existing Capabilities (VERIFIED)

**Decision**: WhatsApp MCP Python server is minimal (text-only). Phase D must add all media, group, status, and contact tools to `mcp_servers/whatsapp/server.py` plus extend the Go bridge for media.

**Findings** (verified by research agent):
- Python MCP server: `mcp_servers/whatsapp/server.py` — **2 tools only**: `send_message`, `health_check`
- No `send_file`, `send_audio`, group, status, or contact tools in MCP
- Go bridge HTTP API (`http://localhost:8080`): likely supports more operations (whatsmeow library) — bridge extension needed for media send, group create, status post
- Architecture: pluggable backends via `WHATSAPP_BACKEND` env var (`go_bridge` or `pywa`)
- Existing watcher: `watchers/whatsapp_watcher.py` — reads incoming messages only (text), routes through `privacy_gate.py`

**FURTHER CORRECTION (found during /sp.adr)**: Go bridge already exposes rich MCP tools DIRECTLY via `.mcp.json`, not through Python wrapper. Live tools confirmed: `send_file`, `send_audio_message`, `download_media`, `list_chats`, `list_messages`, `search_contacts`, `get_chat`, `get_contact_chats`, `get_last_interaction`, `get_message_context`. Only 3 Go HTTP endpoints still missing: `/status`, `/group`, `/profile`. See ADR-0022.

Phase D scope is now SMALLER — media send already available via bridge MCP tools. Python wrapper adds only business logic (HITL gate, rate limiter, PII masking, broadcast cap).

**Rationale**: Go bridge (whatsmeow) already exposes capabilities via MCP. Build on what exists.

**Alternatives considered**:
- Build a new Python bridge: Rejected — existing Go bridge is stable and authenticated.
- Use unofficial python-whatsapp-business: Rejected — requires Facebook Business API approval.

---

## 2. Gmail MCP — Current State (VERIFIED)

**Decision**: Gmail MCP already has write capability (send, move, label) and correct OAuth scopes. Phase B adds ONLY the missing tools: draft management, classify_inbox, attachment flagging, trash, auto-reply.

**Findings** (verified by research agent):
- Current tools (6): `health_check`, `send_email`, `list_emails`, `get_email`, `move_email`, `add_label`
- OAuth scopes ALREADY include: `gmail.readonly`, `gmail.send`, `gmail.modify` — **no re-auth needed**
- `send_email` already supports reply_to_message_id (thread replies)
- `move_email` supports moving to any Gmail label/folder
- `add_label` supports creating labels if they don't exist

**What's still missing for Phase B**:
- `create_draft` / `send_draft` (staged send with HITL gate)
- `trash_emails` (bulk move to Trash)
- `classify_inbox` (triggers Tier 0/1 classifier on inbox)
- `get_attachment_flags` (OTP/password/fraud detection)
- `send_auto_reply` (template-based auto-reply)
- `get_daily_summary` (inbox summary for briefing)

**Corrections to plan**: Phase B scope is SMALLER. OAuth re-auth not needed. `send_email` already works — focus on draft management and classification tooling.

**Rationale**: Extending existing server avoids duplication. Existing scopes sufficient.

---

## 3. Google Calendar — Current OAuth Scope

**Decision**: Calendar MCP uses `calendar.readonly` scope. Phase C re-auths with full `calendar` scope.

**Findings**:
- Current scope in `scripts/calendar_auth.py`: `SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]`
- Full write scope: `https://www.googleapis.com/auth/calendar`
- Re-auth deletes existing `token_calendar.json` and re-runs WSL2 code-paste flow
- `OAUTHLIB_RELAX_TOKEN_SCOPE=1` already set in `scripts/calendar_auth.py`
- Google Calendar API supports: events.insert, events.update, events.delete, events.list, freebusy.query (conflict detection)

**Rationale**: Scope upgrade is a single-line change in `calendar_auth.py` + re-auth. No new library needed.

---

## 4. OpenRouter Free Models — API Format & Model Selection

**Decision**: Use OpenRouter with OpenAI-compatible client. Primary: `google/gemini-flash-1.5`, secondary: `qwen/qwen2.5-72b-instruct:free`, tertiary: `mistralai/mistral-7b-instruct:free`.

**Findings**:
- API base URL: `https://openrouter.ai/api/v1`
- Authentication: `Authorization: Bearer $OPENROUTER_API_KEY`
- Format: OpenAI Chat Completions compatible (works with `openai` Python client)
- Free models (as of 2026-04): google/gemini-flash-1.5, qwen/qwen2.5-72b-instruct:free, mistralai/mistral-7b-instruct:free
- Rate limits (free tier): ~20 req/min per model; round-robin across 3 models = effective 60 req/min

**Implementation**:
```python
from openai import AsyncOpenAI

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

async def tier1_classify(prompt: str, model: str = "google/gemini-flash-1.5") -> str:
    response = await openrouter_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,  # classification responses are short
    )
    return response.choices[0].message.content
```

**Rationale**: OpenAI-compatible API means zero new SDK to learn. `openai` package already likely in requirements. Round-robin provides rate limit resilience.

**Alternatives considered**:
- Direct Google Gemini API: Rejected — separate SDK, separate auth flow. OpenRouter unifies all free models.
- Ollama (local): Rejected — GPU/RAM requirement in WSL2 (ADR-0020 Alternative C).

---

## 5. HITL Manager — Existing Implementation (VERIFIED)

**Decision**: `orchestrator/hitl_manager.py` already exists with a vault-filesystem state machine. Phase A EXTENDS this rather than building from scratch. Add non-blocking behavior and pending-queue briefing integration.

**Findings** (verified by research agent):
- File: `orchestrator/hitl_manager.py` — full HITLManager class
- State machine: vault filesystem (`vault/Pending_Approval/` → `vault/Approved/` / `vault/Rejected/`)
- Draft format: YAML frontmatter + markdown body (platform, status, draft_id, priority, risk_level)
- `submit_draft()`: writes to Pending_Approval, queues notification
- `send_batch_notification()`: single WhatsApp summary for all pending (max 5 concurrent)
- `handle_owner_reply()`: parse "approve <id>" / "reject <id>" from WhatsApp
- `check_timeouts()`: 24h reminder, 48h timeout enforcement
- `_approve()` / `_reject()`: dispatch by action type, call Gmail MCP for email drafts
- Audit log: `vault/Logs/hitl_decisions.jsonl`
- In-memory notification queue: Python list of draft_ids (NOT persistent)

**Gap for Phase A**: In-memory queue is lost on process restart. Non-blocking (fire-and-forget) behavior needs to be added — current implementation has 24h/48h timeout enforcement which needs relaxing per Q1 clarification (indefinite queue).

**Phase A work**:
- Extend `hitl_manager.py` to add persistent queue (SQLite or vault file) for cross-restart durability
- Remove hard timeout enforcement (per Q1 clarification: queue indefinitely)
- Add `get_pending_for_briefing()` method for daily briefing reminders
- Add support for all Phase 6.5 action types (WhatsApp media, calendar, LinkedIn, social)

**Rationale**: Building on the existing manager reuses battle-tested vault state machine. Less risk than a full rebuild.

---

## 6. LinkedIn Messaging API — Application Process

**Decision**: Apply for LinkedIn Messaging API partner access. DMs deferred to Phase 7 if rejected.

**Findings**:
- Application: https://developer.linkedin.com/partner-programs/messaging
- Required: LinkedIn Developer App (already created for Phase 6 OAuth)
- Scopes needed if approved: `r_1st_connections_size`, `r_emailaddress`, `w_messages`
- Review time: typically 2-4 weeks
- Alternative: `r_messaging` scope (LinkedIn Recruiter Messaging) — separate product

**Action (HT)**: CEO applies via LinkedIn Developer portal. Approval is gate for Phase E DM tools.

---

## 7. Greeting Classifier — Multi-Language Pattern Coverage

**Decision**: Regex-based Tier 0 classifier with a curated YAML pattern file.

**Greeting patterns confirmed for `classifiers/greeting_patterns.yaml`**:
```yaml
greeting:
  - "assalam o alaikum"
  - "assalamualaikum"
  - "as-salamu alaykum"
  - "namaste"
  - "namaskar"
  - "sat sri akal"
  - "jai shri krishna"
  - "hello"
  - "hi "
  - "hey "
  - "good morning"
  - "good afternoon"
  - "good evening"
thanks:
  - "thank you"
  - "thanks"
  - "shukriya"
  - "شکریہ"
  - "jazakallah"
  - "barakallah"
  - "dhanyawad"
congrats:
  - "congratulations"
  - "congrats"
  - "mubarak"
  - "مبارک"
  - "well done"
  - "great job"
  - "amazing work"
```

**Matching logic**: lowercase(email_subject + first_50_chars_of_body), any pattern match = greeting category.

---

## 8a. Social MCP Analytics Gap (VERIFIED — NEW FINDING)

**Decision**: All 3 social MCPs (LinkedIn, Facebook, Twitter) have ZERO analytics/read tools beyond basic post listing. Phase E, F, and G need analytics tools added to each.

**Findings**:
- LinkedIn: `post_update`, `get_profile`, `health_check` only. No impressions, no follower data.
- Facebook: `post_update`, `post_facebook_only`, `post_instagram_only`, `get_recent_posts`, `health_check`. No page analytics, no comment reading, no DM access.
- Twitter: `post_tweet`, `get_recent_tweets`, `health_check`. No tweet analytics, no DM access (403 Free tier).

**Social DM Monitor** (`watchers/social_dm_monitor.py`): Polls Facebook/Instagram/Twitter DMs using direct REST API calls (not MCP). Keyword-match escalation only — does NOT read full DM content.

**Impact on plan**:
- LinkedIn analytics (Phase E): Need to add `get_analytics()` tool using LinkedIn Analytics API v2
- Facebook/Instagram analytics (Phase F): Need to add `get_page_analytics()` using Meta Insights API
- Twitter analytics (Phase F): Need to add `get_tweet_analytics()` using Twitter v2 organic metrics (requires Basic tier or higher)
- Comment reading (Phase F): Need to add `list_comments()` + `reply_comment()` to Facebook MCP
- DM tools (Phase F): Facebook Messenger API supports DM reading — can add to Facebook MCP

**8b. Classifiers Gap (VERIFIED — NEW FINDING)**

**Decision**: No `classifiers/` directory exists. Gmail watcher has embedded keyword classification — extract this pattern into a standalone reusable module in Phase A.

**Findings**:
- `watchers/gmail_watcher.py`: `_classify_email()` method with keyword scoring (ACTIONABLE vs INFORMATIONAL)
- `watchers/social_dm_monitor.py`: `should_escalate()` keyword matching
- `watchers/privacy_gate.py`: redaction patterns (OTP, password, card, API key) — reuse in Phase B attachment flagging
- No standalone classifier module

**Phase A**: Create `classifiers/` directory, extract/enhance classification logic from watchers, add multi-language greeting patterns.

## 8. Rate Limiter Implementation

**Decision**: SQLite-backed daily counters in `vault/rate_limits.db`. Reset at midnight UTC.

**Pattern** (reuse across all platforms):
```python
async def check_and_increment(platform: str, action_type: str, daily_limit: int) -> bool:
    today = date.today().isoformat()
    async with aiosqlite.connect("vault/rate_limits.db") as db:
        row = await db.execute_fetchone(
            "SELECT count_today FROM rate_limits WHERE platform=? AND action_type=? AND date=?",
            (platform, action_type, today)
        )
        current = row[0] if row else 0
        if current >= daily_limit:
            return False  # limit hit
        await db.execute("""
            INSERT INTO rate_limits (platform, action_type, count_today, daily_limit, date)
            VALUES (?, ?, 1, ?, ?)
            ON CONFLICT(platform, action_type) DO UPDATE SET count_today = count_today + 1
        """, (platform, action_type, daily_limit, today))
        await db.commit()
        return True  # proceed
```
