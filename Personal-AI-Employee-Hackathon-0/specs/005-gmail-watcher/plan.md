# Implementation Plan: Gmail Watcher -- Phase 2 Bronze Tier

**Feature Branch**: `005-gmail-watcher`
**Spec**: `specs/005-gmail-watcher/spec.md` (Draft, 2026-02-17)
**Date**: 2026-02-17
**Status**: Accepted
**Author**: Spec-Architect (Opus)
**ADRs**: ADR-0001, ADR-0002, ADR-0003, ADR-0004

---

## 1. Context

### Why

Phase 2 of the Personal AI Employee delivers the first watcher -- the perception layer that converts Gmail inbox emails into structured Obsidian vault files. This is the Bronze tier deliverable and the foundation for all downstream phases (Phase 3 reasoning loop, Phase 4 MCP integration, Phase 5 HITL approval, Phase 6 CEO briefing).

Without a working Gmail watcher, the AI Employee has no sensory input. Every subsequent phase depends on the `vault/Needs_Action/` files that this watcher produces.

### Current State

- **Branch**: `005-gmail-watcher` (created from `main`)
- **Spec**: `specs/005-gmail-watcher/spec.md` is complete with 5 user stories, 17 functional requirements, 9 success criteria, and full edge case coverage
- **Constitution**: v1.0.0 ratified (2026-02-16) -- all 10 principles apply
- **Governance**: `ai-control/` directory established with AGENTS.md, LOOP.md, SWARM.md, MCP.md, HUMAN-TASKS.md
- **Infrastructure**: Project root exists with `.specify/`, `specs/`, `history/`, `ai-control/` directories
- **Vault**: Pending HT-001 (human must create Obsidian vault structure)
- **Gmail OAuth2**: Pending HT-002 (human must create credentials.json via Google Cloud Console)
- **Gmail MCP**: Not yet operational (MCP.md status: "Needed #1") -- MCP Fallback Protocol authorizes direct Python SDK usage

### Phase 2 Entry Requirements

Per Constitution Principle VII, Phase 2 MUST NOT begin until Phase 1 exit criteria are met:

- Obsidian vault initialized at `vault/` with canonical folder structure (HT-001)
- `vault/Needs_Action/`, `vault/Inbox/`, `vault/Logs/`, `vault/Done/` directories exist
- `Dashboard.md` and `Company_Handbook.md` templates created
- Phase 1 QA-Overseer sign-off recorded

---

## 2. Technical Context

### Runtime

| Constraint | Value | Source |
|------------|-------|--------|
| Python | 3.13+ | Constitution Tech Stack |
| Async model | `asyncio` with `asyncio.to_thread()` for sync SDK | ADR-0002 |
| Platform | Local machine (no cloud deployment in Phase 2) | Spec constraints |
| Process model | Long-lived async process, single instance per watcher | Spec FR-014 |
| Memory ceiling | 256 MB RSS after 24 hours | Spec NFR Performance |

### Dependencies

**Production (`requirements.txt`)**:

| Package | Version | Purpose |
|---------|---------|---------|
| google-api-python-client | >=2.100.0 | Gmail API access (MCP fallback path) |
| google-auth-oauthlib | >=1.2.0 | OAuth2 browser flow for first-time auth |
| google-auth-httplib2 | >=0.2.0 | HTTP transport for Google Auth |
| pyyaml | >=6.0 | YAML frontmatter rendering for vault files |
| python-dotenv | >=1.0.0 | `.env` file loading for credential paths |

**Development (`requirements-dev.txt`)**:

| Package | Version | Purpose |
|---------|---------|---------|
| pytest | >=8.0.0 | Test runner |
| pytest-asyncio | >=0.23.0 | Async test support for watcher lifecycle |
| pytest-cov | >=4.1.0 | Coverage reporting (>80% target) |

### Storage

| Artifact | Location | Format | Source |
|----------|----------|--------|--------|
| Watcher state | `vault/Logs/gmail_watcher_state.json` | JSON (single object) | ADR-0003 |
| Activity logs | `vault/Logs/gmail_watcher_YYYY-MM-DD.log` | JSONL (one JSON object per line) | ADR-0003 |
| Instance lock | `vault/Logs/.gmail_watcher.lock` | PID file | Spec FR-014 |
| Actionable emails | `vault/Needs_Action/YYYY-MM-DD-HHmm-subject.md` | Markdown + YAML frontmatter | Spec FR-005, FR-006 |
| Informational emails | `vault/Inbox/YYYY-MM-DD-HHmm-subject.md` | Markdown + YAML frontmatter | Spec FR-005, FR-006 |
| OAuth2 token | Path from `GMAIL_TOKEN_PATH` env var | JSON | Spec Security Boundaries |
| OAuth2 credentials | Path from `GMAIL_CREDENTIALS_PATH` env var | JSON | Spec Security Boundaries |

