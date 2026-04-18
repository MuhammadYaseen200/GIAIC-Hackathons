# Implementation Plan: Full Communication Automation (Phase 6.5)

**Branch**: `011-full-comms-automation` | **Date**: 2026-04-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-full-comms-automation/spec.md`

---

## Summary

Phase 6.5 extends the Personal AI Employee from a notification/briefing system into a full communication management platform. The AI Employee gains read/write/manage capabilities across 5 platform groups (WhatsApp, Gmail, LinkedIn, Google Calendar, Social) with HITL guardrails on every irreversible action.

**Technical approach**: Extend all 5 existing MCP servers with write/manage tools. Add a persistent, non-blocking HITL queue (SQLite). Implement a three-tier model routing system (ADR-0020): rule-based classifiers → free models (OpenRouter) → strong model (Anthropic), routed by task type. All new tools follow the MCP-first architecture (Constitution §IV).

---

## Technical Context

**Language/Version**: Python 3.13+ (existing codebase standard)
**Primary Dependencies**:
- Existing: `anthropic`, `google-auth`, `google-api-python-client`, `tweepy`, `requests`, `aiosqlite`, `fastmcp`, `python-dotenv`
- New (Phase 6.5): `openai` (OpenRouter-compatible client), `aiosqlite` (HITL queue), `regex` (classifier patterns), `pyyaml` (routing config)
**Storage**: SQLite (HITL queue, contact records) + Obsidian vault markdown (briefings, logs) — local-first per Constitution §II
**Testing**: `pytest` + `pytest-asyncio` + existing `tests/unit/`, `tests/contract/`, `tests/integration/` structure
**Target Platform**: Linux/WSL2 (existing), Python CLI + cron scheduling
**Performance Goals**:
- WhatsApp command → HITL sent: ≤5s (non-blocking; agent queues and moves on)
- Gmail categorization of 100 emails: ≤10s
- Cross-platform daily summary: ≤30s (SC-010)
- LinkedIn post publish after HITL approval: ≤30s (SC-004)
**Constraints**:
- WhatsApp bulk: ≤10 recipients/broadcast (FR-040)
- LinkedIn DMs: ≤5/day auto-drafted (FR-025)
- LinkedIn connections: ≤20/day auto-accept (FR-040)
- Tier 1 (free models): metadata only, never full message body (FR-043, ADR-0020)
- No secrets hardcoded; all credentials via `.env` (Constitution §IX)
**Scale/Scope**: Single CEO user. Estimated daily volume: ~50 emails, ~20 WhatsApp messages, ~5 LinkedIn interactions, ~5 calendar events, ~3 social posts.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Check | Status |
|-----------|-------|--------|
| I. Spec-Driven Development | spec.md written + clarified + ADR-0020 created | PASS |
| II. Local-First Privacy | All data in vault/; SQLite queue local; Tier 1 metadata-only (FR-043) | PASS |
| III. Human-in-the-Loop | FR-038: 100% irreversible actions require HITL; non-blocking queue (Q1) | PASS |
| IV. MCP-First External Actions | All 5 platform groups extend existing MCP servers; no direct API calls | PASS |
| V. Test-Driven Quality | TDD per phase; unit + contract + integration; >80% coverage target | PASS |
| VI. Watcher Architecture | New watchers inherit BaseWatcher | PASS |
| VII. Phase-Gated Delivery | Phase 6 complete + merged to main | PASS |
| VIII. Reusable Intelligence | ADR-0020 created; PHRs tracked; classifiers extractable as skills | PASS |
| IX. Security by Default | FR-039 PII-free logs; FR-043 metadata-only Tier 1; .env credentials | PASS |
| X. Graceful Degradation | HITL queue survives bridge offline; classifier fallback chain; retry on API error | PASS |

**Constitution Check: ALL PASS. Phase 0 cleared.**

---

## Project Structure

### Documentation (this feature)

```text
specs/011-full-comms-automation/
├── plan.md              <- This file
├── research.md          <- Phase 0 output
├── data-model.md        <- Phase 1 output
├── quickstart.md        <- Phase 1 output
├── contracts/           <- Phase 1 output
│   ├── whatsapp-tools.md
│   ├── gmail-tools.md
│   ├── calendar-tools.md
│   ├── linkedin-tools.md
│   └── social-tools.md
├── checklists/
│   └── requirements.md
└── tasks.md             <- /sp.tasks output (NOT created here)
```

### Source Code (repository root)

```text
mcp_servers/
├── gmail/
│   ├── server.py           <- Extend: draft/send/label/delete/search/auto_reply tools
│   └── auth.py             <- Update: gmail.send + gmail.modify + gmail.labels scopes
├── calendar/
│   ├── server.py           <- Extend: create/update/delete_event + conflict check
│   └── auth.py             <- Update: full `calendar` scope (not readonly)
├── linkedin/
│   ├── server.py           <- Extend: profile_write, analytics, connections, search
│   ├── auth.py             <- Existing OAuth2
│   └── dm_server.py        <- NEW: DM tools (gated on LinkedIn Messaging API access)
├── facebook/
│   └── server.py           <- Extend: comments, DMs, analytics tools
├── twitter/
│   └── server.py           <- Extend: DMs (gated), analytics, replies
└── whatsapp/
    └── server.py           <- Extend/wrap: media send, group mgmt, status, contact save

