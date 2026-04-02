# Feature Specification: CEO Briefing + Odoo Integration

**Feature Branch**: `010-ceo-briefing-odoo-gold`
**Created**: 2026-03-11
**Status**: Approved
**Phase**: 6 — Gold Tier

---

## Clarifications

### Session 2026-03-11

- Q: Does "CEO Briefing" mean daily, weekly, or both? → A: Both — daily lightweight briefing (email/calendar/social) + weekly deep business + accounting audit (Odoo GL/AR/invoice full audit).
- Q: Which social platforms are required? → A: LinkedIn (Phase 5.5, done), Facebook, Instagram, Twitter/X — all four must post messages and generate activity summaries.
- Q: Should all AI functionality be packaged as Agent Skills? → A: Yes — every AI capability (briefing generation, social posting, Odoo audit, Ralph Wiggum loop) MUST be implemented as a reusable Agent Skill (per Gold Tier requirements document).
- Q: Is Odoo API protocol XML-RPC or JSON-RPC? → A: JSON-RPC (per Gold Tier requirements doc; Odoo 18 supports JSON-RPC on `/web/dataset/call_kw` endpoint).
- Q: Is architecture documentation required as a deliverable? → A: Yes — a `docs/architecture.md` (or equivalent) documenting design decisions and lessons learned is a Gold Tier exit criterion.
- Q: Do Facebook/Instagram/Twitter/X developer credentials already exist? → A: None exist yet. Human tasks HT-014 (Facebook Page + App), HT-015 (Instagram Business Account), HT-016 (Twitter/X developer app) required before live testing. No official MCP registry entries for these platforms — custom MCP servers will be built using the project's established FastMCP pattern (same as `linkedin_mcp`, `whatsapp_mcp`).
- Q: What Facebook/Instagram account type will be used for API access? → A: Facebook Page + Instagram Business Account linked to that Page (Option A). Provides full Graph API access for posting, analytics, and engagement metrics in briefing summaries. HT-014 = create Facebook Page + developer app; HT-015 = convert/create Instagram Business Account linked to that Page.
- Q: Should the system monitor incoming social media DMs and comments? → A: Yes (P3) — system should watch for job/client/collaboration keywords in incoming DMs and comments and escalate via WhatsApp HITL notification. Autonomous replies are out of scope; monitoring + alerting is in scope (FR-028 added).
- Q: How should the Ralph Wiggum loop be implemented? → A: New explicit `run_until_complete()` wrapper (Option B). Each workflow step (collect → draft → HITL → send → verify) retries up to N times on failure with self-diagnosis. Escalates to human only after exhausting retries. This is a new module, not the existing 15-min orchestrator polling loop (FR-029 added).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Daily CEO Briefing Delivered to Owner (Priority: P1)

Every morning the owner receives a concise, structured briefing covering
everything that happened in the last 24 hours: emails processed and decisions
made, upcoming 48-hour calendar events, social media activity across LinkedIn,
Facebook, Instagram, and Twitter/X, and a lightweight financial alert from
Odoo (overdue invoices only). The briefing lands in `vault/CEO_Briefings/` as
a markdown file and triggers a WhatsApp HITL approval before email delivery.

**Why this priority**: This is the core Gold tier deliverable. Daily cadence
ensures the owner is never more than 24 hours behind on all monitored domains.

**Independent Test**: Run the briefing generator on-demand (`--now`), verify
`vault/CEO_Briefings/YYYY-MM-DD.md` is created with all mandatory sections
and at least one non-empty data source.

**Acceptance Scenarios**:

1. **Given** the cron fires at 07:00, **When** the briefing generator runs,
   **Then** a markdown file is written to `vault/CEO_Briefings/YYYY-MM-DD.md`
   within 60 seconds containing all mandatory sections.

2. **Given** the briefing file is created, **When** the HITL approval step
   runs, **Then** a WhatsApp message ≤500 chars is sent to the owner with
   key metrics (email count, financial alerts, next calendar event, social posts).

3. **Given** the owner approves, **When** the approval is processed, **Then**
   the full briefing is emailed to the owner's Gmail address and the vault
   file is updated to `status: delivered`.

4. **Given** it is past 08:00 with no briefing for today, **When** the owner
   runs `--now`, **Then** the briefing is generated immediately.

---

### User Story 2 — Weekly Business + Accounting Audit (Priority: P1)