### Testing Strategy

Per Constitution Principle V (TDD mandated):

1. **Red**: Write tests first, verify they fail
2. **Green**: Implement until tests pass
3. **Refactor**: Clean up without breaking tests
4. **Coverage target**: >80% on `watchers/` package (SC target)
5. **Test types**: Unit tests (models, utils, base watcher, gmail watcher), integration tests (full cycle with mocked Gmail API)
6. **Async testing**: `pytest-asyncio` for all watcher lifecycle tests
7. **No live Gmail in CI**: All Gmail API calls mocked; live testing is manual (scripts/gmail_auth.py)

### Performance Budget

| Operation | Budget | Measurement |
|-----------|--------|-------------|
| Poll cycle overhead (excluding Gmail API) | <500 ms | Timer around `_run_poll_cycle()` minus API call time |
| File write latency | <100 ms per file | Timer around `atomic_write()` |
| Classification | <1 ms | Pure Python string matching, no I/O |
| Email parsing | <10 ms per email | Header extraction + body decode |
| Full poll (50 emails) | <90 seconds end-to-end | SC-001 requirement |
| Memory after 24h | <256 MB RSS | `psutil.Process().memory_info().rss` |

---

## 3. Architecture Decisions

Five architectural decisions were evaluated and accepted as ADRs. Each decision was tested against the three-part significance criteria (Impact + Alternatives + Scope = all true).

### ADR-0001: BaseWatcher as Abstract Base Class (ABC)

**Decision**: Use `abc.ABC` with `@abstractmethod` decorators for `BaseWatcher`, not `typing.Protocol`.

**Rationale**: Constitution Principle VI mandates "all watchers MUST inherit from a common BaseWatcher class." The volume of shared logic (retry, state, logging, locking, poll loop) makes a pure interface contract impractical -- Protocol would force duplication across every watcher. ABC provides both the contract and the shared implementation.

**Key consequences**:
- Abstract methods (`poll()`, `process_item()`, `validate_prerequisites()`) enforced at class-definition time
- Shared implementation (retry, state, logging, locking, poll loop) written once in base class
- Future watchers (CalendarWatcher, WhatsAppWatcher) get full infrastructure by inheriting -- SC-007 targets <50 lines of watcher-specific code
- Tight coupling accepted: subclasses are bound to base class implementation (mitigated by small, stable interface)
- Testing requires `MockWatcher` subclass rather than simple mock (mitigated by creating reusable test helper)

**Alternatives rejected**: `typing.Protocol` (no shared implementation), plain duck typing (no enforcement), mixin pattern (over-engineered for 3-5 watchers).

**Reference**: `history/adr/0001-watcher-base-class-design.md`

---

### ADR-0002: Async Polling with asyncio.to_thread()

**Decision**: Use `asyncio.to_thread()` to wrap all synchronous Gmail Python SDK calls, keeping the main watcher loop fully async with `asyncio.sleep()` for poll intervals.

**Rationale**: Constitution prohibits synchronous blocking I/O in watchers ("No synchronous blocking I/O in watchers; use async"). However, `google-api-python-client` is entirely synchronous. The Gmail MCP is not yet operational. `asyncio.to_thread()` bridges sync SDK calls into the async lifecycle without blocking the event loop, using zero additional dependencies (stdlib since Python 3.9).

**Key consequences**:
- Main event loop stays responsive -- multi-watcher concurrency via `asyncio.gather()` works naturally
- Clean migration path to async MCP: replace `await asyncio.to_thread(sync_call)` with `await mcp_tool_call()` -- same `await` pattern
- Signal handling (Ctrl+C / SIGTERM) works correctly with async loop via `loop.add_signal_handler()`
- Thread pool overhead negligible at 1-2 API calls per 60s poll cycle
- Cannot cancel in-flight sync SDK calls (accepted limitation)

**Alternatives rejected**: Fully synchronous with `time.sleep()` (Constitution violation), `aiohttp` + raw REST API (reimplements SDK), custom `ThreadPoolExecutor` (premature optimization), subprocess isolation (massive overhead).

**Reference**: `history/adr/0002-async-integration-pattern-for-sync-sdks.md`

---

### ADR-0003: JSON State Persistence + JSONL Daily Logs

**Decision**: Use JSON files for watcher state and JSONL (JSON Lines) for daily activity logs, both stored in `vault/Logs/`.

