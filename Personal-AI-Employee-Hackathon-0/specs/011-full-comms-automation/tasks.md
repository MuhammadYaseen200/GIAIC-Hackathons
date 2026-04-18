# Tasks: Full Communication Automation (Phase 6.5)

**Input**: Design documents from `/specs/011-full-comms-automation/`
**Branch**: `011-full-comms-automation` | **Generated**: 2026-04-12
**Prerequisites**: spec.md ✅ | plan.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ (5 files) | ADRs: 0020-0023 ✅

**Total tasks**: 89 across 9 phases
**User stories**: US1 (P1) WhatsApp · US2 (P2) Gmail · US3 (P3) LinkedIn · US4 (P4) Calendar · US5 (P5) Social

---

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Parallelizable — different files, no unresolved dependencies
- **[US1–US5]**: Maps to user story from spec.md
- All file paths relative to repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directories, install dependencies, stub files. No implementation yet.

- [ ] T001 Create `classifiers/` Python package: `classifiers/__init__.py`
- [ ] T002 [P] Create skeleton YAML config files: `config/model_routing.yaml`, `config/auto_reply_templates.yaml`, `config/linkedin_interests.yaml` (empty stubs with top-level key only)
- [ ] T003 [P] Verify `openai` and `aiosqlite` in `requirements.txt`; add if missing (Phase 6.5 new deps per plan.md §Technical Context)
- [ ] T004 [P] Create empty test stub files: `tests/unit/test_hitl_queue.py`, `tests/unit/test_email_classifier.py`, `tests/unit/test_dm_classifier.py`
- [ ] T005 [P] Create vault database placeholders: `touch vault/hitl_queue.db vault/contacts.db vault/rate_limits.db` and set permissions `chmod 600` on each (SC-009 security)

**Checkpoint**: Directories exist, deps installed, stubs ready.

---

## Phase 2: Foundation — Phase A Infrastructure

**Purpose**: Core infrastructure ALL user stories depend on. HITL queue, classifiers, model routing, rate limiters.

**⚠️ CRITICAL**: No US1–US5 work can begin until this phase is complete.