classifiers/
├── __init__.py
├── email_classifier.py     <- NEW: Tier 0 rule-based + Tier 1 routing (ADR-0020)
├── dm_classifier.py        <- NEW: intent classifier for WhatsApp/LinkedIn/Social
├── greeting_patterns.yaml  <- NEW: multi-language greeting patterns (FR-012)
└── sensitive_patterns.yaml <- NEW: OTP/password/fraud detection patterns (FR-014)

orchestrator/
├── ceo_briefing.py         <- Update: add pending_hitl_section() + cross_platform_summary()
├── weekly_audit.py         <- No changes needed
├── hitl_queue.py           <- NEW: persistent non-blocking HITL queue (SQLite)
└── social_poster.py        <- Existing

watchers/
├── gmail_reply_watcher.py  <- NEW: monitors HITL-approved drafts + auto-reply queue
└── linkedin_monitor.py     <- NEW: monitors feed, DMs, connection requests

config/
├── model_routing.yaml          <- NEW: ADR-0020 three-tier routing config
├── auto_reply_templates.yaml   <- NEW: FR-012 pre-written reply templates
└── linkedin_interests.yaml     <- NEW: keywords for LinkedIn feed monitoring

tests/
├── unit/
│   ├── test_email_classifier.py
│   ├── test_dm_classifier.py
│   ├── test_hitl_queue.py
│   ├── test_gmail_mcp_write.py
│   ├── test_calendar_mcp_write.py
│   ├── test_linkedin_mcp_extended.py
│   ├── test_whatsapp_mcp_media.py
│   └── test_social_mcp_extended.py
├── contract/
│   ├── test_gmail_contracts.py
│   ├── test_calendar_contracts.py
│   └── test_whatsapp_contracts.py
└── integration/
    ├── test_hitl_full_flow.py
    └── test_gmail_triage_flow.py
```

---

## Implementation Phases

### Phase A — Infrastructure Layer

**Goal**: Build foundations everything else depends on. No platform-specific features yet.

**NOTE (verified)**: `orchestrator/hitl_manager.py` already exists with vault filesystem state machine. Gmail MCP already has write scopes and `send_email`. WhatsApp MCP has text-only. Phase A extends what exists.

**Deliverables**:
- `orchestrator/hitl_manager.py` — EXTEND existing: add persistent queue, remove hard timeout, add `get_pending_for_briefing()`, support Phase 6.5 action types
- `orchestrator/hitl_queue.py` — NEW: thin SQLite persistence layer called by hitl_manager for cross-restart durability
- `config/model_routing.yaml` — ADR-0020 three-tier routing config
- `config/auto_reply_templates.yaml` — FR-012 greeting templates (multi-language)
- `classifiers/email_classifier.py` — Tier 0 rule-based + Tier 1 OpenRouter integration
- `classifiers/dm_classifier.py` — intent classifier for DMs
- `classifiers/greeting_patterns.yaml` — Assalam o Alaikum, Namaste, Hi, etc.
- `classifiers/sensitive_patterns.yaml` — OTP, password, fraud link patterns

**HITL Queue design** (`orchestrator/hitl_queue.py`):
```python
# SQLite schema (vault/hitl_queue.db):
# id TEXT PRIMARY KEY
# platform TEXT
# action_type TEXT
# summary TEXT        (<=500 chars, SC-002)
# content_ref TEXT    (JSON blob — full content stored locally)
# status TEXT         ('pending'|'approved'|'declined'|'executed'|'failed')
# sent_at TIMESTAMP
# responded_at TIMESTAMP NULL
# retry_count INTEGER DEFAULT 0