**Rationale**: Constitution Principle II mandates local-first storage. The spec names `vault/Logs/gmail_watcher_state.json` explicitly. Obsidian with Dataview plugin is the primary monitoring UI (SC-009). JSON/JSONL is human-readable in Obsidian, parseable by Dataview, and requires zero additional dependencies.

**Key consequences**:
- State file: `vault/Logs/gmail_watcher_state.json` -- single JSON object, atomic writes via `os.replace()` (FR-017)
- Log files: `vault/Logs/gmail_watcher_YYYY-MM-DD.log` -- one JSON object per line, append-only
- Corrupt state recovery: log warning, reset to clean `WatcherState`, accept brief re-processing window
- FIFO pruning at 100,000 processed IDs to keep state file under ~10 MB
- Natural daily log rotation, no daemon required (~500 KB/day at 60s polls)
- Phase 6 migration to Neon PostgreSQL is known technical debt, requires migration script

**Alternatives rejected**: SQLite (not human-readable in Obsidian, breaks Dataview), YAML state + plain text logs (YAML type coercion bugs, no structured log queries), single JSON file for everything (unbounded growth, full rewrite on every append).

**Reference**: `history/adr/0003-local-file-based-data-persistence.md`

---

### ADR-0004: Keyword Heuristic Email Classification

**Decision**: Use keyword score dictionaries applied to sender, subject, and first 500 characters of body text, with a default-to-actionable policy.

**Rationale**: The spec explicitly constrains Phase 2 to keyword/heuristic analysis -- LLM-based classification is deferred to Phase 3 when the Ralph Wiggum reasoning loop is available. Target accuracy is 80%+ (SC-005). Default-to-actionable is the safer policy: missing an actionable email is worse than surfacing an informational one.

**Key consequences**:
- `ACTIONABLE_KEYWORDS` dict: "urgent":3, "action required":5, "deadline":3, "please review":4, "approve":4, "meeting":2, "invoice":3
- `INFORMATIONAL_KEYWORDS` dict: "newsletter":5, "unsubscribe":4, "no-reply":3, "digest":3, "automated":3, "notification":2
- `INFORMATIONAL_SENDER_PATTERNS`: regex patterns for `noreply@`, `notifications@`, `newsletter@`, `*@github.com`
- Scoring: if `informational_score > actionable_score + threshold(2)`, classify INFORMATIONAL; otherwise ACTIONABLE
- Case-insensitive matching on all comparisons
- Classification method `_classify_email()` is isolated -- Phase 3 swaps it for LLM call without touching watcher lifecycle
- Zero external dependencies, deterministic, microsecond execution

**Alternatives rejected**: LLM-based classification (explicitly out of Phase 2 scope), pre-trained ML model (no training data, heavy dependencies), regex-only (no scoring nuance), always-actionable (no value).

**Reference**: `history/adr/0004-keyword-heuristic-email-classification.md`

---

### ADR-0005 (Implicit): JSONL Daily Logs with Daily Rotation

This decision is embedded in ADR-0003 but warrants explicit mention. Activity logs use JSONL format with one file per day (`gmail_watcher_YYYY-MM-DD.log`). Each line is a complete JSON object with `timestamp`, `watcher_name`, `event`, `severity`, and `details`. This enables:

- `grep` and `jq` from command line
- Dataview queries in Obsidian Dashboard.md (SC-009)
- Natural daily rotation without log management daemons
- Append-only writes (no corruption risk from concurrent reads)

---

## 4. Implementation Order

### 4.1 Files to Create (12 source files + 1 script)

| # | File | Phase | Purpose | Dependencies |
|---|------|-------|---------|--------------|
| 1 | `watchers/models.py` | A | Data models: Classification, LogSeverity, EmailItem, WatcherState, WatcherLogEntry | None |
| 2 | `watchers/utils.py` | A | Utilities: sanitize_filename, atomic_write, sanitize_utf8, truncate_subject, render_yaml_frontmatter, FileLock, PrerequisiteError, load_env | pyyaml, python-dotenv |
| 3 | `tests/conftest.py` | A | Shared fixtures: tmp_vault, sample_email_item, sample_raw_gmail_message, mock_gmail_service, mock_env | pytest |
| 4 | `tests/unit/test_models.py` | A | Unit tests for all models | watchers.models |
| 5 | `tests/unit/test_utils.py` | A | Unit tests for all utilities | watchers.utils |
| 6 | `watchers/base_watcher.py` | B | BaseWatcher ABC with lifecycle, retry, state, logging, locking | watchers.models, watchers.utils |
| 7 | `tests/unit/test_base_watcher.py` | B | Unit tests for BaseWatcher via MockWatcher subclass | watchers.base_watcher |
| 8 | `watchers/gmail_watcher.py` | C | GmailWatcher: OAuth2, poll, parse, classify, process, render | watchers.base_watcher, google-api-python-client |
| 9 | `scripts/gmail_auth.py` | C | Standalone OAuth2 helper for first-time setup | google-auth-oauthlib |
| 10 | `tests/unit/test_gmail_watcher.py` | C | Unit tests for GmailWatcher (auth, parse, classify, render, process) | watchers.gmail_watcher |
| 11 | `tests/integration/test_gmail_integration.py` | D | Integration tests: full cycle, duplicates, state persistence, routing | watchers.gmail_watcher |
| 12 | `watchers/__init__.py` | A (update) | Re-exports: Classification, EmailItem, WatcherState, BaseWatcher, GmailWatcher | All watchers modules |