- [ ] T006 Implement `orchestrator/hitl_queue.py` — SQLite schema for `CommunicationAction` table (all fields from data-model.md), WAL mode, `(status, sent_at)` index on `vault/hitl_queue.db`
- [ ] T007 Implement `orchestrator/hitl_queue.py` — async functions: `enqueue(action) → str`, `approve(queue_id)`, `decline(queue_id)`, `get_pending() → list[HITLRequest]`, `execute_approved() → list[str]` (non-blocking pattern, ADR-0021)
- [ ] T008 Extend `orchestrator/hitl_manager.py` — add SQLite persistence via `hitl_queue.enqueue()` (dual write: vault file + SQLite); remove 24h/48h hard timeout enforcement; add `get_pending_for_briefing()` method; extend `ActionType` enum: `whatsapp_text`, `whatsapp_media`, `whatsapp_group_create`, `whatsapp_status`, `linkedin_post`, `linkedin_react`, `linkedin_comment`, `linkedin_connect`, `facebook_post`, `facebook_reply`, `twitter_post`, `twitter_reply`, `calendar_create`, `calendar_delete`, `gmail_draft_send`
- [ ] T009 [P] Implement `ContactRecord` SQLite schema in `orchestrator/hitl_queue.py` or a new `db/contacts_db.py` — all fields from data-model.md; `ceo_verified=False` default; `UNIQUE(phone_number)` + `UNIQUE(email_address)` indexes on `vault/contacts.db`
- [ ] T010 [P] Implement `RateLimitCounter` SQLite schema + `check_and_increment(platform, action_type, daily_limit) → bool` in `orchestrator/hitl_queue.py` — daily counters reset at midnight UTC; default limits: `linkedin_dms=5`, `connection_accept=20`, `whatsapp_bulk=10`; uses `vault/rate_limits.db`
- [ ] T011 [P] Write `config/model_routing.yaml` — `tier0_tasks`, `tier1_tasks`, `tier2_tasks` lists; `tier1_providers` (primary: `google/gemini-flash-1.5`, secondary: `qwen/qwen2.5-72b-instruct:free`, tertiary: `mistralai/mistral-7b-instruct:free`); `privacy.tier1_content: metadata_only` (ADR-0020 §Model routing config)
- [ ] T012 [P] Write `config/auto_reply_templates.yaml` — `greeting_universal`, `thanks_universal`, `congrats_universal` keys; each with `en`, `ur`, `ar`, `hi` language variants (FR-012; data-model.md §Configuration Files)
- [ ] T013 [P] Write `config/linkedin_interests.yaml` — `keywords` list and `hiring_signals` list (plan.md Phase G; data-model.md §linkedin_interests.yaml)
- [ ] T014 [P] Write `classifiers/greeting_patterns.yaml` — `greeting`, `thanks`, `congrats` pattern lists covering multi-language variants (research.md §7: Assalam o Alaikum, Namaste, Sat Sri Akal, Hi, Hello, Good morning, JazakAllah, Shukriya, Mubarak, etc.)
- [ ] T015 [P] Write `classifiers/sensitive_patterns.yaml` — OTP patterns, password patterns, fraud link indicators, legal document keywords, PII attachment signals (FR-014; research.md §8b: reuse `watchers/privacy_gate.py` redaction patterns)
- [ ] T016 Implement `classifiers/email_classifier.py` — `classify_email(subject, sender_domain, body_preview, has_attachment) → EmailClassification`; Tier 0: load `greeting_patterns.yaml` + `sensitive_patterns.yaml` and return rule-based result (confidence=1.0); Tier 1 fallback: send metadata-only to OpenRouter via `openai.AsyncOpenAI(base_url="https://openrouter.ai/api/v1")` using model from `config/model_routing.yaml` (FR-043: never full body to Tier 1)
- [ ] T017 [P] Implement `classifiers/dm_classifier.py` — `classify_dm_intent(sender, message_preview, platform) → DMClassification`; intents: `job_inquiry`, `networking`, `spam`, `sales`, `unknown`; Tier 0 keyword rules first; Tier 1 fallback via OpenRouter (metadata only); used by WhatsApp watcher and LinkedIn monitor
- [ ] T018 Write `tests/unit/test_hitl_queue.py` — test: enqueue returns queue_id, approve/decline update status, get_pending returns pending-only, SQLite row persists after mock restart, execute_approved processes approved rows, rate limit check_and_increment enforces daily cap (TDD — write before implementation, expect FAIL)
- [ ] T019 [P] Write `tests/unit/test_email_classifier.py` — test greeting detection for 5+ language patterns from greeting_patterns.yaml, OTP flag on message containing "OTP", spam keyword hit, Tier 0 confidence=1.0, Tier 1 receives only metadata not body (TDD)
- [ ] T020 [P] Write `tests/unit/test_dm_classifier.py` — test job_inquiry classification, networking detection, spam signal, sales pitch pattern, unknown intent fallback (TDD)
- [ ] T021 Validate Phase 2 — run `pytest tests/unit/test_hitl_queue.py tests/unit/test_email_classifier.py tests/unit/test_dm_classifier.py -v` and confirm all pass; config YAML files load without error

**Checkpoint**: Foundation complete — all 5 user story phases can now proceed.

---

## Phase 3: User Story 1 — WhatsApp Full Management (Priority: P1) 🎯 MVP

**Goal**: Full WhatsApp media send, group management, status posting, contact save — with HITL on all outbound.

**Independent Test**: "summarize my unread WhatsApp messages and draft a reply to [contact]" → HITL queued → approve → delivery confirmed. Also: broadcast to 11 recipients refused.