Every Monday morning the system generates a deep weekly audit: full Odoo GL
balance by account type, complete AR aging report (all buckets), invoice
summary (paid, outstanding, overdue), and a 7-day rolling summary of all
social media activity and email triage. This is the "CEO Weekly Briefing" —
more detailed than the daily snapshot and requires a separate HITL approval.

**Why this priority**: This is the primary Gold tier differentiator. The
weekly audit is what distinguishes an autonomous employee from a daily
dashboard. It satisfies the "Weekly Business and Accounting Audit" requirement.

**Independent Test**: Trigger weekly audit manually (`--weekly`), verify
`vault/CEO_Briefings/week-YYYY-WNN.md` is created with GL, AR, and
7-day social/email rollup.

**Acceptance Scenarios**:

1. **Given** it is Monday and the weekly cron fires, **When** the audit runs,
   **Then** `vault/CEO_Briefings/week-YYYY-WNN.md` is written within 120
   seconds with all audit sections populated.

2. **Given** the Odoo GL has 15 accounts, **When** the audit runs, **Then**
   the financial section groups them by type (income, expense, asset,
   liability) with totals per type.

3. **Given** there are 3 invoices 60+ days overdue, **When** the audit runs,
   **Then** those invoices appear in the "OVERDUE — Action Required" subsection
   with partner name, amount, and days outstanding.

4. **Given** Odoo is unavailable during weekly audit, **When** the audit
   completes, **Then** the financial section clearly states
   "Odoo unavailable — accounting data missing this week" and the rest of
   the audit (social, email, calendar) is delivered normally.

---

### User Story 3 — Facebook + Instagram: Post and Summarise (Priority: P2)

The owner can trigger the system to post a message to Facebook Page and
Instagram simultaneously (or either individually). The briefing's social
section includes a 7-day summary of posts published, engagement metrics
if available, and any posts pending HITL approval.

**Why this priority**: Explicit Gold Tier requirement. Extends the social
media capability already established with LinkedIn in Phase 5.5.

**Independent Test**: Call the Facebook/Instagram MCP `health_check` and
`post_update` tools directly; verify the briefing social section reflects
the posted content.

**Acceptance Scenarios**:

1. **Given** valid Facebook + Instagram credentials, **When** `post_update`
   is called with text ≤500 chars, **Then** the post appears on both
   platforms within 60 seconds and a `vault/Logs/social_posts.jsonl` entry
   is written.

2. **Given** a social post is drafted, **When** the HITL approval step runs,
   **Then** a WhatsApp notification is sent with the post preview before
   publishing (no post without approval).

3. **Given** Facebook API is unavailable, **When** `post_update` is called,
   **Then** the Instagram post still proceeds independently and the Facebook
   failure is logged without crashing the workflow.

---

### User Story 4 — Twitter/X: Post and Summarise (Priority: P2)

The owner can trigger the system to post a message to Twitter/X. The briefing
social section includes Twitter/X posts from the last 7 days and any pending
draft tweets awaiting approval.

**Why this priority**: Explicit Gold Tier requirement alongside
Facebook/Instagram. Same HITL pattern as all other social platforms.

**Independent Test**: Call Twitter/X MCP `health_check` and `post_tweet`
tools directly; verify tweet appears in account and is logged.

**Acceptance Scenarios**:

1. **Given** valid Twitter/X credentials, **When** `post_tweet` is called
   with text ≤280 chars, **Then** the tweet is published and logged to
   `vault/Logs/social_posts.jsonl`.

2. **Given** a tweet draft is created, **When** the HITL approval step
   runs, **Then** the WhatsApp notification includes the tweet text before
   publishing.

3. **Given** Twitter/X API rate limit is hit, **When** `post_tweet` is
   called, **Then** the system returns a structured rate-limit error and
   queues the tweet for the next available window.

---

### User Story 5 — Odoo Financial Snapshot in Daily Briefing (Priority: P2)

The daily briefing's financial section shows overdue invoices only (the
lightweight alert). Full GL/AR detail is reserved for the weekly audit.

**Why this priority**: Keeps daily briefing concise. Overdue invoices are the
only financial items requiring daily attention.

**Independent Test**: Call Odoo MCP `get_ar_aging` directly, filter for
overdue bucket, verify the daily briefing matches.

**Acceptance Scenarios**:

1. **Given** 2 invoices are 31+ days overdue, **When** the daily briefing
   generates, **Then** the financial section shows "2 overdue invoices —
   see weekly audit for full details".

2. **Given** no overdue invoices exist, **When** the daily briefing generates,
   **Then** the financial section shows "No overdue invoices — all clear".