### 4.2 Dependency Chain (4 Phases)

```
Phase A: Models & Utilities (no internal dependencies)
  ├── watchers/models.py          (standalone)
  ├── watchers/utils.py           (standalone, uses pyyaml + dotenv)
  ├── tests/conftest.py           (depends on models)
  ├── tests/unit/test_models.py   (depends on models)
  └── tests/unit/test_utils.py    (depends on utils)

Phase B: Base Watcher (depends on Phase A)
  ├── watchers/base_watcher.py          (imports models + utils)
  └── tests/unit/test_base_watcher.py   (imports base_watcher)

Phase C: Gmail Watcher (depends on Phase B)
  ├── watchers/gmail_watcher.py          (extends base_watcher)
  ├── scripts/gmail_auth.py              (standalone auth helper)
  └── tests/unit/test_gmail_watcher.py   (imports gmail_watcher)

Phase D: Integration & Polish (depends on Phase C)
  ├── tests/integration/test_gmail_integration.py
  └── watchers/__init__.py (final re-exports)
```

### 4.3 Implementation Sequence within Each Phase

**Phase A -- Models & Utilities** (~25 min):
1. Write `tests/unit/test_models.py` (RED -- tests fail, no implementation)
2. Write `tests/unit/test_utils.py` (RED -- tests fail, no implementation)
3. Implement `watchers/models.py` (Classification, LogSeverity, EmailItem, WatcherState, WatcherLogEntry)
4. Implement `watchers/utils.py` (sanitize_filename, atomic_write, sanitize_utf8, truncate_subject, render_yaml_frontmatter, FileLock, PrerequisiteError, load_env)
5. Create `tests/conftest.py` with shared fixtures
6. Run `pytest tests/unit/test_models.py tests/unit/test_utils.py -v` (GREEN)
7. **Checkpoint**: All model and utility tests pass

**Phase B -- Base Watcher** (~25 min):
1. Write `tests/unit/test_base_watcher.py` with MockWatcher subclass (RED)
2. Implement `watchers/base_watcher.py` (BaseWatcher ABC with full lifecycle)
3. Run `pytest tests/unit/test_base_watcher.py -v` (GREEN)
4. **Checkpoint**: BaseWatcher lifecycle fully functional

**Phase C -- Gmail Watcher** (~45 min):
1. Write `tests/unit/test_gmail_watcher.py` (RED)
2. Implement `watchers/gmail_watcher.py` (GmailWatcher with OAuth2, poll, parse, classify, process, render)
3. Implement `scripts/gmail_auth.py` (standalone OAuth2 helper)
4. Run `pytest tests/unit/test_gmail_watcher.py -v` (GREEN)
5. **Checkpoint**: Full email-to-vault pipeline works (MVP)

**Phase D -- Integration & Polish** (~20 min):
1. Write `tests/integration/test_gmail_integration.py`
2. Update `watchers/__init__.py` with final re-exports
3. Run `pytest tests/ -v --cov=watchers --cov-report=term-missing` (GREEN, >80% coverage)
4. **Checkpoint**: All tests pass, coverage met, integration verified

---

## 5. YAML Frontmatter Contract (Ralph Wiggum Compatible)

Per spec FR-005, FR-015, and User Story 4, every markdown file written by the GmailWatcher MUST contain YAML frontmatter compatible with the Ralph Wiggum loop state machine (LOOP.md, Loop 2).

### Required Fields

```yaml
---
type: email
status: pending
source: gmail
message_id: "<Gmail message ID>"
from: "sender@example.com"
subject: "Email subject (truncated to 200 chars)"
date_received: "2026-02-17T14:30:00Z"
date_processed: "2026-02-17T14:30:45Z"
classification: "actionable"
priority: "standard"
has_attachments: false
watcher: "gmail_watcher"
---

Email body content here as markdown...
```