- [ ] T022 [US1] Extend Go WhatsApp bridge (`~/whatsapp-mcp/whatsapp-bridge/`) — add `POST /status` HTTP endpoint for WhatsApp Status posting (text + optional media); bridge is the authority for protocol; Python wrapper calls this endpoint (ADR-0022 §Missing Bridge Capabilities)
- [ ] T023 [P] [US1] Extend Go WhatsApp bridge — add `POST /group` endpoint for creating groups with `name`, `members[]`, `description`
- [ ] T024 [P] [US1] Extend Go WhatsApp bridge — add `GET /profile` endpoint for own WhatsApp profile retrieval (display name, status, profile photo URL)
- [ ] T025 [US1] Add `get_unread_summary()` to `mcp_servers/whatsapp/server.py` — calls bridge `mcp__whatsapp__list_chats` + `mcp__whatsapp__list_messages`; applies `dm_classifier.classify_dm_intent()` for priority ranking; masks PII in output; returns `UnreadSummary` (ADR-0022 Layer 2)
- [ ] T026 [P] [US1] Add `save_contact(name, phone, ceo_verified=True)` to `mcp_servers/whatsapp/server.py` — CEO-verified gate: writes `ContactRecord` to `vault/contacts.db` only when `ceo_verified=True`; raises `ContactNotVerifiedError` otherwise (FR-006; data-model.md §ContactRecord)
- [ ] T027 [US1] Add `broadcast(recipients, message)` to `mcp_servers/whatsapp/server.py` — validates `len(recipients) ≤ 10`; raises `WhatsAppBanRiskError` with count if exceeded; calls `check_and_increment("whatsapp", "bulk_broadcast", 10)` from rate limiter; enqueues HITL via `hitl_queue.enqueue()` before sending (FR-004, FR-040)
- [ ] T028 [P] [US1] Add `post_status(content, media_path=None, privacy="contacts")` to `mcp_servers/whatsapp/server.py` — wraps new bridge `/status` endpoint; HITL required before posting; `privacy` defaults to "contacts" (FR-005)
- [ ] T029 [P] [US1] Add `create_group(name, members, description=None)` to `mcp_servers/whatsapp/server.py` — wraps new bridge `/group` endpoint; HITL required; returns `GroupResult` with `group_id` (FR-009)
- [ ] T030 [US1] Add HITL integration wrapper to `mcp_servers/whatsapp/server.py` — all outbound send functions (`broadcast`, `post_status`, `create_group`, and bridge calls for `mcp__whatsapp__send_message`, `mcp__whatsapp__send_file`, `mcp__whatsapp__send_audio_message`) call `hitl_queue.enqueue()` and return immediately (non-blocking, ADR-0021 §Non-Blocking Behavior)
- [ ] T031 [P] [US1] Update `watchers/whatsapp_watcher.py` — integrate `get_unread_summary()` for incoming message routing; route new action types to HITL queue; log all actions to `vault/Logs/whatsapp_YYYY-MM-DD.md` with NO raw message content (FR-039, FR-042)
- [ ] T032 [US1] Write `tests/unit/test_whatsapp_mcp_media.py` — test: broadcast to 11 recipients raises `WhatsAppBanRiskError`, broadcast to 10 enqueues HITL and returns non-blocking, `save_contact` with `ceo_verified=False` raises error, `get_unread_summary` PII masking
- [ ] T033 [P] [US1] Write `tests/contract/test_whatsapp_contracts.py` — contract tests for all WhatsApp tools per `contracts/whatsapp-tools.md`: correct input/output types, error codes, HITL gate presence

**Checkpoint**: WhatsApp full management functional. Test independently before proceeding.

---

## Phase 4: User Story 2 — Gmail Full Management (Priority: P2)

**Goal**: Classify inbox, auto-reply to greetings, draft sensitive replies, trash spam, HITL-gated sends.

**Independent Test**: Trigger classify_inbox → labels applied → greeting auto-replied without HITL → sensitive email draft staged → HITL queued.