3. **Given** Odoo is unavailable, **When** the daily briefing generates,
   **Then** the financial section states "Odoo unavailable" and the briefing
   is still delivered.

---

### User Story 6 — Email Triage Summary in Briefing (Priority: P2)

The briefing summarises orchestrator email decisions from the past 24 hours
(daily) or 7 days (weekly): counts by priority tier, pending HITL approvals,
and any items flagged urgent.

**Acceptance Scenarios**:

1. **Given** 12 emails were processed yesterday, **When** the daily briefing
   generates, **Then** the email section reports "12 processed: 3 HIGH,
   7 MED, 2 LOW. 2 items pending approval."

2. **Given** no emails were processed, **When** the briefing generates,
   **Then** the email section states "No emails processed in the last 24h".

---

### User Story 7 — Calendar Highlights in Briefing (Priority: P3)

The briefing includes the owner's upcoming events for the next 48 hours
(daily) or full week (weekly), from the Calendar MCP live since Phase 5.

**Acceptance Scenarios**:

1. **Given** 3 events in the next 48 hours, **When** the daily briefing
   generates, **Then** all 3 are listed chronologically with title and time.

2. **Given** Calendar MCP is unavailable, **When** the briefing generates,
   **Then** the calendar section states "Calendar unavailable" and the rest
   is unaffected.

---

### User Story 8 — Agent Skills for All AI Capabilities (Priority: P2)

Every AI-powered capability built in Phase 6 is packaged as a reusable Claude
Code Agent Skill. This includes: briefing generation, social media post
drafting, weekly audit analysis, and Odoo financial interpretation. A skill
can be invoked by name in any future Claude Code session without re-explaining
the workflow.

**Why this priority**: Explicit Gold Tier requirement — "All AI functionality
should be implemented as Agent Skills."

**Independent Test**: Each skill file exists under `.claude/skills/` or the
project skills directory, can be loaded with the `Skill` tool, and produces
the expected output when invoked with a test prompt.

**Acceptance Scenarios**:

1. **Given** the `ceo-briefing` skill exists, **When** invoked, **Then** it
   generates a complete briefing without manual prompting.

2. **Given** the `social-post` skill exists, **When** invoked with platform
   and text, **Then** it drafts, routes through HITL, and publishes on the
   specified platform.

---

### Edge Cases

- All external sources (Odoo, Calendar, Facebook/Instagram, Twitter/X, email
  logs) simultaneously unavailable: briefing still generates with
  "unavailable" placeholders; WhatsApp HITL notification is still sent.
- Briefing for today/this-week already exists: on-demand generation
  overwrites it (idempotent).
- Owner never approves: after 24 hours (daily) or 72 hours (weekly audit)
  vault file marked `status: expired`.
- Odoo contains demo data only: financial section notes
  "Demo data detected — verify with real accounts before acting."
- Twitter/X rate limit hit: tweet queued for next window;
  briefing notes "1 tweet queued (rate limited)".
- Facebook/Instagram token expired: structured error returned;
  HITL notification includes "Social credentials need refresh" alert.
- Social post text exceeds platform limit (Twitter: 280 chars, Facebook: 63K
  chars, Instagram: 2200 chars): system truncates to limit and logs a warning.

---

## Requirements *(mandatory)*

### Functional Requirements

**CEO Briefing Generator**

- **FR-001**: System MUST generate a daily briefing written to
  `vault/CEO_Briefings/YYYY-MM-DD.md` with YAML frontmatter:
  `type: ceo_briefing`, `generated_at`, `period: daily`,
  `status: pending_approval`.

- **FR-002**: System MUST generate a weekly audit written to
  `vault/CEO_Briefings/week-YYYY-WNN.md` with `period: weekly` and full
  GL/AR data, 7-day social/email rollup.

- **FR-003**: System MUST collect briefing data from all available sources
  (Odoo MCP, Calendar MCP, Facebook/Instagram MCP, Twitter MCP, orchestrator
  logs, HITL logs, LinkedIn logs) and degrade gracefully when any source is
  unavailable.

- **FR-004**: System MUST send a WhatsApp HITL notification (≤500 chars)
  immediately after each briefing file is written before email delivery
  (Constitution Principle III — no external send without approval).

- **FR-005**: On approval, system MUST email the full briefing to the owner's
  Gmail address and update the vault file to `status: delivered`.