### Field Constraints

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `type` | string | `"email"` | Fixed for GmailWatcher |
| `status` | string | `"pending"` | Ralph Wiggum initial state; Phase 3 transitions to in_progress/done/failed |
| `source` | string | `"gmail"` | Watcher source identifier |
| `message_id` | string | Gmail API message ID | Unique identifier for dedup |
| `from` | string | Sender email address | Extracted from `From` header |
| `subject` | string | Truncated to 200 chars | `truncate_subject()` applied |
| `date_received` | string | ISO 8601 timestamp | From email `Date` header |
| `date_processed` | string | ISO 8601 timestamp | When watcher processed the email |
| `classification` | string | `"actionable"` or `"informational"` | From `_classify_email()` |
| `priority` | string | `"standard"` | Fixed in Phase 2; Phase 3 may upgrade |
| `has_attachments` | boolean | `true` / `false` | Detected from MIME parts |
| `watcher` | string | `"gmail_watcher"` | Watcher instance name |

### Ralph Wiggum State Mapping

| GmailWatcher Output | YAML `status` | Vault Location | Next Actor |
|---------------------|---------------|----------------|------------|
| Actionable email | `pending` | `vault/Needs_Action/` | Ralph Wiggum (Phase 3) |
| Informational email | `pending` | `vault/Inbox/` | Human review / auto-archive |

The GmailWatcher ONLY writes files with `status: pending`. All state transitions beyond PENDING are the responsibility of the Phase 3 reasoning loop.

---

## 6. Source Code Layout

```
watchers/
  __init__.py              # Public API re-exports
  models.py                # Classification, LogSeverity, EmailItem, WatcherState, WatcherLogEntry
  utils.py                 # sanitize_filename, atomic_write, sanitize_utf8, truncate_subject,
                           #   render_yaml_frontmatter, FileLock, PrerequisiteError, load_env
  base_watcher.py          # BaseWatcher ABC (start, stop, poll, process_item, retry, state, logging, locking)
  gmail_watcher.py         # GmailWatcher (OAuth2, _fetch_unread_emails, _parse_email, _classify_email,
                           #   _generate_filename, _render_markdown, _get_vault_target_dir, process_item, poll)

scripts/
  gmail_auth.py            # Standalone OAuth2 setup helper (browser flow, token save, profile verify)

tests/
  conftest.py              # Shared fixtures (tmp_vault, sample_email_item, sample_raw_gmail_message,
                           #   mock_gmail_service, mock_env)
  unit/
    test_models.py         # Classification, LogSeverity, EmailItem, WatcherState, WatcherLogEntry tests
    test_utils.py          # sanitize_filename, atomic_write, sanitize_utf8, truncate_subject,
                           #   render_yaml_frontmatter, FileLock, load_env tests
    test_base_watcher.py   # MockWatcher + lifecycle, retry, state, logging, locking, health check tests
    test_gmail_watcher.py  # Auth, parse, classify, render, process, poll, routing, compatibility tests
  integration/
    test_gmail_integration.py  # Full cycle, duplicate prevention, state persistence, routing accuracy,
                               #   error recovery, concurrent lock prevention tests
```

### Module Dependency Graph

```
                    models.py  (no imports from watchers/)
                        |
                    utils.py   (imports models.py for PrerequisiteError only)
                        |
                  base_watcher.py  (imports models.py + utils.py)
                        |
                  gmail_watcher.py (imports base_watcher.py + models.py + utils.py)
                        |
                   __init__.py     (re-exports from all modules)
```

---

## 7. Vault Output Layout

```
vault/
  Needs_Action/
    2026-02-17-1430-urgent-please-review-contract.md          # Actionable email
    2026-02-17-1445-invoice-from-acme-corp.md                 # Actionable email
    2026-02-17-1502-meeting-tomorrow-at-3pm.md                # Actionable email

  Inbox/
    2026-02-17-1435-weekly-newsletter-from-techcrunch.md      # Informational email
    2026-02-17-1440-github-notification-pr-merged.md          # Informational email

  Logs/
    gmail_watcher_state.json                                   # Persistent watcher state
    gmail_watcher_2026-02-17.log                               # Daily JSONL activity log
    .gmail_watcher.lock                                        # PID-based instance lock

  Done/           # (Empty in Phase 2 -- Phase 3 moves completed items here)
```

### Filename Pattern

```
YYYY-MM-DD-HHmm-<sanitized-subject>.md
```

