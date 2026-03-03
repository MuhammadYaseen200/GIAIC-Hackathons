# Feature Specification: HITL + WhatsApp Silver Tier

**Feature Branch**: `008-hitl-whatsapp-silver`
**Created**: 2026-03-02
**Version**: 2.0.0 *(enriched with full governance, RI, agent team, SWARM plan)*
**Status**: Draft
**Phase**: 5 — Silver Tier
**Input**: Phase 5: HITL + WhatsApp Silver tier — WhatsApp watcher, HITL approval workflow, Google Calendar MCP integration

---

## Clarifications

### Session 2026-03-02

- Q: Which WhatsApp backend should be implemented and tested FIRST in Phase 5? → A: Go bridge at `:8080` (primary); pywa Cloud API as secondary fallback if bridge has issues.
- Q: What is the default calendar look-ahead window when the orchestrator queries events for scheduling context? → A: 7 days (covers this week + next week, the most common scheduling scenarios).
- Q: When a WhatsApp message lands in vault/Needs_Action/, does the orchestrator auto-draft a WhatsApp reply in Phase 5? → A: Capture only — WhatsApp messages are ingested to vault but orchestrator does NOT auto-draft WhatsApp replies in Phase 5. US4 (WhatsApp triage) is a bonus if time permits after P1/P2 are complete.
- Q: Should there be a cap on concurrent pending drafts to avoid WhatsApp notification flood? → A: Yes — cap at 5 simultaneous drafts. BUT instead of individual notifications, use a batch summary message: one WhatsApp message listing all pending drafts with sender name/email, subject, and priority/urgency tag (HIGH/MEDIUM/LOW). User approves or rejects each by draft ID from the single list.
- Q: What drives the HIGH/MED/LOW priority classification in the batch notification? → A: Tiered classifier — Layer 1 (rule-based spam/promo filter, zero tokens, skip drafting); Layer 2 (keyword heuristic: urgent/ASAP/deadline→HIGH, meeting/schedule/availability→MED, zero tokens); Layer 3 (LLM classification ONLY for ambiguous emails that pass layers 1+2, ~20-30% of emails). Maximizes accuracy on important emails while minimizing token spend.
- Owner privacy requirement (non-negotiable): The system MUST NEVER store, process, or forward sensitive media (images, video, audio) or sensitive text (passwords, OTPs, PINs, private data) — even accidentally. A mandatory Privacy Gate (FR-031–FR-039) runs before every vault write and LLM call. Media content is unconditionally blocked. Sensitive text is redacted before any storage or AI processing. Owner receives a privacy alert when redaction occurs. This is a hard constraint with zero exceptions.
- Privacy Gate scope extended to Gmail watcher (Phase 5 scope, Option A): `PrivacyGate` is built as a shared standalone utility (`watchers/privacy_gate.py`) — pure function, zero side effects. Applied to both WhatsApp watcher (new) and Gmail watcher (one-line retrofit). Existing Phase 2/3/4 tests are unaffected because test fixture emails contain no sensitive patterns. If any fixture accidentally triggers redaction, the fix is updating the fixture to assert `[REDACTED]` — which is correct behavior. Zero risk to working setup.

---

## Governance Alignment

> This specification was generated with full governance applied per `ai-control/AGENTS.md`, `ai-control/LOOP.md`, `ai-control/SWARM.md`, `ai-control/MCP.md`, `ai-control/SKILLS.md`, and `ai-control/HUMAN-TASKS.md`.

| Control Layer         | File                          | Status Applied |
|-----------------------|-------------------------------|----------------|
| Agent Registry        | `ai-control/AGENTS.md`        | ✅ Agent team instantiated (see below) |
| Enforcement Loops     | `ai-control/LOOP.md`          | ✅ Loop 3 (HITL) is the core of this spec |
| Swarm Coordination    | `ai-control/SWARM.md`         | ✅ Fan-Out SWARM plan defined below |
| MCP Registry          | `ai-control/MCP.md`           | ✅ WhatsApp MCP + Calendar MCP registered |
| Skills Registry       | `ai-control/SKILLS.md`        | ✅ Required skills identified below |
| Human Tasks           | `ai-control/HUMAN-TASKS.md`   | ✅ HT-004 DONE; HT-011/HT-012 pending |
| Constitution          | `.specify/memory/constitution.md` | ✅ All 10 principles checked below |

### MCPs Applied During Specification Generation

| MCP / Tool        | Purpose During Spec |
|-------------------|---------------------|
| `context7`        | pywa API surface; Google Calendar API `events().list()` signature |
| `code-search`     | BaseWatcher pattern; vault/Pending_Approval usage; atomic_write |
| `mcp__git`        | Branch history; existing ADR enumeration |
| `mcp__filesystem` | Directory tree audit; RI file discovery |

---

## Agent Team Instance

> Instantiated per `ai-control/AGENTS.md`. All agents MUST be invoked via `Task tool` during planning and implementation phases.