- [ ] T034 [US2] Add `create_draft(to, subject, body, reply_to_id=None)` to `mcp_servers/gmail/server.py` — calls Gmail Drafts.create API; returns `DraftResult` with `draft_id`; does NOT send (FR-013)
- [ ] T035 [P] [US2] Add `send_draft(draft_id)` to `mcp_servers/gmail/server.py` — validates action status = `approved` in hitl_queue before calling Gmail Drafts.send; raises `HITLNotApprovedError` if not approved (FR-013)
- [ ] T036 [P] [US2] Add `label_emails(message_ids, labels)` + `archive_emails(message_ids)` to `mcp_servers/gmail/server.py` — batch Gmail label apply and archive operations; returns `LabelResult` / `ArchiveResult`
- [ ] T037 [P] [US2] Add `trash_emails(message_ids)` + `search_emails(query, max_results=50)` to `mcp_servers/gmail/server.py` — `trash_emails` moves to Trash (NOT permanent delete, FR-015); `search_emails` wraps Gmail search API
- [ ] T038 [US2] Add `classify_inbox(max_emails=100)` to `mcp_servers/gmail/server.py` — calls `email_classifier.classify_email()` per message; writes `EmailClassification` rows to `vault/hitl_queue.db`; applies Gmail labels: `AI_Urgent`, `AI_Opportunity`, `AI_Promotional`, `AI_Spam`, `AI_OTC`, `AI_Routine`, `AI_SensitiveAttachment` (FR-011)
- [ ] T039 [P] [US2] Add `get_attachment_flags(message_id)` to `mcp_servers/gmail/server.py` — runs `classifiers/sensitive_patterns.yaml` patterns against attachment metadata and body snippet; returns `AttachmentFlags` (FR-014)
- [ ] T040 [P] [US2] Add `send_auto_reply(message_id, template_key)` to `mcp_servers/gmail/server.py` — loads template from `config/auto_reply_templates.yaml` by key; sends via Gmail API immediately (no HITL for auto-reply); logs to `vault/Logs/gmail_autoreply_YYYY-MM-DD.md` (FR-012)
- [ ] T041 [P] [US2] Add `get_daily_summary()` to `mcp_servers/gmail/server.py` — returns `InboxSummary` with: `total_received`, `action_required_count`, `opportunities_count`, `spam_removed_count`, `top_3_senders` (FR-017; data-model.md §InboxSummary)
- [ ] T042 [US2] Implement sensitive email HITL flow in `mcp_servers/gmail/server.py` — `classify_inbox()` detects `urgent` or `opportunity` category → calls `create_draft()` → calls `hitl_queue.enqueue(summary=..., action_type="gmail_draft_send", content_ref=draft_id)` → returns immediately; CEO approves → `execute_approved()` calls `send_draft(draft_id)` (FR-013, ADR-0021)
- [ ] T043 [US2] Create `watchers/gmail_reply_watcher.py` — polls every 60s: run `classify_inbox()` on new emails, send auto-reply for greeting candidates, call `execute_approved()` for any approved Gmail drafts, write `vault/Logs/gmail_triage_YYYY-MM-DD.md` (plan.md Phase B §Watcher)
- [ ] T044 [P] [US2] Write `tests/unit/test_gmail_mcp_write.py` — test: classify labels 85%+ sample set, `create_draft` does not send email, auto-reply sends without HITL, `trash_emails` uses Trash not Delete, attachment flag on OTP subject line
- [ ] T045 [P] [US2] Write `tests/contract/test_gmail_contracts.py` — contract tests for all 8 new Gmail tools per `contracts/gmail-tools.md`: input validation, output schema, error taxonomy

**Checkpoint**: Gmail full management functional. Test independently before proceeding.

---

## Phase 5: User Story 3 — LinkedIn Full Management (Priority: P3)

**Goal**: Profile write, analytics, connection management, post engagement, DMs gated on API key.

**Independent Test**: Post text update → appears on LinkedIn. `get_analytics()` returns impressions. `accept_connection()` rate limiter enforced at 20/day. `send_dm` without LINKEDIN_MESSAGING_API_KEY raises informative error.