Where `<sanitized-subject>` is:
- Lowercased
- Non-alphanumeric characters replaced with hyphens
- Multiple consecutive hyphens collapsed to single hyphen
- Leading/trailing hyphens stripped
- Truncated to 60 characters
- Collision suffix appended if file exists: `-001`, `-002`, etc.

### State File Schema (`gmail_watcher_state.json`)

```json
{
  "last_poll_timestamp": "2026-02-17T14:30:00Z",
  "processed_ids": ["msg_abc123", "msg_def456", "...up to 100k"],
  "error_count": 0,
  "total_emails_processed": 42,
  "uptime_start": "2026-02-17T08:00:00Z"
}
```

### Log Entry Schema (JSONL line)

```json
{"timestamp": "2026-02-17T14:30:45Z", "watcher_name": "gmail_watcher", "event": "poll_complete", "severity": "info", "details": {"emails_found": 3, "emails_processed": 3, "errors": 0, "next_poll_time": "2026-02-17T14:31:45Z"}}
```

---

## 8. Constitution Compliance

Every implementation decision maps back to a Constitution principle. This table ensures no principle is overlooked.

| Principle | Requirement | How This Plan Satisfies It | Verified By |
|-----------|-------------|---------------------------|-------------|
| **I. Spec-Driven** | Spec before code | This plan follows `spec.md`; `tasks.md` follows this plan; code follows tasks | Loop-Controller enforcement |
| **II. Local-First Privacy** | All data local, secrets in `.env` | Vault files local-only; credentials via `.env` vars; token.json local-only; no cloud sync | Security scan pre-push |
| **III. HITL for Sensitive Actions** | Approval for external sends | Phase 2 is READ-ONLY; no email sending; no HITL needed yet | Spec constraints section |
| **IV. MCP-First** | External calls via MCP | Gmail MCP not operational; MCP Fallback Protocol authorizes direct Python SDK; clean migration path via ADR-0002 | MCP.md registry |
| **V. TDD** | Tests first, >80% coverage | TDD mandated in tasks.md; all phases start with RED tests; coverage target in Phase D | `pytest --cov` in Phase D |
| **VI. Watcher Architecture** | BaseWatcher inheritance, idempotency | ADR-0001 defines ABC; processed_ids prevent duplicates; structured markdown with YAML frontmatter | test_base_watcher.py, test_gmail_watcher.py |
| **VII. Phase-Gated** | Entry/exit criteria, no phase skip | Phase 2 entry criteria checked; exit criteria defined in spec; `/phase-execution-controller` validates | QA-Overseer sign-off |
| **VIII. Reusable Intelligence** | PHRs for every prompt, ADRs for decisions | ADR-0001 through ADR-0004 created; PHRs created per session | history/adr/, history/prompts/ |
| **IX. Security by Default** | No hardcoded secrets, input validation | `.env` for all credential paths; `.gitignore` blocks credentials.json/token.json; all Gmail API responses validated before vault write | Security scan, `.gitignore` audit |
| **X. Graceful Degradation** | Independent failure, structured logging, health checks | BaseWatcher retry with backoff (ADR-0001); JSONL structured logs (ADR-0003); health_check() method; file lock prevents concurrent corruption | test_retry_*, test_log_*, test_health_check |

---

## 9. Human Prerequisites

Two human tasks MUST be completed before the GmailWatcher can operate. These are documented in `ai-control/HUMAN-TASKS.md` and referenced throughout the spec.

### HT-001: Create Obsidian Vault and Folder Structure

**What**: Initialize Obsidian vault at `vault/` with the canonical folder taxonomy.

**Required directories**:
```
vault/
  Needs_Action/
  Inbox/
  Logs/
  Done/
  Plans/
  Pending_Approval/
  Approved/
```

**Required files**:
- `vault/Dashboard.md` -- system health dashboard template
- `vault/Company_Handbook.md` -- operational handbook template

**Verification**: GmailWatcher `validate_prerequisites()` checks for `vault/Needs_Action/`, `vault/Inbox/`, `vault/Logs/` at startup. Missing directories cause a `PrerequisiteError` with message: "Vault directory not found. Complete HT-001: Create Obsidian Vault and Folder Structure. See ai-control/HUMAN-TASKS.md".

**Status**: PENDING

---

### HT-002: Set Up Gmail API OAuth2 Credentials

**What**: Create a Google Cloud project, enable the Gmail API, create OAuth2 Desktop Application credentials, and download `credentials.json`.