- **FR-006**: System MUST support on-demand generation:
  `--now` (daily), `--weekly` (audit).

- **FR-007**: System MUST log each briefing event to
  `vault/Logs/ceo_briefing.jsonl` (timestamp, period, status, sections
  collected, errors, whatsapp_sent, email_sent).

- **FR-008**: System MUST be idempotent: re-running on the same
  day/week overwrites the existing file rather than duplicating.

**Odoo MCP Server**

- **FR-009**: System MUST provide an Odoo MCP server with tools:
  `get_gl_summary`, `get_ar_aging`, `get_invoices_due`, `health_check`.

- **FR-010**: `get_gl_summary` MUST return GL balances grouped by account
  type (income, expense, asset, liability) via Odoo JSON-RPC API.

- **FR-011**: `get_ar_aging` MUST return AR bucketed by: current (0–30 days),
  overdue (31–60), seriously overdue (61–90), bad debt risk (90+).

- **FR-012**: `get_invoices_due` MUST return invoices due within 7 days with
  partner name, amount, due date, and days remaining.

- **FR-013**: `health_check` MUST verify Odoo reachability and return
  `healthy`, Odoo version, and database name.

- **FR-014**: All Odoo MCP calls MUST use Odoo JSON-RPC API
  (`/web/dataset/call_kw` endpoint) and authenticate from `.env` only.

- **FR-015**: If Odoo is down, all tools MUST return a structured error
  dict (never raise unhandled exceptions).

**Social Media MCP Servers**

- **FR-016**: System MUST provide a Facebook/Instagram MCP server built on
  the Meta Graph API using a Facebook Page Access Token (Facebook Page +
  Instagram Business Account linked to it). Tools: `post_update` (posts to
  both), `post_facebook_only`, `post_instagram_only`,
  `get_recent_posts` (last N posts), `health_check`.

- **FR-017**: `post_update` MUST route through HITL approval before publishing
  (Constitution Principle III).

- **FR-018**: System MUST provide a Twitter/X MCP server with tools:
  `post_tweet`, `get_recent_tweets`, `health_check`.

- **FR-019**: `post_tweet` MUST route through HITL approval before publishing.

- **FR-020**: All social media posts MUST be logged to
  `vault/Logs/social_posts.jsonl` with platform, text, post_id, timestamp,
  status (drafted | approved | published | rejected | failed).

- **FR-021**: System MUST enforce platform character limits before calling
  the API: Twitter 280, Instagram 2200, Facebook 63206.

- **FR-028**: System SHOULD monitor incoming social media DMs and comments
  for job/client/collaboration keywords. When a match is detected, a WhatsApp
  HITL notification MUST be sent to the owner with sender, platform, snippet,
  and suggested reply options (P3). No automated reply is sent without owner
  approval.

**Agent Skills**

- **FR-022**: Each AI capability MUST be packaged as a reusable Agent Skill
  file loadable via the `Skill` tool: `ceo-briefing`, `ceo-weekly-audit`,
  `social-post`, `odoo-financial-summary`.

- **FR-023**: Each skill MUST include a persona, workflow steps, and
  invocation examples in its skill file.

**Audit Logging & Documentation**

- **FR-024**: System MUST maintain a comprehensive audit log at
  `vault/Logs/audit.jsonl` recording every autonomous action: what action,
  which agent, outcome, timestamp (Constitution: comprehensive audit logging).

- **FR-025**: Phase 6 MUST produce an architecture documentation file at
  `docs/architecture.md` covering: system design, MCP server registry,
  data flow diagram (text/ASCII), ADR index, and lessons learned.

**Ralph Wiggum Loop**

- **FR-029**: System MUST implement a `run_until_complete(workflow, steps,
  max_retries=3)` utility that sequences workflow steps, catches per-step
  failures, logs each attempt to `vault/Logs/audit.jsonl`, retries up to
  `max_retries` times with exponential backoff, and escalates via WhatsApp
  HITL after exhausting retries. Used by: daily briefing, weekly audit,
  social post workflows.

- **FR-030**: Each step in a `run_until_complete` workflow MUST be an atomic
  unit (e.g., `collect_odoo_data`, `draft_briefing`, `send_hitl_notification`)
  so that retry re-enters at the failed step, not from the beginning.

**Cron & Scheduling**

- **FR-026**: System MUST add cron entries for: daily briefing at 07:00
  and weekly audit on Mondays at 07:00, managed by `H0_CRON_MANAGED`
  idempotency (result: 4 total managed entries after Phase 6).