- [ ] T046 [P] [US3] Add `update_profile_field(field, value)` to `mcp_servers/linkedin/server.py` — fields: `headline`, `summary`, `current_position`, `open_to_work`, `hiring_status`; HITL required; returns `ProfileResult` with updated URL (FR-022)
- [ ] T047 [P] [US3] Add `upload_resume(file_path)` to `mcp_servers/linkedin/server.py` — HITL required; uses LinkedIn v2 Document API; returns `ResumeResult`
- [ ] T048 [P] [US3] Add `react_post(post_id, reaction="like")` + `comment_post(post_id, text)` to `mcp_servers/linkedin/server.py` — `react_post` no HITL; `comment_post` HITL required (FR-019)
- [ ] T049 [P] [US3] Add `repost(post_id, commentary=None)` + `save_post(post_id)` to `mcp_servers/linkedin/server.py` — `repost` HITL required; `save_post` no HITL; log saved post URL to `vault/Logs/linkedin_saves.md` (FR-024)
- [ ] T050 [US3] Add `list_pending_connections(filter=None)` + `accept_connection(profile_id)` to `mcp_servers/linkedin/server.py` — `accept_connection` calls `check_and_increment("linkedin", "connection_accept", 20)` rate limiter; raises `LinkedInRateLimitError` if daily cap hit (FR-021, FR-040)
- [ ] T051 [P] [US3] Add `reject_connection(profile_id)`, `send_connection_request(profile_id, note=None)`, `unconnect(profile_id)`, `block_profile(profile_id)`, `follow_profile(profile_id)` to `mcp_servers/linkedin/server.py` — `send_connection_request` requires HITL approval (FR-021)
- [ ] T052 [P] [US3] Add `search_profiles(query, filters=None)` to `mcp_servers/linkedin/server.py` — uses LinkedIn People Search API; returns `SearchResults` with name, headline, profile_url, mutual_connections_count
- [ ] T053 [P] [US3] Add `get_analytics(period="7d")` to `mcp_servers/linkedin/server.py` — calls LinkedIn Analytics API v2; returns `AnalyticsReport` with `impressions`, `profile_views`, `post_reach`, `follower_growth`, `top_post` (FR-023)
- [ ] T054 [US3] Create `mcp_servers/linkedin/dm_server.py` — GATED by `LINKEDIN_MESSAGING_API_KEY`; implements `list_conversations() → ConversationList`, `send_dm(recipient_id, text) → DMResult` with `check_and_increment("linkedin", "dm_send", 5)` rate limiter, `classify_dm_intent(text) → DMClassification` using `dm_classifier`; all `send_dm` calls require HITL; raises `LinkedInDMUnavailable("Apply at https://developer.linkedin.com/partner-programs/messaging")` if env var not set (FR-020)
- [ ] T055 [US3] Update `mcp_servers/linkedin/server.py` — add conditional DM tools import at bottom: `if os.getenv("LINKEDIN_MESSAGING_API_KEY"): from .dm_server import register_dm_tools; register_dm_tools(mcp)` (ADR-0023 §Rule 2: Gated capabilities)
- [ ] T056 [US3] Create `watchers/linkedin_monitor.py` — polls LinkedIn feed every 15 min using `list_conversations()` (if key set) and feed search; writes `vault/Needs_Action/linkedin_YYYY-MM-DD-HH-MM.md` for: new DMs, new connections, posts matching `config/linkedin_interests.yaml` keywords (plan.md Phase G §New watcher)
- [ ] T057 [P] [US3] Write `tests/unit/test_linkedin_mcp_extended.py` — test: `get_analytics()` returns expected keys, `accept_connection` raises `LinkedInRateLimitError` after 20 calls, `send_dm` without env key raises `LinkedInDMUnavailable`, `update_profile_field` enqueues HITL and returns immediately

**Checkpoint**: LinkedIn full management functional. Test independently before proceeding.

---

## Phase 6: User Story 4 — Google Calendar Full Management (Priority: P4)

**Goal**: Create/update/delete events, conflict detection, focus blocks, email-to-event extraction.

**Independent Test**: Create meeting → appears in Google Calendar. Create overlapping event → ConflictDetected raised. Delete event → attendee cancellation notification sent.