| Agent                    | Role                  | Model     | Auth Level | Responsibilities |
|--------------------------|-----------------------|-----------|------------|-----------------|
| `@loop-controller`       | Process Sheriff       | Opus      | HIGH       | Gate Phase 5 entry; verify Phase 4 artifacts complete before any code is written |
| `@imperator`             | Strategic Commander   | Opus      | SUPREME    | Phase 5 transition approval; master-plan.md update; scope decisions |
| `@spec-architect`        | Spec Owner            | Opus      | MEDIUM     | This document; clarification resolution; ADR suggestions |
| `@modular-ai-architect`  | HITL Workflow Designer| Opus      | MEDIUM     | Design HITL state machine (pending→approved→rejected→timed_out); concurrent draft handling |
| `@backend-builder`       | Primary Implementer   | Opus      | MEDIUM     | WhatsApp watcher, HITL manager, Calendar MCP, vault integration, orchestrator wiring |
| `@path-warden`           | Directory Guardian    | Sonnet    | MEDIUM     | Validate every new file placement after each write operation |
| `@qa-overseer`           | Quality Gate          | Opus      | HIGH       | Validate SC-001–SC-008 before marking phase complete; block merge if any SC fails |

### SWARM Fan-Out Execution Plan

```
[Phase 5 Start]
  1. Task(@loop-controller)       → verify Phase 4 complete (spec/plan/tasks all [X])
  2. Task(@imperator)             → approve scope; assign work packages; update master-plan.md

  [Parallel Block A — Design]
  3a. Task(@modular-ai-architect) → design HITL state machine + draft ID schema
  3b. Task(Explore, background)   → audit existing MCP server patterns for scaffolding reuse

  [Sequential — after 3a resolves]
  4.  Task(@spec-architect)       → confirm acceptance criteria match design

  [Parallel Block B — Build]
  5a. Task(@backend-builder)      → T1-T3: WhatsApp watcher (pywa + Go bridge)
  5b. Task(@backend-builder)      → T10-T12: Calendar MCP server
  5c. Skill(fetching-library-docs, "pywa") → pywa webhook + async handler docs

  [Sequential — after 5a]
  6a. Task(@backend-builder)      → T4-T9: HITL manager + approve/reject listener
  6b. Task(@path-warden)          → validate watcher + MCP file placements

  [Sequential — after 6a]
  7.  Task(@backend-builder)      → T13-T16: Orchestrator wiring + timeout handler
  8.  Task(@path-warden)          → validate orchestrator changes

  [Sequential — after all build]
  9.  Task(@qa-overseer)          → validate SC-001–SC-008 integration tests
  10. Skill(security-scan)        → audit for hardcoded secrets, path traversal
  11. Skill(deployment-preflight-check) → confirm Phase 5 deploy-ready

[Phase 5 End: write PHR + update overview.md]
```

---

## Phase Entry & Exit Criteria

### Entry Criteria (Phase 5 may begin ONLY when ALL are met)

| # | Criterion | Evidence Required |
|---|-----------|-------------------|
| E1 | Phase 4 complete | `specs/007-mcp-integration/spec.md` status = Complete |
| E2 | Gmail MCP operational | `mcp_servers/gmail/server.py` + health_check passes |
| E3 | Obsidian MCP operational | `mcp_servers/obsidian/server.py` + health_check passes |
| E4 | HT-004 DONE | WhatsApp paired as `XXXXXXXXXXXX:4@s.whatsapp.net`; Go bridge at `:8080` ✅ |
| E5 | HT-005 DONE | `gmail_mcp` + `obsidian_mcp` in `~/.claude.json` ✅ |
| E6 | loop-controller cleared | Phase gate verified by `@loop-controller` invocation |

### Exit Criteria (Phase 5 complete ONLY when ALL are met)

| # | Criterion | Measured By |
|---|-----------|-------------|
| X1 | WhatsApp watcher ingests to vault within 30s | SC-001 integration test |
| X2 | HITL notification sent within 30s of draft write | SC-002 integration test |
| X3 | Approved email sent within 60s of owner reply | SC-003 integration test |
| X4 | Zero emails sent without explicit "approve" | SC-005 invariant test |
| X5 | Calendar context in 95%+ scheduling drafts | SC-006 sampling test |
| X6 | All vault writes atomic | SC-007 filesystem probe |
| X7 | System recovers from connectivity drop | SC-008 chaos test |
| X8 | All spec FRs (FR-001–FR-024) covered by tasks | `@qa-overseer` sign-off |
| X9 | `ai-control/HUMAN-TASKS.md` updated with HT-011/HT-012 | File exists |
| X10 | PHR written and path-warden validated | `history/prompts/hitl-whatsapp-silver/` |

---

## Reusable Intelligence Applied

> Every decision below reuses proven patterns from earlier phases per Constitution Principle I (Spec-First) and Principle VII (Phase-Gated Delivery).