**Steps** (human-executed):
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the Gmail API
4. Configure OAuth consent screen (External, test mode is fine)
5. Create OAuth 2.0 Client ID (Desktop application type)
6. Download the client configuration as `credentials.json`
7. Place `credentials.json` at the path specified by `GMAIL_CREDENTIALS_PATH` in `.env`
8. Ensure `.env` contains both `GMAIL_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH`

**Required `.env` variables**:
```
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
```

**OAuth2 scopes** (requested by `scripts/gmail_auth.py` and `GmailWatcher._authenticate()`):
- `https://www.googleapis.com/auth/gmail.readonly` -- Read inbox (Phase 2)
- `https://www.googleapis.com/auth/gmail.send` -- Send email (Phase 4, future-proofing)
- `https://www.googleapis.com/auth/gmail.modify` -- Modify labels (Phase 4, future-proofing)

**Verification**: GmailWatcher `validate_prerequisites()` checks:
1. `GMAIL_CREDENTIALS_PATH` env var exists
2. `GMAIL_TOKEN_PATH` env var exists
3. File at `GMAIL_CREDENTIALS_PATH` exists and is readable

Missing or invalid triggers `PrerequisiteError` with message: "Gmail credentials not found. Complete HT-002: Set Up Gmail API OAuth2 Credentials. See ai-control/HUMAN-TASKS.md".

**Status**: PENDING

---

## 10. Verification Plan

### 10.1 Unit Tests (Automated)

| Test File | Covers | Count | Phase |
|-----------|--------|-------|-------|
| `tests/unit/test_models.py` | Classification, LogSeverity, EmailItem, WatcherState, WatcherLogEntry | ~12 tests | A |
| `tests/unit/test_utils.py` | sanitize_filename, atomic_write, sanitize_utf8, truncate_subject, render_yaml_frontmatter, FileLock, load_env | ~20 tests | A |
| `tests/unit/test_base_watcher.py` | MockWatcher lifecycle, retry, state persistence, logging, locking, health check, poll interval validation | ~11 tests | B |
| `tests/unit/test_gmail_watcher.py` | OAuth2 auth (new/existing/expired/corrupt token), prerequisites, parse (full/no-body/non-utf8), classify (actionable/informational/default), filename (normal/collision), render markdown, process (routing), poll (dedup), async thread wrapping, Ralph Wiggum compatibility, filename pattern, directory compliance | ~24 tests | C |

### 10.2 Integration Tests (Automated, Mocked Gmail)

| Test | Description | Phase |
|------|-------------|-------|
| `test_full_email_cycle` | 3 emails (2 actionable, 1 informational) through complete pipeline; verify file count and frontmatter | D |
| `test_duplicate_prevention_across_cycles` | Same 3 emails across 5 poll cycles; verify exactly 3 files | D |
| `test_state_persistence_across_restart` | Process, save, new instance, load, poll; verify no new files | D |
| `test_classification_routing_accuracy` | 10 emails (5 actionable, 5 informational); verify all routed correctly | D |
| `test_error_recovery_mid_cycle` | Fail on 2nd of 5 emails; verify 1st processed, error logged, next cycle retries | D |
| `test_concurrent_lock_prevention` | Start watcher, attempt second instance; verify lock error | D |

### 10.3 Manual Verification (Post-Implementation)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Run `python scripts/gmail_auth.py` | Browser opens, consent screen appears, token.json created, profile printed |
| 2 | Send test email to configured Gmail account | Email appears in inbox |
| 3 | Run `python -m watchers.gmail_watcher` | Watcher starts, polls, creates markdown file in vault/Needs_Action/ |
| 4 | Check vault/Needs_Action/ | File exists with correct YAML frontmatter and email body |
| 5 | Wait for next poll cycle | Same email NOT re-processed (check logs) |
| 6 | Send newsletter-style email | File appears in vault/Inbox/ (not Needs_Action/) |
| 7 | Check vault/Logs/ | JSONL log file exists with structured entries |
| 8 | Ctrl+C the watcher | Graceful shutdown, state saved, lock released |
| 9 | Restart watcher | State loaded, previous emails not re-processed |
| 10 | Attempt second instance | Error message about existing lock |

### 10.4 Coverage Report

```bash
pytest tests/ -v --cov=watchers --cov-report=term-missing
```

**Target**: >80% line coverage on `watchers/` package.

**Expected coverage gaps** (acceptable):
- `scripts/gmail_auth.py` (manual-only, not in `watchers/` package)
- `__main__` block in `gmail_watcher.py` (CLI entry point)
- Signal handler registration (platform-dependent)

---

## 11. Risks

### Risk 1: Gmail API Quota Exhaustion