- [ ] T058 [US4] Update `scripts/calendar_auth.py` — change `SCOPES` from `["https://www.googleapis.com/auth/calendar.readonly"]` to `["https://www.googleapis.com/auth/calendar"]`; delete `token_calendar.json` if it exists; re-run OAuth flow (WSL2 code-paste method); verify write access by creating and deleting a test event (research.md §3)
- [ ] T059 [US4] Add `check_conflicts(start, end)` to `mcp_servers/calendar/server.py` — queries Google Calendar freebusy API for time range; returns `ConflictCheck` with `has_conflict: bool` and `conflicting_events: list[EventSummary]`; MUST be called internally before every `create_event` (FR-029)
- [ ] T060 [P] [US4] Add `create_event(title, start, end, attendees=None, location=None, description=None, notify_attendees=True)` to `mcp_servers/calendar/server.py` — calls `check_conflicts(start, end)` first; raises `ConflictDetected(conflicting_events)` if overlap found; HITL required; sends attendee invites if `notify_attendees=True` (FR-026)
- [ ] T061 [P] [US4] Add `update_event(event_id, **updates)` to `mcp_servers/calendar/server.py` — HITL required; sends update notifications to attendees; supports updating title, time, location, attendees, description (FR-027)
- [ ] T062 [P] [US4] Add `delete_event(event_id, notify_attendees=True)` to `mcp_servers/calendar/server.py` — HITL required; sends cancellation notification if `notify_attendees=True`; returns `DeleteResult` (FR-027)
- [ ] T063 [P] [US4] Add `create_focus_block(start, end, title="Focus Time")` to `mcp_servers/calendar/server.py` — creates event with status `busy`, no attendees, no invites; NO HITL required (FR-030)
- [ ] T064 [US4] Add `extract_event_from_email(email_body_metadata)` to `mcp_servers/calendar/server.py` — sends ONLY email metadata (subject, sender_domain, date, length) to Tier 1 OpenRouter model (FR-043: never full body); returns `EventProposal` with title, proposed_start, proposed_end, suggested_attendees; CEO confirms via HITL before `create_event` is called (FR-031)
- [ ] T065 [P] [US4] Write `tests/unit/test_calendar_mcp_write.py` — test: `create_event` calls `check_conflicts` first, overlapping times raise `ConflictDetected`, `create_focus_block` creates without HITL, `delete_event` sends cancellation notification, `extract_event_from_email` sends only metadata to model
- [ ] T066 [P] [US4] Write `tests/contract/test_calendar_contracts.py` — contract tests for all 6 Calendar tools per `contracts/calendar-tools.md`

**Checkpoint**: Calendar full management functional. Test independently before proceeding.

---

## Phase 7: User Story 5 — Social Media Automation (Priority: P5)

**Goal**: Facebook/Instagram comment + DM management. Twitter reply, like, analytics. Spam auto-hide.

**Independent Test**: Post tweet → appears on Twitter. Query engagement → analytics returned. DM reply → HITL queued. `list_dms()` on Free Twitter tier raises `TwitterDMTierError`.

- [ ] T067 [P] [US5] Add `list_comments(post_id)` + `reply_comment(comment_id, text)` + `delete_comment(comment_id)` to `mcp_servers/facebook/server.py` — `reply_comment` HITL required; `delete_comment` HITL required (FR-033)
- [ ] T068 [P] [US5] Add `hide_comment(comment_id)` to `mcp_servers/facebook/server.py` — auto-hide when `dm_classifier` or Tier 0 spam patterns match; NO HITL for auto-hide; include in daily briefing (FR-035)
- [ ] T069 [P] [US5] Add `list_dms(platform="facebook")` + `reply_dm(conversation_id, message)` to `mcp_servers/facebook/server.py` — `reply_dm` HITL required (FR-034)
- [ ] T070 [P] [US5] Add `get_page_analytics(period="7d")` to `mcp_servers/facebook/server.py` — calls Meta Insights API; returns `PageAnalytics` with `reach`, `impressions`, `new_followers`, `post_engagement`, `top_post` (FR-036)
- [ ] T071 [P] [US5] Add `reply_tweet(tweet_id, text)` + `quote_tweet(tweet_id, comment)` to `mcp_servers/twitter/server.py` — both HITL required (FR-033)
- [ ] T072 [P] [US5] Add `like_tweet(tweet_id)` + `follow_user(user_id)` + `unfollow_user(user_id)` to `mcp_servers/twitter/server.py` — `like_tweet` no HITL; `follow_user` / `unfollow_user` no HITL (FR-037)
- [ ] T073 [US5] Add `list_dms()` + `reply_dm(dm_id, message)` (GATED) to `mcp_servers/twitter/server.py` — check `TWITTER_TIER` env var; raise `TwitterDMTierError("Upgrade to Twitter Basic at developer.twitter.com")` if Free tier; `reply_dm` HITL required (FR-034)
- [ ] T074 [P] [US5] Add `get_tweet_analytics(period="7d")` to `mcp_servers/twitter/server.py` — calls Twitter v2 organic metrics; returns `TweetAnalytics` with `impressions`, `likes`, `retweets`, `profile_visits`, `top_tweet` (FR-036)
- [ ] T075 [US5] Integrate Tier 0 spam classifier in Facebook + Twitter comment flows — `list_comments()` in `mcp_servers/facebook/server.py` and `mcp_servers/twitter/server.py` runs `dm_classifier.is_spam(text)` on each comment; auto-hide on match; include spam count in daily briefing (FR-035)
- [ ] T076 [P] [US5] Write `tests/unit/test_social_mcp_extended.py` — test: Facebook comment list/reply/auto-hide, Twitter reply requires HITL, `list_dms()` on free tier raises `TwitterDMTierError`, analytics return correct structure