| Pattern / ADR               | Source                                | Applied To |
|-----------------------------|---------------------------------------|------------|
| `BaseWatcher` ABC           | `watchers/base_watcher.py` + ADR-0001 | WhatsApp watcher MUST inherit BaseWatcher |
| FastMCP + Pydantic v2 + stdio| ADR-0005                             | WhatsApp MCP + Calendar MCP server stack |
| MCPClient fallback protocol | ADR-0007                              | Orchestrator calls WhatsApp/Calendar via MCPClient |
| ADR-0008 error taxonomy     | `history/adr/0008-*`                  | `auth_required`, `not_found`, `rate_limited`, `mcp_unavailable`, `send_failed` |
| ADR-0009 MCPClient wiring   | `history/adr/0009-*`                  | Dual MCPClient pattern in orchestrator |
| `atomic_write`              | `watchers/utils.py`                   | All vault writes (Pending_Approval, Needs_Action) |
| Loop 3 HITL format          | `ai-control/LOOP.md`                  | Pending_Approval YAML frontmatter schema |
| Gmail OAuth2 pattern        | `mcp_servers/gmail/`                  | Calendar MCP OAuth2 follows same token refresh flow |
| Phase 007 FR structure      | `specs/007-mcp-integration/spec.md`   | FR table format + SC format |
| Phase 007 data model        | `specs/007-mcp-integration/data-model.md` | Pydantic v2 input/output model patterns |
| `_retry_with_backoff()`     | `watchers/base_watcher.py:L89`        | WhatsApp send retries + Calendar API retries |

---

## Constitution Compliance Check

| Principle | Requirement | Phase 5 Compliance |
|-----------|-------------|-------------------|
| I — Spec-First | No code without approved spec | ✅ This spec gates all implementation |
| II — Local-First | All data processed locally; no cloud dependency for core logic | ✅ vault/ is local; MCPs run locally |
| III — HITL | No irreversible action without human approval | ✅ Email send blocked until owner WhatsApp "approve" |
| IV — MCP-First | Tool calls via MCPClient; direct API calls forbidden | ✅ Gmail, WhatsApp, Calendar all via MCP |
| V — Vault-Centric | Vault is source of truth; all state in vault/ | ✅ Pending_Approval/, Approved/, Rejected/ are state |
| VI — Watcher Architecture | All watchers inherit BaseWatcher ABC | ✅ WhatsApp watcher extends BaseWatcher |
| VII — Phase-Gated | Phase 5 may not begin until Phase 4 complete | ✅ Entry criteria E1-E5 enforced |
| VIII — Error Taxonomy | Use ADR-0008 error codes; no silent failures | ✅ FRs reference error codes explicitly |
| IX — Security & Audit | No secrets in code; all HITL decisions logged | ✅ OWNER_WHATSAPP_NUMBER in .env; vault/Logs/ audit trail |
| X — Graceful Degradation | System continues when MCPs unavailable | ✅ FR-015 (Calendar fallback); FR-020 (WhatsApp retry) |

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — WhatsApp Message Ingestion (Priority: P1)

As the owner of the Personal AI Employee, when someone sends me a WhatsApp message, the system automatically captures and archives it to my Obsidian vault so I never miss an important message and have a searchable record of all conversations.

**Why this priority**: Core foundation of the WhatsApp integration. Without message ingestion, the HITL workflow cannot function. It is the entry point for all downstream processing.

**Independent Test**: Send a WhatsApp message to the monitored number; verify a corresponding Markdown file appears in `vault/Needs_Action/` within 30 seconds.

**Acceptance Scenarios**:

1. **Given** the WhatsApp watcher is running, **When** an incoming WhatsApp text message arrives, **Then** the system creates a Markdown file in `vault/Needs_Action/` with sender info, timestamp (ISO 8601), message content, and WhatsApp message ID within 30 seconds.
2. **Given** the WhatsApp watcher is running, **When** a media message (image/audio) arrives, **Then** the system creates a Markdown file noting the media type and metadata (caption if present), even if the media body is not stored locally.
3. **Given** a duplicate message is received (same message ID), **When** the watcher processes it, **Then** no duplicate vault file is created (idempotent — `atomic_write` with message ID check).
4. **Given** the watcher loses connectivity, **When** it reconnects, **Then** it re-processes any missed messages via `_retry_with_backoff()` without creating duplicates.
5. **Given** a message arrives from an unknown/spam sender, **When** ingested, **Then** the vault file is created with `source: unknown` label; no filtering or blocking.

---

### User Story 2 — HITL Draft Review via WhatsApp (Priority: P1)

As the owner, when the orchestrator has drafted an email reply, I receive a WhatsApp notification asking me to approve or reject before anything is sent, so I maintain full control over all outbound communications.

**Why this priority**: Core HITL safety guarantee per Constitution Principle III. Without this, the system could send emails without human review — the primary business constraint of the Silver tier.

**Independent Test**: Trigger a draft email scenario; verify (a) file appears in `vault/Pending_Approval/`, (b) WhatsApp message arrives on owner's phone with draft summary and approve/reject prompt within 30s.

**Acceptance Scenarios**:

1. **Given** the orchestrator has produced a draft email reply, **When** the draft is ready, **Then** the draft is written to `vault/Pending_Approval/<ISO-timestamp>-<draft-id>.md` AND a WhatsApp message is sent to `OWNER_WHATSAPP_NUMBER` with: subject, recipient, body preview (≤500 chars), draft ID, and "Reply 'approve <draft-id>' or 'reject <draft-id>'" instructions.
2. **Given** a draft is in `vault/Pending_Approval/`, **When** the owner sends "approve <draft-id>" (case-insensitive), **Then** the system marks the draft approved, sends the email via Gmail MCP, and moves the file to `vault/Approved/`.
3. **Given** a draft is in `vault/Pending_Approval/`, **When** the owner sends "reject <draft-id>" (case-insensitive), **Then** the system does NOT send the email, archives to `vault/Rejected/`, and sends a WhatsApp confirmation.
4. **Given** a draft has been pending for 24 hours with no response, **When** timeout is reached, **Then** the system sends a WhatsApp reminder and marks status as `awaiting_reminder`; does NOT send the email.
5. **Given** multiple drafts are pending, **When** the owner approves one by draft ID, **Then** only that draft is sent; other pending drafts are unaffected.
6. **Given** the owner sends an ambiguous reply (e.g., "ok"), **When** parsed, **Then** the system replies: "Please reply with 'approve <draft-id>' or 'reject <draft-id>'" — no irreversible action taken.