**Likelihood**: Low (default quota is 250 units/user/second; we use 1-2 calls per 60s)
**Impact**: Medium (polling stops until quota resets)
**Mitigation**: Minimum 30s poll interval enforced; exponential backoff on 429 responses; rate-limit-specific backoff starting at 60 seconds (spec edge case)

### Risk 2: OAuth2 Token Expiry During Long-Running Operation

**Likelihood**: Medium (access tokens expire after ~1 hour; refresh tokens can expire after extended inactivity)
**Impact**: Medium (polling fails until re-authentication)
**Mitigation**: `_authenticate()` checks `creds.valid` before each poll; automatic `creds.refresh()` for expired access tokens; corrupt/expired refresh token triggers clear error message referencing HT-002

### Risk 3: Heuristic Classification Accuracy Below 80%

**Likelihood**: Medium (keyword scoring is inherently limited for nuanced emails)
**Impact**: Low (default-to-actionable means worst case is informational emails in Needs_Action/)
**Mitigation**: ADR-0004 documents the trade-off; Phase 3 replaces with LLM classification; `_classify_email()` is isolated for clean swap; keyword lists can be tuned post-deployment

### Risk 4: State File Corruption on Unexpected Process Death

**Likelihood**: Low (atomic write via `os.replace()` is crash-safe on most filesystems)
**Impact**: Medium (state reset causes re-processing of recent emails, producing duplicates)
**Mitigation**: ADR-0003 accepts brief re-processing window on corrupt recovery; atomic_write uses temp file + os.replace(); FileLock prevents concurrent state writes

### Risk 5: Human Prerequisites (HT-001, HT-002) Not Completed

**Likelihood**: High (human tasks are the most common blockers)
**Impact**: Critical (watcher cannot start at all)
**Mitigation**: `validate_prerequisites()` fails fast with clear error messages referencing specific HT-xxx tasks; `scripts/gmail_auth.py` provides guided setup; HUMAN-TASKS.md provides step-by-step instructions

---

## 12. Next Steps

1. **Generate `tasks.md`**: Break this plan into atomic, testable implementation tasks with TDD ordering (Red -> Green -> Checkpoint per phase). **DONE** -- see `specs/005-gmail-watcher/tasks.md`

2. **Complete HT-001**: Human creates Obsidian vault and folder structure at `vault/`.

3. **Complete HT-002**: Human sets up Gmail API OAuth2 credentials and configures `.env`.

4. **Begin Phase A implementation**: Models and utilities (tests first per Constitution Principle V).

5. **Phase 3 forward-compatibility**: Ensure all vault output files are parseable by the Ralph Wiggum loop state machine. The `status: pending` field and vault directory routing are the critical interface points.

6. **MCP migration planning**: When Gmail MCP becomes operational (after HT-005), plan the refactor from `asyncio.to_thread(sdk_call)` to `await mcp_tool_call()` per ADR-0002's migration path.

---

## Appendix: Acceptance Criteria Traceability

| Spec Requirement | Plan Section | ADR | Task Phase |
|-----------------|--------------|-----|------------|
| FR-001 (BaseWatcher ABC) | ADR-0001, Source Code Layout | ADR-0001 | B |
| FR-002 (GmailWatcher extends BaseWatcher) | Implementation Order Phase C | ADR-0001 | C |
| FR-003 (Read unread emails) | Implementation Order Phase C | ADR-0002 | C |
| FR-004 (Keyword classification) | ADR-0004 | ADR-0004 | C |
| FR-005 (Markdown + YAML frontmatter) | YAML Frontmatter Contract | -- | C |
| FR-006 (Vault routing) | Vault Output Layout | -- | C |
| FR-007 (Duplicate prevention) | Storage, State File Schema | ADR-0003 | C |
| FR-008 (Retry with backoff) | ADR-0001, ADR-0002 | ADR-0001 | B |
| FR-009 (Structured logging) | Log Entry Schema | ADR-0003 | B |
| FR-010 (Configurable poll interval) | Technical Context, Performance Budget | -- | B |
| FR-011 (Token refresh) | Human Prerequisites HT-002 | -- | C |
| FR-012 (Unique filenames) | Filename Pattern | -- | C |
| FR-013 (Startup validation) | Human Prerequisites, Verification Plan | -- | C |
| FR-014 (File-based lock) | Storage, Source Code Layout | ADR-0001 | B |
| FR-015 (Ralph Wiggum compatible) | YAML Frontmatter Contract | -- | C |
| FR-016 (Independent failure) | Constitution Compliance (X) | ADR-0001 | B |
| FR-017 (Atomic file writes) | Storage | ADR-0003 | A |