**Checkpoint**: Social media automation functional. Test independently before proceeding.

---

## Phase 8: Orchestrator & Briefing Integration

**Purpose**: Wire HITL queue into CEO daily briefing. Cross-platform summary. Register watchers.

- [ ] T077 Update `orchestrator/ceo_briefing.py` — add `collect_pending_hitl_section() -> str`: calls `hitl_queue.get_pending()` and formats as `"PENDING APPROVALS (N):\n- [platform→target] summary_text\n..."` block for daily briefing (plan.md Phase G)
- [ ] T078 Update `orchestrator/ceo_briefing.py` — add `collect_cross_platform_summary() -> str`: uses `asyncio.gather()` to query all 5 platform analytics in parallel; total budget ≤30s (SC-010); collect results from `get_daily_summary()`, `get_analytics()`, `get_page_analytics()`, `get_tweet_analytics()`, `get_unread_summary()`
- [ ] T079 [P] Register `watchers/gmail_reply_watcher.py` in cron scheduler — every 60s polling; confirm vault/Logs/ write path and no-PII constraint
- [ ] T080 [P] Register `watchers/linkedin_monitor.py` in cron scheduler — every 15 min; writes to `vault/Needs_Action/linkedin_YYYY-MM-DD-HH-MM.md`
- [ ] T081 Add vault/Logs PII audit function in `orchestrator/hitl_queue.py` — `audit_logs_for_pii() -> AuditResult`: scans last 7 days of vault/Logs/ files for E.164 phone patterns, email address patterns, and message body content; returns findings for SC-009 compliance

**Checkpoint**: Briefing includes HITL pending section and cross-platform summary.

---

## Phase 9: Tests, Security & QA

**Purpose**: Integration tests, security scan, acceptance criteria verification.

- [ ] T082 Write `tests/integration/test_hitl_full_flow.py` — end-to-end: `hitl_queue.enqueue()` → HITL queued → mock CEO approve via `hitl_queue.approve()` → `execute_approved()` triggers action → confirm action status = `executed`; also test decline path → action stays in `declined` state, not executed
- [ ] T083 [P] Write `tests/integration/test_gmail_triage_flow.py` — end-to-end: mock email arrives → `classify_inbox()` → label applied in Gmail → sensitive email triggers `create_draft()` → `hitl_queue.enqueue()` → mock approval → `send_draft()` called
- [ ] T084 Run full test suite — `pytest tests/unit/ tests/contract/ tests/integration/ --cov=classifiers --cov=orchestrator --cov=mcp_servers -v` — confirm: classifiers ≥90%, `hitl_queue.py` ≥90%, new MCP server tools ≥80%, new watchers ≥80%
- [ ] T085 [P] Security scan — verify Tier 1 privacy constraint: grep `classifiers/email_classifier.py` confirms full body never passed to `openrouter_client`; verify no hardcoded credentials: `git grep -n "api_key\|token\|password\|secret"` with no matches outside `.env` references; verify vault SQLite permissions: `ls -la vault/*.db` shows `600`
- [ ] T086 [P] Rate limit validation — write `tests/unit/test_rate_limiters.py`: verify `WhatsAppBanRiskError` on broadcast to 11, `LinkedInRateLimitError` after 20 `accept_connection` calls, `LinkedInRateLimitError` after 5 `send_dm` calls; confirm counters reset after mocking midnight UTC
- [ ] T087 Run quickstart.md validation — follow `specs/011-full-comms-automation/quickstart.md` step-by-step: confirm all new env vars documented (`OPENROUTER_API_KEY`, `WHATSAPP_BRIDGE_URL_BUSINESS`, `LINKEDIN_MESSAGING_API_KEY`, `TWITTER_TIER`), OAuth flows documented for Calendar write and LinkedIn re-auth
- [ ] T088 [P] PII audit of vault/Logs/ — run `audit_logs_for_pii()` (T081) against test log output; confirm SC-009: zero raw phone numbers, email addresses, or full message content in any log file
- [ ] T089 Final acceptance criteria verification — confirm each SC-001 through SC-010 is measurable; document which are blocked by human tasks (e.g., SC-001 WhatsApp ≤60s requires bridge running; SC-003 85% Gmail accuracy requires live inbox); tag blocked items with `[HT]` in acceptance notes

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
  └─→ Phase 2 (Foundation) ← BLOCKS all user story phases
        ├─→ Phase 3 (US1 WhatsApp) ─┐
        ├─→ Phase 4 (US2 Gmail) ────┤
        ├─→ Phase 5 (US3 LinkedIn) ─┤ ← can run in parallel after Phase 2
        ├─→ Phase 6 (US4 Calendar) ─┤
        └─→ Phase 7 (US5 Social) ───┘
              └─→ Phase 8 (Orchestrator)
                    └─→ Phase 9 (QA)