async def enqueue(action: CommunicationAction) -> str  # non-blocking, returns queue_id
async def approve(queue_id: str) -> None
async def decline(queue_id: str) -> None
async def get_pending() -> list[HITLRequest]  # for briefing reminders
async def execute_approved() -> list[str]     # process all approved items
```

**Model routing config** (`config/model_routing.yaml`):
```yaml
tier0_tasks:   # Rule-based, zero LLM cost
  - greeting_detection
  - spam_keyword_match
  - otp_flag
  - password_attachment_flag
  - duplicate_post_check

tier1_tasks:   # Free model via OpenRouter (metadata only, FR-043)
  - email_categorization
  - dm_intent_classification
  - calendar_event_extraction
  - short_summarization

tier2_tasks:   # Anthropic claude-sonnet-4-6
  - sensitive_email_draft
  - ceo_briefing_synthesis
  - linkedin_post_draft
  - complex_whatsapp_reply

tier1_providers:
  primary:   "google/gemini-flash-1.5"
  secondary: "qwen/qwen2.5-72b-instruct:free"
  tertiary:  "mistralai/mistral-7b-instruct:free"

privacy:
  tier1_content: "metadata_only"  # FR-043: never full body to Tier 1
```

**Tests (TDD — write first)**:
- `test_hitl_queue.py`: enqueue, approve, decline, persist across restart, get_pending
- `test_email_classifier.py`: greeting detection for 10 languages, OTP, spam keywords
- `test_dm_classifier.py`: job inquiry / networking / spam / sales intent

**Exit criteria**: Classifier tests green; HITL queue survives process restart; routing config loads cleanly.

---

### Phase B — Gmail Write & Triage

**Goal**: Full Gmail inbox management — classify, label, auto-reply, draft, HITL-approved send.

**OAuth scope** (VERIFIED): Gmail MCP already has `gmail.readonly + gmail.send + gmail.modify` — NO re-auth needed. Existing `send_email`, `move_email`, `add_label` tools already work.

**New tools** added to `mcp_servers/gmail/server.py`:
```python
async def create_draft(to, subject, body, reply_to_id=None) -> DraftResult
async def send_draft(draft_id) -> SendResult         # HITL-approved only
async def send_email(to, subject, body) -> SendResult # direct (low-stakes only)
async def label_emails(message_ids, labels) -> LabelResult
async def archive_emails(message_ids) -> ArchiveResult
async def trash_emails(message_ids) -> TrashResult   # NOT permanent delete
async def search_emails(query, max_results=50) -> EmailList
async def classify_inbox(max_emails=100) -> ClassificationReport
async def get_attachment_flags(message_id) -> AttachmentFlags
async def send_auto_reply(message_id, template_key) -> SendResult
```

**Labels created** (FR-011):
`AI_Urgent`, `AI_Opportunity`, `AI_Promotional`, `AI_Spam`, `AI_OTC` (one-time code), `AI_Routine`, `AI_SensitiveAttachment`

**HITL flow** for sensitive emails:
```
classify → sensitive → create_draft() → enqueue_hitl(summary) →
WhatsApp message sent (non-blocking) → CEO replies "yes" →
execute_approved() → send_draft()
```

**Auto-reply flow** (no HITL, Tier 0):
```
email arrives → classifier detects greeting/thanks/congrats →
select_template(template_key) → send_auto_reply() → log to vault
```

**Watcher** (`watchers/gmail_reply_watcher.py`):
- Polls every 60s for: new emails to classify, HITL-approved drafts to send, auto-reply queue
- Writes daily triage report to `vault/Logs/gmail_triage_YYYY-MM-DD.md`

**Exit criteria**: Inbox classify labels 85%+ correctly; draft created for sensitive email without sending; auto-reply sent for greeting without HITL.

---

### Phase C — Google Calendar Write

**Goal**: Full calendar CRUD — create, update, delete events, extract from emails, detect conflicts.

**OAuth scope change**: `calendar.readonly` → `calendar` (full read/write)
- Re-run `scripts/calendar_auth.py` with updated scope constant

**New tools** added to `mcp_servers/calendar/server.py`:
```python
async def create_event(title, start, end, attendees=None, location=None,
                        description=None, notify_attendees=True) -> EventResult