- **FR-027**: System MUST NOT run briefing generator concurrently with
  the orchestrator process lock.

### Key Entities

- **CEO Briefing (daily)**: `vault/CEO_Briefings/YYYY-MM-DD.md`. Fields:
  `generated_at`, `period: daily`, `status`, `sections_collected`.

- **CEO Weekly Audit**: `vault/CEO_Briefings/week-YYYY-WNN.md`. Fields:
  `generated_at`, `period: weekly`, `status`, `sections_collected`,
  `odoo_gl_snapshot`, `ar_aging_buckets`.

- **Social Post**: Cross-platform post record. Fields: `platform`,
  `text`, `post_id`, `published_at`, `status`, `hitl_draft_id`.

- **GL Snapshot**: Point-in-time GL balances grouped by account type.

- **AR Aging Record**: Outstanding receivables by age bucket.

- **Audit Log Entry**: `vault/Logs/audit.jsonl` line. Fields:
  `ts`, `action`, `agent`, `platform`, `outcome`, `detail`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Daily briefing written to vault within 60 seconds of 07:00 cron.

- **SC-002**: Weekly audit written to vault within 120 seconds of Monday
  07:00 cron.

- **SC-003**: WhatsApp HITL notification delivered within 90 seconds of
  briefing/audit file creation.

- **SC-004**: Odoo financial data included in weekly audit on ≥95% of attempts
  when Odoo container is running.

- **SC-005**: Briefing/audit generation completes (all non-Odoo sections
  populated) on 100% of attempts even when Odoo is unavailable.

- **SC-006**: Facebook, Instagram, and Twitter/X posts published within 60
  seconds of owner approval.

- **SC-007**: All 7 briefing sections present in every generated briefing;
  unavailable sections show human-readable "unavailable" note.

- **SC-008**: Zero HITL violations — no external post or email sent without
  explicit owner approval.

- **SC-009**: Test coverage ≥80% on all new modules (SC-008 gate).

- **SC-010**: Cron idempotency — `setup_cron.sh` after Phase 6 produces
  exactly 4 `H0_CRON_MANAGED` entries.

- **SC-011**: Every autonomous action recorded in `vault/Logs/audit.jsonl`
  — zero unlogged actions.

- **SC-012**: `docs/architecture.md` exists, covers all MCP servers, data
  flow, and ADR index.

---

## Assumptions

- Odoo 18 is running on `localhost:8069` (HT-007 DONE). JSON-RPC endpoint
  `/web/dataset/call_kw` is available on Odoo 18 (supported since Odoo 16).
  Demo data acceptable for initial testing.
- `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD` in `.env`.
- postgres MCP connected to Neon (confirmed 2026-03-11).
- WhatsApp Go bridge running on `:8080` (HT-004 DONE).
- Facebook/Instagram developer app and Twitter/X API credentials require
  human setup (HT-014: Facebook Page + App, HT-015: Instagram Business Account,
  HT-016: Twitter/X developer app) before live posting can be tested.
- No official MCP server exists in the public registry for Facebook, Instagram,
  or Twitter/X. Custom MCP servers will be built using the project's FastMCP
  pattern (same as `linkedin_mcp`, `whatsapp_mcp`, `calendar_mcp`).
- Anthropic credits required for LLM-assisted briefing drafting and social
  post generation; structural/non-LLM sections work without credits.
- `vault/CEO_Briefings/` already exists (HT-001 DONE).
- The briefing generator reuses `GoBridge`, `HITLManager`, Gmail MCP,
  Calendar MCP from Phases 4–5.5.
- Agent Skills directory: `.claude/skills/` (global) or
  `ai-control/skills/` (project-local) — to be confirmed in planning.
- All social platforms require HITL approval before posting (no autonomous
  publishing, per Constitution Principle III).

---

## Out of Scope

- Multi-user or team briefings (single owner only).
- Odoo write operations (read-only in Phase 6).
- Odoo upgrade to version 19+ (Odoo 18 JSON-RPC is functionally equivalent).
- Historical trend charts or graphs (text/markdown only).
- Slack, Telegram, or Discord notifications.
- Oracle Cloud VM deployment (Phase 7 Platinum).
- LinkedIn changes (complete, managed by Phase 5.5 codebase).
- Autonomous replies to social media DMs or comments (monitoring + HITL
  escalation for job/client keywords is in scope via FR-028; automated
  replies without owner approval are out of scope).
- Paid social media APIs or boosted posts.