---

### User Story 3 — Google Calendar Context in Draft Replies (Priority: P2)

As the owner, when the orchestrator drafts a reply to a meeting-related email, it automatically consults my Google Calendar for scheduling context, so replies about availability or meeting times are accurate.

**Why this priority**: Enhances reply quality but is not blocking for the core HITL workflow. Can be added after US1 and US2 are functional.

**Independent Test**: Send an email asking about availability for a specific date; verify the draft reply references actual calendar events (or gracefully notes unavailability) for that date.

**Acceptance Scenarios**:

1. **Given** an incoming email contains scheduling keywords ("meeting", "availability", "schedule", "call", "appointment"), **When** the orchestrator drafts a reply, **Then** it queries the Calendar MCP for events in the relevant time window and incorporates that context in the draft.
2. **Given** the Calendar MCP is unavailable, **When** a scheduling email needs a reply, **Then** the draft is still created with a note: "⚠️ Calendar data unavailable — verify availability manually before sending."
3. **Given** the calendar has conflicting events in a requested slot, **When** a reply is drafted, **Then** the draft accurately reflects the conflict and suggests alternative times.

---

### User Story 4 — WhatsApp Triage Channel (Priority: P3 — DEFERRED)

> **Clarified 2026-03-02**: This story is explicitly deferred. Phase 5 treats WhatsApp messages as capture-only (US1). The orchestrator does NOT auto-draft WhatsApp replies in Phase 5. US4 may be implemented as a bonus at the end of Phase 5 if P1/P2 are fully delivered with time to spare.

As the owner, WhatsApp messages are treated as actionable items — the orchestrator classifies them, generates draft WhatsApp replies, and presents them through the same HITL approval loop.

**Why this priority**: Bonus capability extending the system's reach. P1 stories cover minimum Silver tier requirements.

**Independent Test**: Send a WhatsApp message with an actionable request; verify the orchestrator produces a draft WhatsApp reply in `vault/Pending_Approval/` with `reply_type: whatsapp`.

**Acceptance Scenarios**:

1. **Given** a WhatsApp message is classified as actionable, **When** a draft WhatsApp reply is created, **Then** it follows the same `vault/Pending_Approval/` → HITL → send flow with `reply_type: whatsapp`.
2. **Given** an approved WhatsApp reply draft, **When** the owner approves, **Then** the system sends the reply via WhatsApp MCP to the original sender.

---

### Edge Cases