async def update_event(event_id, **updates) -> EventResult
async def delete_event(event_id, notify_attendees=True) -> DeleteResult
async def check_conflicts(start, end) -> ConflictCheck  # called before every create
async def create_focus_block(start, end, title="Focus Time") -> EventResult
async def extract_event_from_email(email_body) -> EventProposal  # Tier 1 model
```

**Conflict detection** (FR-029): Before every `create_event`, call `check_conflicts`. Conflict found → return both events to CEO, never auto-resolve.

**Gmail integration** (FR-031): `extract_event_from_email` uses Tier 1 model on email metadata → `EventProposal` → CEO confirms via HITL.

**Exit criteria**: Event appears in Google Calendar; conflict detected for overlapping times; cancellation notification sent to attendees on delete.

---

### Phase D — WhatsApp Media & Management

**Goal**: Full media send, group management, status, contact save.

**Note (CORRECTED by research)**: WhatsApp MCP currently has ONLY `send_message` + `health_check`. ALL media, group, status, and contact tools must be built. Go bridge HTTP API needs new endpoints for media/group/status — then Python MCP wraps them.

**New/extended tools** in `mcp_servers/whatsapp/server.py`:
```python
# Media (wrap existing bridge tools)
async def send_image(to, path, caption=None) -> SendResult
async def send_video(to, path, caption=None) -> SendResult
async def send_document(to, path, filename) -> SendResult
async def send_location(to, lat, lng, name=None) -> SendResult

# Groups
async def create_group(name, members, description=None) -> GroupResult
async def get_group_info(group_id) -> GroupInfo
async def add_group_member(group_id, contact) -> GroupResult

# Status
async def post_status(content, media_path=None, privacy="contacts") -> StatusResult
async def delete_status(status_id) -> DeleteResult

# Contacts
async def save_contact(name, phone, ceo_verified=True) -> ContactResult
async def get_contact_info(query) -> ContactInfo  # search by name or number

# Organization
async def mark_read(chat_id) -> Result
async def archive_chat(chat_id) -> Result
async def star_message(message_id) -> Result
async def get_unread_summary() -> UnreadSummary  # prioritized list
```

**Business WhatsApp** (FR-008): Second bridge on port 8081.
Config: `WHATSAPP_BRIDGE_URL_BUSINESS=http://localhost:8081` in `.env`.

**HITL on all outbound**: Every send → `enqueue_hitl()` → non-blocking.

**Bulk cap** (FR-040): `broadcast()` enforces ≤10 recipients; raises `WhatsAppBanRiskError` if exceeded.

**Exit criteria**: Image sent to test contact after HITL; group created; status posted; contact saved with verification; >10 broadcast refused.

---

### Phase E — LinkedIn Extension

**Goal**: Profile write, analytics, connections, search, save/react. DMs gated on API access.

**New tools** in `mcp_servers/linkedin/server.py`:
```python
# Profile
async def update_profile_field(field, value) -> ProfileResult
  # fields: headline, summary, current_position, open_to_work, hiring_status
async def upload_resume(file_path) -> ResumeResult

# Engagement
async def react_post(post_id, reaction="like") -> ReactionResult
async def comment_post(post_id, text) -> CommentResult
async def repost(post_id, commentary=None) -> RepostResult
async def save_post(post_id) -> SaveResult

# Connections
async def list_pending_connections(filter=None) -> ConnectionList
async def accept_connection(profile_id) -> ConnectionResult  # rate-limited: 20/day
async def reject_connection(profile_id) -> ConnectionResult
async def send_connection_request(profile_id, note=None) -> ConnectionResult
async def unconnect(profile_id) -> ConnectionResult
async def block_profile(profile_id) -> BlockResult
async def follow_profile(profile_id) -> FollowResult

# Search
async def search_profiles(query, filters=None) -> SearchResults

# Analytics
async def get_analytics(period="7d") -> AnalyticsReport
  # impressions, profile_views, post_reach, follower_growth, top_post
```

**DM gate** (`mcp_servers/linkedin/dm_server.py`):
```python
LINKEDIN_DM_ENABLED = bool(os.getenv("LINKEDIN_MESSAGING_API_KEY"))
# Raises LinkedInDMUnavailable with application URL if not set
```

**Rate limiters** (FR-025, FR-040): SQLite counters in `vault/rate_limits.db`
- DMs: 5/day
- Connection accepts: 20/day

**Exit criteria**: Profile headline updated; analytics returned; connection accepted; post reacted to; DM gate raises informative error.

---

### Phase F — Social Media Extension (Facebook / Instagram / Twitter)