```

### Human Tasks Required Before Implementation

| Phase | Human Task | Blocker |
|-------|-----------|---------|
| Phase 2 | Sign up at openrouter.ai; add `OPENROUTER_API_KEY` to `.env` | Tier 1 classifier calls fail without key |
| Phase 3 | WhatsApp Go bridge running on port 8080 (personal account) | All WhatsApp tools fail without bridge |
| Phase 5 | Apply for LinkedIn Messaging API at developer.linkedin.com | `dm_server.py` tools gate on this; DMs deferred to Phase 7 if rejected |
| Phase 6 | Re-run `scripts/calendar_auth.py` after T058 scope change + delete `token_calendar.json` | Calendar write scope required |
| Phase 7 | Twitter Basic tier upgrade (optional) | `list_dms`/`reply_dm` gated; Free tier raises error |

### Within Each User Story Phase

- Tests FIRST (TDD where listed) — write test, confirm FAIL, then implement
- Schema/config before implementation
- Implementation before HITL integration
- Unit tests before integration tests

### Parallel Opportunities

**Within Phase 2**: T009, T010, T011, T012, T013, T014, T015 all run in parallel (separate YAML/schema files)
**Within Phase 3**: T023, T024 parallel (separate Go endpoints); T025, T026, T028, T029 parallel (separate server.py methods)
**Within Phase 4**: T035, T036, T037, T039, T040, T041 parallel (separate Gmail tools, no file conflicts)
**Across Phases 3–7**: After Phase 2 completes, all 5 user story phases can run in parallel with separate developers

---

## Parallel Execution Example — Phase 2 Foundation

```bash
# Run these simultaneously (separate files, no conflicts):
Task: "Write config/model_routing.yaml — T011"
Task: "Write config/auto_reply_templates.yaml — T012"
Task: "Write classifiers/greeting_patterns.yaml — T014"
Task: "Write classifiers/sensitive_patterns.yaml — T015"
Task: "Write tests/unit/test_email_classifier.py — T019"
Task: "Write tests/unit/test_dm_classifier.py — T020"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T005)
2. Complete Phase 2: Foundation (T006–T021) — required for all stories
3. Complete Phase 3: US1 WhatsApp (T022–T033)
4. **STOP and VALIDATE**: WhatsApp send + HITL + broadcast cap all work
5. Demo: unread summary → HITL draft → approve → delivered

### Incremental Delivery Order

1. Setup + Foundation → Foundation ready (all 5 stories unblocked)
2. Phase 3 US1 WhatsApp → MVP! Core HITL channel + media send
3. Phase 4 US2 Gmail → High-volume inbox automation
4. Phase 5 US3 LinkedIn → Professional brand channel
5. Phase 6 US4 Calendar → Schedule management
6. Phase 7 US5 Social → Brand presence automation
7. Phase 8 Orchestrator → Briefing integration
8. Phase 9 QA → Production-ready sign-off

### Notes

- [P] tasks = different files, no unresolved dependencies — safe to parallelize
- [USN] label maps each task to the user story it serves
- Human tasks ([HT] items in Dependencies table) must be completed before the relevant phase
- Commit after each task or logical group — small, testable diffs
- Stop at phase checkpoints to validate independently before proceeding
- Vault files are gitignored; never commit `vault/*.db`, `token_*.json`, `.env`
