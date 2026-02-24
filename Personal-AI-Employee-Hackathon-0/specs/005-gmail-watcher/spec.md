# Feature Specification: Gmail Watcher -- Phase 2 Bronze Tier

**Feature Branch**: `005-gmail-watcher`
**Created**: 2026-02-17
**Status**: Complete ✅
**Phase**: 2 (First Watcher -- Bronze)
**Input**: User description: "Create BaseWatcher class and GmailWatcher for Phase 2 -- read Gmail inbox via OAuth2, parse emails, write actionable items as markdown files to vault/Needs_Action/"

## Governance Alignment

This specification is governed by the following project control documents. All requirements herein MUST comply with these references. Any conflict between this spec and a governance document MUST be resolved in favor of the governance document.

| Document | Principles Applied | Reference |
|----------|-------------------|-----------|
| Constitution | I (Spec-First), II (Local-First Privacy), III (HITL), IV (MCP-First), V (TDD), VI (Watcher Architecture), VII (Phase-Gated), IX (Security), X (Graceful Degradation) | `.specify/memory/constitution.md` |
| LOOP.md | Loop 1 (Spec-Driven), Loop 2 (Ralph Wiggum), Loop 4 (Directory Guard) | `ai-control/LOOP.md` |
| MCP.md | Gmail MCP (Needed #1), Fallback Protocol | `ai-control/MCP.md` |
| AGENTS.md | Backend-Builder (owner), DevOps-RAG-Engineer (infra), Spec-Architect (this spec) | `ai-control/AGENTS.md` |
| SWARM.md | Phase 2 config: Specialist Pair pattern | `ai-control/SWARM.md` |
| HUMAN-TASKS.md | HT-001 (Obsidian Vault), HT-002 (Gmail OAuth2), HT-005 (MCP Config) | `ai-control/HUMAN-TASKS.md` |

## Phase 2 Entry/Exit Criteria

Per Constitution Principle VII (Phase-Gated Delivery), Phase 2 MUST NOT begin until Phase 1 exit criteria are met, and Phase 3 MUST NOT begin until Phase 2 exit criteria are met.

### Entry Criteria (from Phase 1)

- [x] Obsidian vault initialized at `vault/` with canonical folder structure (HT-001 DONE)
- [x] `vault/Needs_Action/`, `vault/Inbox/`, `vault/Logs/`, `vault/Done/` directories exist
- [x] `Dashboard.md` and `Company_Handbook.md` templates created
- [x] Phase 1 QA-Overseer sign-off recorded
- [x] `/phase-execution-controller` validates Phase 1 complete

### Exit Criteria (for Phase 2)

- [x] BaseWatcher abstract class exists with lifecycle contract (start/stop/poll/process_item)
- [x] GmailWatcher extends BaseWatcher, connects via OAuth2, and reads inbox
- [x] Emails produce correctly formatted markdown files in vault directories
- [x] Duplicate prevention verified across 100+ poll cycles (SC-002)
- [x] Watcher runs for 24+ hours without memory leaks or crashes (SC-006)
- [x] Integration tests pass with mock Gmail data
- [x] All acceptance scenarios in this spec verified by QA-Overseer
- [x] `/phase-execution-controller` validates Phase 2 complete

## Constraints (DEFINE FIRST)

Per the Spec-Architect mandate: define what the system CANNOT do before defining what it CAN do.

### NOT Supported in Phase 2

- **No email sending** -- Sending email is Phase 4 (MCP Integration). This watcher is READ-ONLY.
- **No LLM-based classification** -- Email triage uses keyword/heuristic rules only. LLM classification is Phase 3 when the Ralph Wiggum reasoning loop (LOOP.md, Loop 2) is available.
- **No attachment processing** -- Email attachments are logged in frontmatter metadata but NOT downloaded or parsed.
- **No multi-account support** -- Only one Gmail account per watcher instance.
- **No label/folder filtering** -- Only the primary inbox is watched. Label-based routing is a future enhancement.
- **No cloud deployment** -- The watcher runs as a local long-lived process. Daemonization (tmux/systemd) is Phase 7 (Platinum).
- **No WhatsApp or Calendar watchers** -- Those are Phase 5+.
- **No direct API calls from agent code** -- Per Constitution Principle IV, all Gmail interactions MUST be routed through a Gmail MCP server or use the MCP Fallback Protocol (MCP.md) if the MCP is not yet operational.

### Performance Limits

- **Poll interval**: Configurable, default 60 seconds, minimum 30 seconds (to respect Gmail API quotas)
- **Processing latency**: New email to markdown file MUST complete within 90 seconds of email arrival (SC-001)
- **Memory ceiling**: Watcher process MUST NOT exceed 256 MB RSS after 24 hours of continuous operation
- **Gmail API quota**: MUST NOT exceed 250 quota units per user per second (Gmail API default)
- **Retry ceiling**: Maximum 3 retries per transient failure, with exponential backoff starting at 2 seconds (2s, 4s, 8s)
- **Ralph Wiggum safety**: If integrated into the reasoning loop in future phases, max iterations = 5 (LOOP.md)

### Security Boundaries (Constitution Principle IX)

- **Secrets**: `credentials.json` and `token.json` MUST NEVER be committed to version control. They MUST be listed in `.gitignore`.
- **Credentials**: All credential paths MUST be read from `.env` variables (`GMAIL_CREDENTIALS_PATH`, `GMAIL_TOKEN_PATH`). Hardcoding is FORBIDDEN.
- **Token storage**: OAuth2 tokens MUST be stored locally only. They MUST NOT sync to cloud (Constitution Principle II).
- **Data residency**: All email content MUST remain local in the Obsidian vault. No email data MUST be sent to external services.
- **Input validation**: All Gmail API responses MUST be validated before writing to vault (malformed data MUST NOT corrupt vault files).
- **Audit logging**: Every email processed MUST be logged to `vault/Logs/` with timestamp, message_id, classification, and outcome.

### Technical Debt (Known Limitations)

- Heuristic email classification will have lower accuracy than LLM-based classification (expected 80%+ per SC-005). This debt is resolved in Phase 3.
- Processed-ID tracking uses local file storage. Migration to database persistence is deferred to Phase 6 (Gold tier, Neon PostgreSQL).
- No health check endpoint exposed. Dashboard.md health integration is manual until Phase 3 orchestrator.

## Human-Dependent Prerequisites

Per `ai-control/HUMAN-TASKS.md`, the following tasks MUST be completed by a human before this feature can function. Claude CANNOT perform these tasks autonomously.

| Task ID | Task | Status | Blocks |
|---------|------|--------|--------|
| **HT-001** | Create Obsidian Vault and Folder Structure | PENDING | Vault directories for file output |
| **HT-002** | Set Up Gmail API OAuth2 Credentials | PENDING | `credentials.json` for authentication |
| **HT-005** | Add Gmail MCP Server Configuration | PENDING | MCP-first Gmail access (Phase 4 full use) |

**Verification protocol**: Before starting GmailWatcher for the first time, the system MUST verify:
1. `vault/Needs_Action/` directory exists (HT-001)
2. `credentials.json` exists at the path specified by `GMAIL_CREDENTIALS_PATH` (HT-002)
3. `.env` contains `GMAIL_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH` keys

If any check fails, the watcher MUST exit with a clear error message referencing the specific HT-xxx task and setup instructions.

## User Scenarios & Testing *(mandatory)*

### User Story 1 -- Email to Action Item (Priority: P1)

As a solo founder/CEO, I want my AI employee to automatically read my Gmail inbox and convert important emails into actionable markdown files in my Obsidian vault, so I never miss action items buried in email.

**Why this priority**: This is the core value proposition of Phase 2 and the Bronze tier. Without email-to-vault conversion, no downstream processing (Phase 3 reasoning loop, Phase 5 HITL approvals) can happen. This story maps directly to the Mind Map Architecture: Watcher Layer -> `/Needs_Action/` folder -> Reasoning Layer.

**Independent Test**: Can be fully tested by sending a test email to the configured Gmail account and verifying a markdown file appears in `vault/Needs_Action/` within 90 seconds. Delivers immediate value as a standalone email triage tool.

**Acceptance Scenarios**:

1. **Given** the GmailWatcher is running and authenticated, **When** a new unread email arrives in the inbox, **Then** a markdown file is created in `vault/Needs_Action/` with YAML frontmatter containing: type, from, subject, date, priority, status, message_id, and classification, plus the email body as markdown content.
2. **Given** the GmailWatcher is running, **When** it encounters an email that is purely informational (newsletter, notification, automated alert), **Then** it creates a markdown file in `vault/Inbox/` instead of `vault/Needs_Action/`.
3. **Given** the GmailWatcher has processed an email, **When** it runs again, **Then** it does NOT create a duplicate file for the same email (idempotency per Constitution Principle VI).
4. **Given** the GmailWatcher creates a file in `vault/Needs_Action/`, **When** the Ralph Wiggum loop (Phase 3) reads the vault, **Then** the file format is compatible with the LOOP.md state machine (status: PENDING in YAML frontmatter).

---

### User Story 2 -- Watcher Lifecycle Management (Priority: P2)

As a developer, I want a BaseWatcher abstract class that defines the standard interface for all watchers (Gmail, WhatsApp, Calendar), so that future watchers follow a consistent pattern and can be managed uniformly.

**Why this priority**: Architectural foundation. Per Constitution Principle VI (Watcher Architecture), ALL watchers MUST inherit from a common BaseWatcher class. Without this, each future watcher will be implemented inconsistently, making Phase 4+ integration painful.

**Independent Test**: Can be tested by instantiating a mock watcher that extends BaseWatcher, calling start/stop/poll, and verifying the lifecycle hooks fire correctly. No Gmail credentials required.

**Acceptance Scenarios**:

1. **Given** a watcher class that extends BaseWatcher, **When** `start()` is called, **Then** the watcher begins its polling loop and logs its initial state to `vault/Logs/`.
2. **Given** a running watcher, **When** `stop()` is called, **Then** it completes any in-progress work, saves its persistent state (WatcherState), and exits cleanly.
3. **Given** a watcher that encounters a transient error (network timeout, API error), **When** the error occurs during polling, **Then** the watcher retries up to 3 times with exponential backoff (2s, 4s, 8s) before logging the failure and continuing to the next poll cycle.
4. **Given** a watcher that encounters a fatal error (missing credentials, vault unreachable), **When** the error occurs, **Then** the watcher logs the error to `vault/Logs/` with severity CRITICAL and exits without crashing the parent process.
5. **Given** multiple watcher instances (e.g., GmailWatcher + future CalendarWatcher), **When** one watcher fails, **Then** the other watchers continue operating independently (Constitution Principle X: Graceful Degradation).

---

### User Story 3 -- OAuth2 Authentication Flow (Priority: P3)

As a user setting up the system for the first time, I want the Gmail watcher to guide me through OAuth2 authentication and securely store my tokens, so I only need to authenticate once.

**Why this priority**: Authentication is a prerequisite for P1 but only happens once. The flow should be smooth but is not the ongoing value. Depends on HT-002 completion.

**Independent Test**: Can be tested by running the auth flow with `credentials.json`, completing the browser consent, and verifying `token.json` is created and subsequent API calls succeed without re-authentication.

**Acceptance Scenarios**:

1. **Given** `credentials.json` exists but `token.json` does not, **When** the GmailWatcher starts, **Then** it opens a browser for OAuth2 consent and saves the resulting token to `token.json` at the path specified by `GMAIL_TOKEN_PATH`.
2. **Given** `token.json` exists and is valid, **When** the GmailWatcher starts, **Then** it authenticates silently without user interaction.
3. **Given** `token.json` exists but the refresh token has expired, **When** the GmailWatcher starts, **Then** it prompts the user to re-authenticate and updates `token.json`.
4. **Given** `credentials.json` is missing or malformed, **When** the GmailWatcher starts, **Then** it exits with a clear error message referencing HT-002 setup instructions from `ai-control/HUMAN-TASKS.md`.

---

### User Story 4 -- Vault File Routing and Ralph Wiggum Compatibility (Priority: P4)

As the system architect, I want watcher output files to follow the vault file routing conventions defined in the Mind Map and LOOP.md, so that the Phase 3 reasoning loop can consume them without modification.

**Why this priority**: This story ensures Phase 2 output is forward-compatible with Phase 3. Without correct file routing and frontmatter format, the Ralph Wiggum loop cannot pick up watcher output.

**Independent Test**: Can be tested by creating a sample watcher output file and verifying it passes validation against the LOOP.md state machine schema (status field, type field, routing to correct vault directory).

**Acceptance Scenarios**:

1. **Given** the GmailWatcher creates a markdown file, **When** the file is written to `vault/Needs_Action/`, **Then** its YAML frontmatter includes all fields required by the Ralph Wiggum loop state machine: `type`, `from`, `subject`, `priority`, `status` (set to "pending"), `created` (ISO 8601 timestamp), and `message_id`.
2. **Given** the GmailWatcher creates a file, **When** the filename is generated, **Then** it follows the pattern `YYYY-MM-DD-HHmm-<sanitized-subject>.md` where the sanitized subject contains only alphanumeric characters, hyphens, and underscores, truncated to 60 characters.
3. **Given** the GmailWatcher writes to the vault, **When** the Path-Warden agent (LOOP.md, Loop 4) validates the file location, **Then** the file passes directory validation (vault content MUST be in `vault/` per the canonical directory map).

---

### User Story 5 -- Observability and Health Reporting (Priority: P5)

As an operator, I want the Gmail watcher to log all its activity in a structured format to `vault/Logs/`, so I can monitor its health and diagnose issues from the Obsidian dashboard.

**Why this priority**: Constitution Principle X (Graceful Degradation) requires health checks and structured logging. This enables Dashboard.md integration.

**Independent Test**: Can be tested by starting the watcher, letting it run through 5 poll cycles, and verifying structured log entries exist in `vault/Logs/`.

**Acceptance Scenarios**:

1. **Given** the GmailWatcher starts, **When** it begins its first poll cycle, **Then** it writes a structured log entry to `vault/Logs/` with: timestamp, watcher_name ("gmail"), event ("started"), and status ("ok").
2. **Given** the GmailWatcher completes a poll cycle, **When** emails were processed, **Then** it writes a log entry with: emails_found count, emails_processed count, errors count, and next_poll_time.
3. **Given** the GmailWatcher encounters an error, **When** the error is logged, **Then** the log entry includes: severity (WARN/ERROR/CRITICAL), error_type, error_message, retry_count, and stack_trace_reference.

---

### Edge Cases

- **Gmail API rate limit hit**: The watcher backs off using exponential backoff (starting at 60 seconds for rate limits specifically) and retries after the rate limit window resets, logging the event to `vault/Logs/`.
- **`credentials.json` missing or malformed**: The watcher exits with a clear error message referencing HT-002 setup instructions. It MUST NOT attempt to create dummy credentials.
- **Vault directory does not exist**: The watcher checks for `vault/Needs_Action/` and `vault/Inbox/` at startup. If missing, it exits with an error referencing HT-001. It MUST NOT silently create vault directories (those belong to the Obsidian vault setup).
- **Two emails arrive simultaneously**: Each email produces its own markdown file with unique filenames (timestamp + sanitized subject). If filenames collide, a numeric suffix is appended (e.g., `-001`).
- **Email has no body (subject only)**: The watcher still creates the markdown file with available metadata. The body section is left empty with a note: "No email body content."
- **Network outage mid-poll**: The watcher logs the error, abandons the current cycle, and retries on the next poll interval. Partially processed emails are NOT written to vault (atomic write or nothing).
- **Email with extremely long subject (500+ characters)**: Subject is truncated to 200 characters in frontmatter and 60 characters in filename.
- **Email with non-UTF8 characters**: The watcher sanitizes encoding to UTF-8, replacing unmappable characters with a replacement character. Frontmatter MUST remain valid YAML.
- **OAuth token file corrupted**: The watcher detects invalid JSON in `token.json`, logs the error, deletes the corrupted file, and prompts re-authentication.
- **Watcher state file corrupted**: The watcher detects corruption, logs a warning, resets to a clean state (re-processes recent emails), and continues. This may produce duplicates for the reset window, which is acceptable as a recovery trade-off.
- **Multiple watcher instances started accidentally**: The watcher MUST use a file-based lock (`vault/Logs/.gmail_watcher.lock`) to prevent concurrent instances. A second instance MUST exit with a clear error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a BaseWatcher abstract class with `start()`, `stop()`, `poll()`, and `process_item()` methods, per Constitution Principle VI (Watcher Architecture).
- **FR-002**: System MUST implement GmailWatcher that extends BaseWatcher and connects to Gmail via OAuth2.
- **FR-003**: System MUST read unread emails from the authenticated Gmail inbox on each poll cycle.
- **FR-004**: System MUST classify each email as "actionable" or "informational" based on keyword/heuristic analysis (NOT LLM-based in Phase 2).
- **FR-005**: System MUST create a markdown file for each new email with YAML frontmatter containing: type, from, subject, date, priority, status, message_id, classification, and has_attachments.
- **FR-006**: System MUST route actionable emails to `vault/Needs_Action/` and informational emails to `vault/Inbox/`, per the Mind Map vault folder taxonomy.
- **FR-007**: System MUST track processed email IDs persistently to prevent duplicate file creation across restarts (idempotency per Constitution Principle VI).
- **FR-008**: System MUST implement retry logic with exponential backoff (3 retries, base 2 seconds) for transient API failures.
- **FR-009**: System MUST log all watcher state transitions, errors, and processing events to `vault/Logs/` with structured format.
- **FR-010**: System MUST support configurable poll interval (default: 60 seconds, minimum: 30 seconds).
- **FR-011**: System MUST handle OAuth2 token refresh automatically when the access token expires.
- **FR-012**: System MUST generate unique filenames using the pattern `YYYY-MM-DD-HHmm-<sanitized-subject>.md` with collision handling.
- **FR-013**: System MUST validate all environment prerequisites at startup (vault dirs, credentials, .env vars) and fail fast with actionable error messages referencing HT-xxx tasks.
- **FR-014**: System MUST use a file-based lock to prevent concurrent watcher instances.
- **FR-015**: System MUST write YAML frontmatter compatible with the Ralph Wiggum loop state machine (LOOP.md, Loop 2), including a `status: pending` field on all `vault/Needs_Action/` files.
- **FR-016**: System MUST operate independently of other watchers; a GmailWatcher failure MUST NOT affect other watcher instances (Constitution Principle X).
- **FR-017**: System MUST perform atomic file writes (write to temp file, then rename) to prevent corrupt partial files in the vault.

### Key Entities

- **BaseWatcher**: Abstract foundation for all watchers. Defines lifecycle (start/stop/poll/process_item), retry policy, logging contract, state persistence interface, and health check method. Per Constitution Principle VI, all watchers MUST inherit from this class.
- **GmailWatcher**: Concrete watcher for Gmail. Holds OAuth2 credentials reference, poll interval, and processed-email tracking state. Extends BaseWatcher.
- **EmailItem**: Represents a single parsed email with: sender, recipients, subject, body, date, message_id, labels, classification (actionable/informational), has_attachments flag, and raw_size.
- **WatcherState**: Persistent state across restarts -- last poll timestamp, set of processed message IDs, error count, total emails processed, uptime. Serialized to `vault/Logs/gmail_watcher_state.json`.
- **WatcherLogEntry**: Structured log entry with: timestamp, watcher_name, event, severity, details, and optional error information. Written to `vault/Logs/`.

## MCP Integration and Fallback Protocol

Per Constitution Principle IV (MCP-First) and `ai-control/MCP.md`:

### Current State (Phase 2)

Gmail MCP is listed as "Needed #1" in MCP.md with status: not yet operational. During Phase 2, the GmailWatcher MAY use the Gmail Python SDK (`google-api-python-client`) directly as the MCP Fallback Protocol permits:

```
1. Attempt MCP tool call
2. If MCP fails -> log error to /Logs/
3. Check fallback method in MCP registry
4. Execute fallback (Gmail Python SDK in this case)
5. If fallback fails -> escalate to human
6. NEVER silently skip the operation
```

### Future State (Phase 4)

When Gmail MCP is operational (after HT-005 completion), the GmailWatcher MUST be refactored to route all Gmail API calls through the MCP server. The Python SDK calls become the fallback, not the primary path.

### Registration Requirement

The Gmail MCP server MUST be registered in `ai-control/MCP.md` before it is used. Per MCP Development Standards, it MUST:
1. Have a spec in `specs/<mcp-name>/spec.md` before coding
2. Expose typed tool definitions with input validation
3. Be stateless (state lives in Obsidian vault)
4. Have contract tests
5. Define fallback behavior
6. Handle errors gracefully

## Enforcement Loop Integration

This feature participates in the following enforcement loops defined in `ai-control/LOOP.md`:

### Loop 1: Spec-Driven Loop

This specification (`specs/005-gmail-watcher/spec.md`) MUST exist and be approved before any implementation code is written. The implementation sequence is:
1. This spec (current document) -- MUST be approved
2. `specs/005-gmail-watcher/plan.md` -- Architecture decisions
3. `specs/005-gmail-watcher/tasks.md` -- Atomic implementation tasks
4. Implementation code in `watchers/` directory
5. Tests in `tests/` directory
6. QA-Overseer verification

### Loop 2: Ralph Wiggum Loop (Forward Compatibility)

The GmailWatcher output files MUST be compatible with the Ralph Wiggum loop state machine for Phase 3 consumption:

| State | Vault Location | YAML status field | Meaning |
|-------|---------------|-------------------|---------|
| PENDING | `vault/Needs_Action/` | `status: pending` | New email awaiting reasoning |
| IN_PROGRESS | `vault/Plans/` | `status: in_progress` | Claude is processing (Phase 3) |
| AWAITING_APPROVAL | `vault/Pending_Approval/` | `status: awaiting_approval` | Needs human review (Phase 5) |
| DONE | `vault/Done/` | `status: done` | Completed |
| FAILED | `vault/Logs/` | `status: failed` | Failed with RCA |

The GmailWatcher ONLY writes files with `status: pending` to `vault/Needs_Action/` or `vault/Inbox/`. State transitions beyond PENDING are the responsibility of the Phase 3 reasoning loop.

### Loop 4: Directory Guard

All file writes MUST comply with the canonical directory map in LOOP.md:
- Watcher source code: `watchers/`
- Vault output files: `vault/Needs_Action/`, `vault/Inbox/`
- Watcher logs: `vault/Logs/`
- Watcher state: `vault/Logs/gmail_watcher_state.json`
- Tests: `tests/`
- Spec artifacts: `specs/005-gmail-watcher/`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: New unread emails appear as markdown files in the vault within 90 seconds of arrival.
- **SC-002**: Zero duplicate files created across 100+ email processing cycles.
- **SC-003**: The watcher recovers from transient failures (network drops, API errors) without manual intervention in 95% of cases.
- **SC-004**: First-time OAuth2 setup completes in under 2 minutes with clear terminal guidance.
- **SC-005**: Email classification correctly routes actionable vs. informational emails with 80%+ accuracy (measured against a labeled test set of 50+ emails).
- **SC-006**: The watcher runs continuously for 24+ hours without memory leaks (RSS stays below 256 MB) or crashes.
- **SC-007**: A new watcher type (e.g., CalendarWatcher) can be created by extending BaseWatcher with fewer than 50 lines of watcher-specific code.
- **SC-008**: All startup prerequisite checks complete within 5 seconds and produce actionable error messages on failure.
- **SC-009**: Structured log entries in `vault/Logs/` are parseable by Obsidian Dataview plugin queries for Dashboard.md integration.

## Non-Functional Requirements

### Performance

- Poll cycle overhead (excluding Gmail API call): under 500 ms
- File write latency: under 100 ms per markdown file
- Memory: under 256 MB RSS after 24 hours continuous operation
- Gmail API calls per poll: 1-2 (list + batch get, not per-email calls)

### Scalability

- Phase 2 target: 1 Gmail account, up to 50 emails per poll cycle
- Processed-ID set: MUST handle up to 100,000 IDs without degradation
- State file size: MUST remain under 10 MB

### Security (Constitution Principle IX)

- OAuth2 credentials MUST use `.env` file paths, never hardcoded
- `credentials.json` and `token.json` MUST be in `.gitignore`
- Token refresh MUST NOT log token values (log token expiry time only)
- Email body content in vault files is local-only (Constitution Principle II)
- File-based lock prevents unauthorized concurrent access

### Observability (Constitution Principle X)

- All state transitions logged to `vault/Logs/`
- Log format MUST be structured (YAML or JSON) for Dataview queries
- Error logs MUST include severity, error type, and recovery action taken
- Health status MUST be queryable from `vault/Logs/gmail_watcher_state.json`
- Dashboard.md SHOULD reflect watcher health (manual integration in Phase 2, automated in Phase 3)

## Agent Assignments

Per `ai-control/AGENTS.md` and `ai-control/SWARM.md` Phase 2 configuration:

| Agent | Role | Deliverable |
|-------|------|-------------|
| **Spec-Architect** | Specification (this document) | `specs/005-gmail-watcher/spec.md` |
| **Backend-Builder** | Implementation | `watchers/base_watcher.py`, `watchers/gmail_watcher.py` |
| **DevOps-RAG-Engineer** | Infrastructure | Docker config, tmux scripts, test harness |
| **QA-Overseer** | Verification | Acceptance criteria validation, test review |
| **Loop-Controller** | Enforcement | Verify spec-driven loop compliance throughout |

**Swarm Pattern**: Specialist Pair (Backend-Builder + DevOps-RAG-Engineer) with Pipeline to QA-Overseer.

## Assumptions

- User has already completed HT-002 (Gmail OAuth2 setup) and `credentials.json` exists at the path specified by `GMAIL_CREDENTIALS_PATH` in `.env`.
- The Obsidian vault is initialized at `vault/` with the canonical folder structure (HT-001 completed).
- Email classification for Phase 2 uses simple keyword/heuristic analysis (NOT LLM-based). LLM classification is deferred to Phase 3 when the Ralph Wiggum reasoning loop is available.
- The watcher runs as a long-lived Python process (not serverless/cron). Persistent session management (tmux/systemd) is Phase 7 (Platinum).
- Only the primary inbox is watched (no label/folder filtering in Phase 2).
- The `.env` file exists with `GMAIL_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH` defined (verified: `.env` currently contains these variables).
- Gmail MCP is NOT yet operational. The MCP Fallback Protocol (MCP.md) authorizes direct Python SDK usage as the fallback.

## Scope

### In Scope

- BaseWatcher abstract class with full lifecycle (start/stop/poll/process_item)
- GmailWatcher with OAuth2 authentication extending BaseWatcher
- Email reading, parsing, and heuristic classification
- Markdown file generation with YAML frontmatter (Ralph Wiggum compatible)
- Vault file routing (actionable to `vault/Needs_Action/`, informational to `vault/Inbox/`)
- Duplicate prevention via persistent processed-ID tracking (idempotency)
- Retry logic with exponential backoff and structured error logging
- Startup prerequisite validation (fail-fast per ADR-013 pattern)
- File-based concurrent instance lock
- Structured logging to `vault/Logs/` for Dataview/Dashboard integration

### Out of Scope

- Sending emails (Phase 4 -- MCP Integration)
- LLM-based email classification (Phase 3 -- Claude reasoning loop)
- WhatsApp or Calendar watchers (Phase 5+)
- Cloud deployment / daemonization via tmux/systemd (Phase 7)
- Email attachment downloading or parsing (future enhancement)
- Multi-account Gmail support (future enhancement)
- Gmail MCP server implementation (Phase 4, separate spec required)
- HITL approval workflow for email responses (Phase 5)
- Database persistence for watcher state (Phase 6 -- Neon PostgreSQL)

## Dependencies

### Upstream (what this feature consumes)

- `credentials.json` from HT-002 (human-provided)
- `vault/` directory structure from HT-001 (human-created in Obsidian)
- `.env` file with `GMAIL_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH`
- Gmail API (external service, via Python SDK as MCP fallback)

### Downstream (what consumes this feature's output)

- **Phase 3 -- Ralph Wiggum Loop**: Reads `vault/Needs_Action/` files to begin reasoning
- **Phase 4 -- Gmail MCP**: GmailWatcher refactored to use MCP instead of direct SDK
- **Phase 5 -- HITL Approval**: Actionable items may trigger approval workflows
- **Phase 6 -- CEO Briefing**: Email summaries feed into Monday morning briefings
- **Dashboard.md**: Watcher health and email statistics displayed via Dataview queries

### External Services

- **Gmail API**: Via Google API Python client (MCP fallback path)
- **Google OAuth2**: For authentication token management