- **Owner WhatsApp unreachable**: System queues notification; retries 3× with exponential backoff (60s, 300s, 900s). After exhaustion, logs CRITICAL to `vault/Logs/`; draft remains in Pending_Approval.
- **Ambiguous approval reply** (e.g., "ok", "yes"): System sends clarification — no irreversible action taken.
- **Multiple pending drafts, approval without draft ID**: System replies with the list of pending draft IDs and asks to re-specify.
- **Calendar OAuth token expires**: System logs `auth_required` (ADR-0008), continues without calendar context, sends WhatsApp alert to re-authorize.
- **Vault filesystem full or unwritable**: System does NOT write to Pending_Approval, does NOT send HITL notification. Logs error; sends WhatsApp system alert.
- **Go bridge at :8080 unavailable** (when `WHATSAPP_BACKEND=go_bridge`): MCPClient falls back to `pywa` if configured; logs `mcp_unavailable`; escalates if both fail.
- **Incoming message contains password/OTP/PIN**: Privacy Gate intercepts, replaces with `[REDACTED]` before vault write; LLM never sees it; owner gets privacy alert.
- **Incoming message is an image/video/audio**: Privacy Gate blocks media content unconditionally; only metadata written to vault; media never passed to LLM; no AI analysis of any kind.
- **Someone sends a sensitive image** (any person's image, private content): System stores ONLY `media_type: image` + sender + timestamp. No content read, no AI processing, no forwarding. Owner is the only person who can view it directly via their own WhatsApp app.
- **Regex false positive** (e.g., a 6-digit order number flagged as OTP): System redacts and sends privacy alert. False positives are acceptable — the system errs on the side of privacy. Owner sees `[REDACTED]` in vault and can check their phone's WhatsApp for the original if needed.
- **Draft ID collision**: Draft ID = `<YYYYMMDD-HHMMSS>-<8-hex>` — collision probability is negligible; if detected, increment counter suffix.

---

## Requirements *(mandatory)*

### Functional Requirements

#### WhatsApp Watcher (`watchers/whatsapp_watcher.py`)

| ID      | Requirement |
|---------|-------------|
| FR-001  | MUST inherit `BaseWatcher` ABC (`watchers/base_watcher.py`); implement `poll()`, `process_item()`, `validate_prerequisites()`. |
| FR-002  | MUST continuously monitor an assigned WhatsApp number for incoming messages. Backend selectable via `WHATSAPP_BACKEND=pywa\|go_bridge` env var. |
| FR-003  | MUST write each received message to `vault/Needs_Action/<YYYYMMDD-HHMMSS>-wa-<message_id>.md` within 30 seconds using `atomic_write`. |
| FR-004  | Vault file MUST include: `message_id`, `sender_number`, `sender_name` (if known), `received_at` (ISO 8601), `body`, `media_type`, `source` (`known`/`unknown`). |
| FR-005  | MUST deduplicate by `message_id` — if vault file for that ID already exists, skip without error (idempotent). |
| FR-006  | MUST reconnect gracefully after connectivity interruptions using `_retry_with_backoff(max_retries=5, base_delay=30.0)`. |

#### WhatsApp MCP Server (`mcp_servers/whatsapp/server.py`)

| ID      | Requirement |
|---------|-------------|
| FR-007  | MUST be implemented using FastMCP + Pydantic v2 + stdio (ADR-0005). |
| FR-008  | MUST expose tool: `send_message(to: str, body: str) → SendResult`. |
| FR-009  | MUST expose tool: `health_check() → HealthResult` returning `{status, connected_number, backend}`. |
| FR-010  | MUST support both backends: pywa (Cloud API webhook) and Go bridge (`:8080`) selectable via `WHATSAPP_BACKEND`. |
| FR-011  | On send failure, MUST return structured error using ADR-0008 taxonomy (`send_failed`, `auth_required`, `rate_limited`). |

#### HITL Manager (`orchestrator/hitl_manager.py`)

| ID      | Requirement |
|---------|-------------|
| FR-012  | MUST write orchestrator-generated draft replies to `vault/Pending_Approval/<ISO-timestamp>-<draft-id>.md` before any send action, using `atomic_write`. |
| FR-013  | Pending_Approval file MUST use YAML frontmatter per Loop 3 format: `type: approval_request`, `action: send_email\|send_whatsapp`, `draft_id`, `reply_type`, `recipient`, `subject`, `status: pending`, `created_at`, `risk_level`, `reversible: false`. |
| FR-014  | MUST send a **batch summary WhatsApp message** to `OWNER_WHATSAPP_NUMBER` within 2 minutes of any new draft arriving in Pending_Approval. The batch message lists ALL currently pending unnotified drafts (max 5) in a single message. Each entry MUST include: priority tag (🔴 HIGH / 🟡 MED / 🟢 LOW), draft ID, recipient name/email, subject. Format example: `📋 3 drafts pending approval:\n1. [🔴 HIGH] a1b2c3d4 — boss@co.com — Re: Urgent...\n2. [🟡 MED] e5f6g7h8 — client@... — Re: Meeting...\nReply: approve a1b2 / reject a1b2` [Clarified 2026-03-02] |
| FR-014a | When a new draft arrives while a batch notification was already sent (i.e., within the same polling window), MUST send an updated batch message rather than a separate notification. |
| FR-014b | Maximum 5 drafts in Pending_Approval at one time. If cap is reached, new drafts are held in an in-memory queue and added to the next batch notification as existing drafts are cleared. |
| FR-015  | MUST listen for owner WhatsApp replies (via WhatsApp watcher event stream) and route by draft ID. |
| FR-016  | On "approve <draft-id>": MUST call Gmail MCP `send_email()`, move file to `vault/Approved/`, log decision to `vault/Logs/hitl_decisions.jsonl`. |
| FR-017  | On "reject <draft-id>": MUST NOT call Gmail MCP; MUST move file to `vault/Rejected/`; MUST send WhatsApp confirmation. |
| FR-018  | On ambiguous reply (no valid draft ID or unrecognized command): MUST send clarification message; MUST NOT take any irreversible action. |
| FR-019  | MUST send 24-hour reminder if no decision received; mark status `awaiting_reminder`. After 48 hours of total silence, mark `timed_out`; do NOT send email. |
| FR-020  | MUST support concurrent pending drafts identified by unique draft ID (`<YYYYMMDD-HHMMSS>-<8-hex>`). |

#### Calendar MCP Server (`mcp_servers/calendar/server.py`)

| ID      | Requirement |
|---------|-------------|
| FR-021  | MUST be implemented using FastMCP + Pydantic v2 + stdio (ADR-0005). |
| FR-022  | MUST expose tool: `list_events(time_min: datetime, time_max: datetime, max_results: int = 10) → EventList`. Default window when called by orchestrator: `time_min=now`, `time_max=now+7days`. [Clarified 2026-03-02] |
| FR-023  | MUST expose tool: `check_availability(time_slot_start: datetime, time_slot_end: datetime) → AvailabilityResult`. |
| FR-024  | MUST expose tool: `health_check() → HealthResult` returning `{status, calendar_id, email}`. |

#### Orchestrator Integration (`orchestrator/orchestrator.py`)

| ID      | Requirement |
|---------|-------------|
| FR-025  | Orchestrator MUST classify each email through a **three-layer priority classifier** before drafting: Layer 1 (rule-based spam/promo/auto-reply filter — skip drafting entirely, zero tokens); Layer 2 (keyword heuristic — urgent/ASAP/deadline/overdue → HIGH; meeting/schedule/availability/call/appointment → MED and triggers Calendar MCP query; otherwise → AMBIGUOUS, zero tokens); Layer 3 (LLM classification for AMBIGUOUS emails only — assigns HIGH/MED/LOW with one-sentence reasoning). [Clarified 2026-03-02] |
| FR-026  | Calendar MCP MUST be invoked via MCPClient (ADR-0007 + ADR-0009); direct Google API calls are forbidden. |
| FR-027  | If Calendar MCP returns `mcp_unavailable`, orchestrator MUST continue draft creation with a note in the body: "⚠️ Calendar data unavailable — verify availability manually." |
| FR-028  | Orchestrator MUST route all draft output through HITL Manager (FR-012) before any send; direct email sends are forbidden. |

#### Privacy & Content Safety *(non-negotiable — religious + security requirement)*

> **Owner requirement**: Per owner privacy requirement, sensitive media (images, video, audio) and sensitive text (passwords, OTPs, private data) must NEVER be stored, processed, or forwarded — even accidentally. This is a hard constraint with no exceptions.

| ID      | Requirement |
|---------|-------------|
| FR-031  | System MUST run a **Privacy Gate** on every incoming WhatsApp message BEFORE any vault write, LLM call, or HITL notification. The Privacy Gate is the FIRST step in `process_item()`. |
| FR-032  | **Sensitive text detection**: Privacy Gate MUST scan message body for sensitive patterns using regex: passwords (`password`, `pwd`, `pass`), PIN codes (`\bpin\b`, `\d{4,6}\b` near "pin"/"code"), OTPs (`otp`, `one.?time`, `verification code`, `\b\d{6}\b`), card numbers (13–19 consecutive digits), CVV (`cvv`, `cvc`), secret keys, tokens, credentials. Matched segments MUST be replaced with `[REDACTED]` in vault file. Original text is NEVER written to disk. |
| FR-033  | When FR-032 redacts content, system MUST send owner a privacy alert via WhatsApp: `"⚠️ Private/sensitive content detected in message from [sender]. Stored as REDACTED. AI did NOT read or process this."` The alert contains NO portion of the original content. |
| FR-034  | **Media absolute block**: System MUST NEVER store, read, process, analyze, forward, display, or pass to any LLM/API the binary content of any media message (image, video, audio, document, sticker). This is unconditional — no exceptions regardless of caption or context. |
| FR-035  | Vault file for a media message MUST contain ONLY: `media_type`, `caption` (text caption only, also Privacy-Gated per FR-032), `timestamp`, `sender_number`, `sender_name`, `message_id`. Field `body` MUST be: `"[MEDIA — content not stored]"`. |
| FR-036  | **LLM privacy gate**: System MUST NEVER send to any LLM API: (a) any text segment flagged as sensitive/redacted, (b) any image or media content, (c) any message body that failed the Privacy Gate. Violation of this rule is a critical bug. |
| FR-037  | **HITL notification privacy**: Batch summary notification MUST NEVER include sensitive/redacted text. For media messages, the batch entry reads: `"📎 [media_type] from [sender name] — [caption if clean, else 'no caption']"`. No media content, no redacted segments, no original sensitive text appears in any WhatsApp message the system sends. |
| FR-038  | **No forwarding without approval**: System MUST NEVER forward any message content (text or media) to any external party (email, WhatsApp reply, API) without explicit owner "approve" via the HITL flow. This is absolute — even for non-sensitive content. |
| FR-039  | Privacy Gate decisions MUST be logged to `vault/Logs/privacy_gate.jsonl`: `{message_id, sender_number, redaction_applied: bool, media_blocked: bool, timestamp}`. Log entry contains NO original sensitive content. |

#### Vault Operations

| ID      | Requirement |
|---------|-------------|
| FR-040  | All vault writes (Needs_Action, Pending_Approval, Approved, Rejected, Logs) MUST use `atomic_write` from `watchers/utils.py`. |
| FR-041  | HITL decisions MUST be logged to `vault/Logs/hitl_decisions.jsonl` as structured JSON: `{draft_id, decision, decided_at, decided_by, sent_at}`. |

### Key Entities

```
WhatsAppMessage:
  message_id: str          # WhatsApp unique message ID
  sender_number: str       # E.164 format
  sender_name: str | None
  body: str
  media_type: str          # "text" | "image" | "audio" | "video" | "document"
  received_at: datetime    # ISO 8601
  vault_path: Path

PendingApproval:
  draft_id: str            # <YYYYMMDD-HHMMSS>-<8-hex>
  reply_type: str          # "email" | "whatsapp"
  recipient: str
  subject: str
  body: str
  status: str              # "pending" | "approved" | "rejected" | "awaiting_reminder" | "timed_out"
  created_at: datetime
  decided_at: datetime | None
  risk_level: str          # "low" | "medium" | "high"
  reversible: bool         # always False for email send

HITLDecision:
  draft_id: str
  decision: str            # "approve" | "reject" | "timeout"
  decided_at: datetime
  decided_by: str          # owner WhatsApp number
  sent_at: datetime | None # only if approved

CalendarContext:
  query_time_min: datetime
  query_time_max: datetime
  events: list[CalendarEvent]
  has_conflicts: bool
  fetched_at: datetime
  error: str | None        # ADR-0008 error code if fetch failed

CalendarEvent:
  event_id: str
  summary: str
  start: datetime
  end: datetime
  attendees: list[str]
```

---

## Success Criteria *(mandatory)*

| ID     | Measurable Outcome | Target | Verification |
|--------|--------------------|--------|-------------|
| SC-001 | WhatsApp messages appear in `vault/Needs_Action/` after receipt | ≤ 30 seconds end-to-end | Integration test: send message → check vault file |
| SC-002 | HITL batch summary notification reaches owner's WhatsApp after first draft write | ≤ 2 minutes | Integration test: trigger draft → check WhatsApp batch message received with correct fields |
| SC-003 | Approved email sent after owner's approval reply | ≤ 60 seconds | Integration test: approve → verify Gmail sent |
| SC-004 | Approve/reject routed to correct draft with zero misdirected sends | 100% accuracy | Test: 3 concurrent drafts, approve each by ID |
| SC-005 | No email sent without explicit owner "approve" reply | Zero violations | Invariant test: check all sent emails have a matching approval log |
| SC-006 | Calendar context provided (or graceful fallback logged) in scheduling drafts when Calendar MCP is available | ≥ 95% | Sampling test over 20 scheduling emails |
| SC-007 | No partial vault files observable during normal operation | Zero partial files | Filesystem probe during concurrent writes |
| SC-008 | System recovers from 60-second connectivity drop without data loss | Full recovery | Chaos test: kill and restore WhatsApp bridge; verify no missed messages |
| SC-009 | Sensitive text (password/OTP/PIN patterns) is NEVER written to vault or sent to LLM — always replaced with `[REDACTED]` | Zero violations | Test: send message containing "password: abc123"; verify vault file contains `[REDACTED]`, LLM API logs show no original text |
| SC-010 | Media content (image/video/audio binary) is NEVER stored, processed by LLM, or forwarded | Zero violations | Test: send image; verify vault file has `[MEDIA — content not stored]`, no API call contains binary data |

---

## Scope & Boundaries

### In Scope

- **Privacy Gate** — mandatory pre-processing layer: sensitive text redaction (passwords, OTPs, PINs, card numbers) + unconditional media content block, before any vault write or LLM call
- WhatsApp message ingestion via pywa or Go bridge → `vault/Needs_Action/`
- HITL approval workflow: `vault/Pending_Approval/` → WhatsApp notify → approve/reject → Gmail MCP send
- WhatsApp MCP server (send_message, health_check)
- Google Calendar MCP server (list_events, check_availability, health_check) — read-only
- Concurrent pending draft management with unique draft IDs
- Graceful degradation when Calendar MCP is unavailable
- HITL audit log in `vault/Logs/hitl_decisions.jsonl`
- WHATSAPP_BACKEND env switch (pywa | go_bridge)

### Out of Scope

- Outbound WhatsApp messages for non-reply use cases (broadcast, notifications to third parties)
- WhatsApp group message handling (direct/individual messages only)
- Google Calendar write operations (creating/modifying events)
- Multi-owner / multi-approver workflows
- WhatsApp media file storage in vault (metadata only)
- SMS fallback for approval notifications
- Odoo, Neon DB, Oracle VM (Phase 6+)

---

## Vault Directory Additions (Phase 5)

```
vault/
├── Needs_Action/         ← existing; WhatsApp messages added here
├── Pending_Approval/     ← existing; HITL drafts written here
├── Approved/             ← existing; moved after approval
├── Rejected/             ← NEW: rejected drafts archived here
├── Logs/
│   └── hitl_decisions.jsonl  ← NEW: append-only HITL audit log
```

---

## MCP Servers (Phase 5)

| Server              | Path                                | Tools Exposed | Priority |
|---------------------|-------------------------------------|---------------|----------|
| `whatsapp_mcp`      | `mcp_servers/whatsapp/server.py`    | `send_message`, `health_check` | HIGH |
| `calendar_mcp`      | `mcp_servers/calendar/server.py`    | `list_events`, `check_availability`, `health_check` | MEDIUM |

Both servers follow ADR-0005 (FastMCP + Pydantic v2 + stdio) and ADR-0007 (MCPClient fallback protocol).

---

## Human Tasks Required

> Per `ai-control/HUMAN-TASKS.md`. These block Phase 5 implementation and MUST be completed before WH-MCP is tested live.

| ID     | Task | Status | Blocks |
|--------|------|--------|--------|
| HT-004 | Authenticate WhatsApp Web Session | **DONE** (2026-02-25) | ✅ Unblocked |
| HT-011 | Authorize Google Calendar API OAuth2 | **PENDING** | Calendar MCP live run |
| HT-012 | Configure pywa Cloud API credentials (if using pywa backend) | **PENDING** | pywa backend |

---

## Skills & Hooks Applied (Phase 5)

| Phase | Required Skill / Hook | Purpose |
|-------|-----------------------|---------|
| Spec  | `fetching-library-docs` (pywa) | pywa API surface discovery |
| Spec  | `fetching-library-docs` (Google Calendar) | events().list() signature |
| Build | `building-mcp-servers` | WhatsApp MCP + Calendar MCP scaffolding |
| Build | `scaffolding-fastapi-dapr` (optional) | If pywa webhook needs FastAPI host |
| QA    | `qa-overseer` | SC-001–SC-008 validation |
| QA    | `security-scan` | Secrets audit (OWNER_WHATSAPP_NUMBER, Calendar credentials) |
| QA    | `deployment-preflight-check` | Phase 5 exit gate |
| All   | `systematic-debugging` | When any integration test fails |
| Hooks | `PreToolUse` hook | Blocks shell if `.env` missing OWNER_WHATSAPP_NUMBER |
| Hooks | `PostToolUse` hook | path-warden fires after every vault file write |

---

## Dependencies

- **Phase 4 complete**: Gmail MCP + Obsidian MCP operational (HT-005 DONE ✅)
- **HT-004 DONE**: Go bridge running at `:8080`, WhatsApp paired ✅
- **pywa**: Python library for WhatsApp Cloud API (requires Meta Developer webhook setup — HT-012)
- **Google Calendar API**: OAuth2 credentials with `calendar.readonly` scope (HT-011)
- **BaseWatcher**: `watchers/base_watcher.py` — all watchers extend this
- **atomic_write**: `watchers/utils.py` — all vault writes use this
- **MCPClient**: `orchestrator/mcp_client.py` (ADR-0007/0009) — all MCP calls via this

---

## Assumptions

- `OWNER_WHATSAPP_NUMBER` is stored in `.env` in E.164 format (e.g., `+XXXXXXXXXXXX`).
- "Approve" and "reject" (with draft ID) are the only accepted HITL commands; no partial approval or edit-and-approve.
- Draft ID format: `<YYYYMMDD-HHMMSS>-<8-char-hex>` (e.g., `20260302-143022-a1b2c3d4`).
- Google Calendar OAuth2 follows the same credentials.json + token.json pattern as Gmail MCP.
- Orchestrator detects scheduling intent via keyword matching (same pattern as existing email classification in `orchestrator/orchestrator.py`).
- **Go bridge backend is the primary implementation** (HT-004 DONE — bridge at `:8080`, already authenticated). pywa Cloud API is a secondary fallback only if the Go bridge has issues (HT-012 remains DEFERRED). `WHATSAPP_BACKEND=go_bridge` is the default. [Clarified 2026-03-02]
- `vault/Rejected/` directory does not yet exist and must be created in Phase 5 setup.

---

## ADR Suggestions

> Per Constitution Section "Explicit ADR suggestions". These decisions have long-term architectural impact and should be documented before implementation.

📋 **Architectural decision detected**: HITL state machine design (pending → approved/rejected/timed_out) and concurrent draft ID routing strategy.
→ Document reasoning and tradeoffs? Run `/sp.adr hitl-state-machine-design`

📋 **Architectural decision detected**: WhatsApp backend selection (pywa Cloud API webhook vs. Go bridge at :8080) — affects Meta Developer dependency, webhook hosting, and session persistence.
→ Document reasoning and tradeoffs? Run `/sp.adr whatsapp-backend-selection`

📋 **Architectural decision detected**: 3-layer tiered email classifier (spam filter → keyword heuristic → LLM fallback) — long-term cost and accuracy implications for all email processing.
→ Document reasoning and tradeoffs? Run `/sp.adr tiered-email-priority-classifier`

📋 **Architectural decision detected**: Privacy Gate as mandatory pre-processing layer (sensitive text redaction + unconditional media block before any LLM call or vault write) — driven by security AND religious values; applies to all future watchers.
→ Document reasoning and tradeoffs? Run `/sp.adr privacy-gate-sensitive-content-policy`

---

## Agent Team Task Division (Preliminary)

> Formal task list generated by `/sp.tasks`. This is a preview for team assignment planning.

| Task Range | Assigned To | Work Package |
|------------|-------------|--------------|
| T00     | `@backend-builder` | Privacy Gate utility (`watchers/privacy_gate.py`): sensitive text redaction + media block + alert; tested in isolation first |
| T00b    | `@backend-builder` | Retrofit Privacy Gate into Gmail watcher (`gmail_watcher.py`) — one-line insertion; re-run existing Phase 2/3 tests to confirm no regression |
| T01–T03 | `@backend-builder` | WhatsApp watcher: pywa/bridge integration, message ingestion, vault writer |
| T04–T06 | `@modular-ai-architect` → `@backend-builder` | HITL state machine design + HITLManager implementation |
| T07–T09 | `@backend-builder` | WhatsApp notification sender + approve/reject listener + timeout handler |
| T10–T12 | `@backend-builder` | Calendar MCP server: list_events, check_availability, health_check |
| T13–T14 | `@backend-builder` | Orchestrator wiring: Calendar MCP + HITL Manager hooks |
| T15–T16 | `@backend-builder` | Concurrent draft ID management + `vault/Rejected/` setup |
| T17–T18 | `@qa-overseer` | Integration tests for full HITL cycle + SC-001–SC-008 validation |
| T19 | `@path-warden` (auto) | Validate all new file placements |
| T20 | All | Update ai-control/HUMAN-TASKS.md with HT-011 + HT-012 |

---

*Spec version 2.0.0 — enriched with full governance, RI, agent team SWARM plan, and Constitution compliance.*
*Generated: 2026-03-02 | Next: `/sp.clarify` (optional) → `/sp.plan` → `/sp.tasks` → `/sp.implement`*