**Goal**: Comments, DMs, analytics for all 3 social platforms.

**Facebook/Instagram** (extends `mcp_servers/facebook/server.py`):
```python
async def list_comments(post_id) -> CommentList
async def reply_comment(comment_id, text) -> CommentResult
async def delete_comment(comment_id) -> DeleteResult
async def hide_comment(comment_id) -> HideResult
async def list_dms(platform="facebook") -> DMList
async def reply_dm(conversation_id, message) -> DMResult
async def get_page_analytics(period="7d") -> PageAnalytics
```

**Twitter** (extends `mcp_servers/twitter/server.py`):
```python
async def reply_tweet(tweet_id, text) -> TweetResult
async def quote_tweet(tweet_id, comment) -> TweetResult
async def like_tweet(tweet_id) -> LikeResult
async def follow_user(user_id) -> FollowResult
async def unfollow_user(user_id) -> FollowResult
async def list_dms() -> DMList               # GATED: Twitter Basic tier required
async def reply_dm(dm_id, message) -> DMResult  # GATED
async def get_tweet_analytics(period="7d") -> TweetAnalytics
```

**Spam detection** (FR-035): Tier 0 classifier on comment text → auto-hide on match → CEO notified in briefing.

**Exit criteria**: Comment listed and replied to; DM reply queued for HITL; analytics returned; spam comment hidden.

---

### Phase G — Orchestrator & Briefing Updates

**Goal**: CEO briefing shows pending HITL queue + cross-platform daily summary. LinkedIn monitor watcher running.

**Updates to `orchestrator/ceo_briefing.py`**:
```python
async def collect_pending_hitl_section() -> str:
    # Pull pending from hitl_queue.get_pending()
    # Format: "PENDING APPROVALS (3):\n- [WhatsApp->Ahmed] Reply drafted\n- ..."

async def collect_cross_platform_summary() -> str:
    # asyncio.gather() all 5 platform analytics in parallel (SC-010: <=30s)
```

**New watcher** (`watchers/linkedin_monitor.py`):
- Polls LinkedIn feed every 15 min
- Writes `vault/Needs_Action/linkedin_YYYY-MM-DD-HH-MM.md` for: new DMs, new connections, posts matching `config/linkedin_interests.yaml`

**Exit criteria**: Briefing includes pending HITL section when queue non-empty; cross-platform summary within 30s; LinkedIn monitor writes vault files.

---

### Phase H — Tests, Security & QA

**Test coverage targets**:
- `classifiers/`: 90%+
- `orchestrator/hitl_queue.py`: 90%+
- All new MCP server tools: 80%+
- New watchers: 80%+

**Security scan checklist**:
- Tier 1 never receives full message body
- No hardcoded credentials in any new file
- HITL queue SQLite not world-readable
- Rate limiters enforce platform caps
- PII not in vault/Logs/ entries

**QA gate**: All 30 acceptance scenarios from spec.md verified. SC-001 through SC-010 measurable outcomes confirmed.

---

## Complexity Tracking

| Concern | Why Needed | Simpler Alternative Rejected Because |
|---------|------------|--------------------------------------|
| Three-tier model routing | Token cost grows linearly without routing | Single-model burns credits on greeting detection; proven in Q3 |
| SQLite HITL queue | Non-blocking queue survives restart | In-memory dict lost on crash; JSON has race conditions |
| Dual WhatsApp bridge | Business account dev/test separate | Same bridge mixes personal + business messages |
| LinkedIn DM API gate | Partner access required | Browser automation = ToS violation + ban risk (Q4) |

---

## Dependencies & Human Tasks

| Item | Status | Owner | Action Required |
|------|--------|-------|-----------------|
| Gmail write OAuth re-auth | Pending | CEO + Agent | Re-auth after `scripts/gmail_write_auth.py` is built (Phase B) |
| Calendar write OAuth re-auth | Pending | CEO + Agent | Re-run `scripts/calendar_auth.py` with updated scope (Phase C) |
| LinkedIn Messaging API | Blocked | CEO | Apply at developer.linkedin.com partner program |
| WhatsApp Business bridge | Dev/Test | CEO | Family member's account; run second bridge on port 8081 |
| OpenRouter API key | Required | CEO | Sign up openrouter.ai; add `OPENROUTER_API_KEY` to `.env` |
| Twitter Basic tier | Optional | CEO | Upgrade if Twitter DM feature required; otherwise deferred |
