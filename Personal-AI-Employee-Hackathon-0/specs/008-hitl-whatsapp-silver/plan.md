# Implementation Plan: HITL + WhatsApp Silver Tier — Phase 5

**Branch**: `008-hitl-whatsapp-silver` | **Date**: 2026-03-02 | **Spec**: `specs/008-hitl-whatsapp-silver/spec.md`
**Input**: Build Privacy Gate, WhatsApp watcher, HITL approval workflow, WhatsApp MCP, Calendar MCP; wire orchestrator; integrate all Phase 5 components.

---

## Summary

Phase 5 adds the Human-in-the-Loop approval workflow and WhatsApp integration to the Personal AI Employee. Five new source files are created; two existing files are modified. The core loop: WhatsApp watcher ingests messages via Go bridge → orchestrator applies tiered classifier → Privacy Gate redacts sensitive content → HITL Manager writes draft to `vault/Pending_Approval/` → batch WhatsApp notification sent to owner → owner approves/rejects via WhatsApp reply → Gmail MCP sends approved email. Google Calendar MCP is wired in for scheduling context on MED-priority emails.

All existing Phase 4 infrastructure (MCPClient, Gmail MCP, Obsidian MCP, vault structure) is reused unchanged. The Privacy Gate is backported to Gmail watcher as a one-line retrofit.

---

## Technical Context

| Field | Value |
|-------|-------|
| Language/Version | Python 3.12 (consistent with existing codebase) |
| Primary Dependencies | `mcp>=1.0.0`, `pydantic>=2.0`, `google-api-python-client`, `google-auth-oauthlib`, `httpx>=0.27` (new), `pyyaml`, `python-dotenv`, `anyio` |
| Storage | Vault filesystem; `vault/Logs/` for HITL + privacy audit; no new database |
| Testing | `pytest`, `pytest-asyncio`, `unittest.mock`; no live API calls in tests |
| Target Platform | Linux/WSL2 local stdio + Go bridge at `:8080` |
| Project Type | Single project (adds to existing repo structure) |
| Performance Goals | WhatsApp ingestion ≤30s; HITL notification ≤2min; approved email sent ≤60s |
| Constraints | No breaking changes to Phase 2-4 code or tests; all secrets in `.env`; Privacy Gate mandatory before any vault write or LLM call |
| Scale/Scope | 2 new MCP servers (2 + 3 tools); 3 new source modules; 2 modified modules; ~50 new tests |

---

## Constitution Check

*GATE: Must pass before Phase A implementation. All principles verified.*

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I — Spec-First | spec.md v2.0 complete; clarifications resolved; all FRs covered | ✅ PASS |
| II — Local-First | vault/ is local; MCPs run locally via stdio; Go bridge is local `:8080`; no cloud dependency for core logic | ✅ PASS |
| III — HITL | Email send blocked until owner WhatsApp "approve" reply; `vault/Pending_Approval/` is the mandatory gate; `reversible: false` on all drafts | ✅ PASS |
| IV — MCP-First | WhatsApp send → WhatsApp MCP; Calendar data → Calendar MCP; Gmail send → Gmail MCP; direct API calls forbidden | ✅ PASS |
| V — Vault-Centric | All state in vault/: Pending_Approval/, Approved/, Rejected/, Logs/hitl_decisions.jsonl, Logs/privacy_gate.jsonl | ✅ PASS |
| VI — Watcher Architecture | WhatsApp watcher inherits BaseWatcher ABC; implements poll(), process_item(), validate_prerequisites() | ✅ PASS |
| VII — Phase-Gated | Entry criteria E1-E6 enforced; Phase 4 must be complete before any Phase 5 code is written | ✅ PASS |
| VIII — Error Taxonomy | ADR-0008 error codes (`auth_required`, `send_failed`, `mcp_unavailable`, etc.) used across all new MCP servers | ✅ PASS |
| IX — Security | OWNER_WHATSAPP_NUMBER in .env; Privacy Gate mandatory; audit logs in vault/Logs/; no secrets in code | ✅ PASS |
| X — Graceful Degradation | Calendar MCP unavailable → draft with warning note; WhatsApp bridge down → retry with backoff + log; fallback paths defined | ✅ PASS |

**ALL GATES PASS** — cleared to proceed to Phase A implementation.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-hitl-whatsapp-silver/
├── plan.md              ← This file
├── spec.md              ← Feature requirements (41 FRs, 10 SCs, 4 user stories)
├── research.md          ← Phase 0 output: 8 key decisions
├── data-model.md        ← Phase 1 output: all Pydantic models + state machines
├── quickstart.md        ← Phase 1 output: setup, test, troubleshoot guide
├── contracts/
│   ├── whatsapp-tools.json    ← Phase 1 output: 2 tool schemas
│   └── calendar-tools.json   ← Phase 1 output: 3 tool schemas
├── checklists/
│   └── requirements.md       ← Spec quality checklist (all PASS)
└── tasks.md             ← Phase 2 output (/sp.tasks — NOT created by /sp.plan)
```

### Source Code (repository root)

```text
watchers/
├── privacy_gate.py              ← NEW: shared utility; pure functions; Layer 0 for all watchers
├── whatsapp_watcher.py          ← NEW: WhatsApp message ingestion; inherits BaseWatcher
├── gmail_watcher.py             ← MODIFIED: one-line Privacy Gate retrofit (import + call)
└── base_watcher.py              ← UNCHANGED: ABC pattern reused by WhatsApp watcher

mcp_servers/
├── whatsapp/
│   ├── __init__.py              ← NEW
│   ├── server.py                ← NEW: FastMCP entry point; stdio transport; 2 tools
│   ├── bridge.py                ← NEW: Go bridge HTTP client (httpx); pywa fallback stub
│   └── models.py                ← NEW: Pydantic I/O models for send_message, health_check
└── calendar/
    ├── __init__.py              ← NEW
    ├── server.py                ← NEW: FastMCP entry point; stdio transport; 3 tools
    ├── auth.py                  ← NEW: Calendar OAuth2 (adapted from Gmail MCP auth.py pattern)
    └── models.py                ← NEW: Pydantic I/O models for list_events, check_availability, health_check

orchestrator/
├── hitl_manager.py              ← NEW: HITL lifecycle; submit_draft, batch_notify, handle_reply, timeouts
├── orchestrator.py              ← MODIFIED: tiered classifier + Calendar MCP + HITLManager wiring
└── mcp_client.py                ← UNCHANGED: reused as-is for WhatsApp + Calendar clients

scripts/
└── calendar_auth.py             ← NEW: one-time Google Calendar OAuth2 authorization (HT-011)

vault/
└── Rejected/
    └── .gitkeep                 ← NEW: created in T00 setup

tests/
├── unit/
│   ├── test_privacy_gate.py             ← NEW: 20+ cases (regex patterns, media block, edge cases)
│   ├── test_whatsapp_watcher.py         ← NEW: poll(), process_item(), deduplication
│   ├── test_hitl_manager.py             ← NEW: state machine, batch notification, timeout logic
│   └── test_orchestrator_hitl.py        ← NEW: tiered classifier + calendar wiring (mocked MCPClient)
├── contract/
│   ├── test_whatsapp_mcp_contracts.py   ← NEW: schema validation for 2 WhatsApp tools
│   └── test_calendar_mcp_contracts.py   ← NEW: schema validation for 3 Calendar tools
└── integration/
    ├── test_whatsapp_watcher_integration.py  ← NEW: full ingestion flow; mocked bridge; tmp vault
    ├── test_hitl_integration.py              ← NEW: full HITL cycle; mocked MCPClients; real vault
    └── test_calendar_mcp_integration.py      ← NEW: list_events, check_availability; mocked Google API

requirements.txt                 ← MODIFIED: add httpx>=0.27
.env                             ← MODIFIED: add WHATSAPP_* and CALENDAR_* and HITL_* vars
ai-control/HUMAN-TASKS.md        ← MODIFIED: update HT-011 progress; HT-012 remains DEFERRED
```

---

## Complexity Tracking

> No constitution violations. All additions are necessary.

| Addition | Why Needed | Simpler Alternative Rejected |
|---------|------------|------------------------------|
| `watchers/privacy_gate.py` (shared utility) | Shared between WhatsApp + Gmail watchers; pure function = independently testable; Layer 0 guarantee | Inline regex in each watcher duplicates code; harder to test; privacy invariant less visible |
| `orchestrator/hitl_manager.py` (new module) | HITL lifecycle is complex (state machine + timing + batch logic); SRP requires separation from orchestrator | Inline in orchestrator.py would make orchestrator.py unreadably long; state machine harder to test |
| `mcp_servers/whatsapp/bridge.py` (backend abstraction) | Go bridge and pywa have different interfaces; abstraction enables WHATSAPP_BACKEND env switch without conditionals in server.py | Inline conditionals in server.py tightly couple transport selection to tool logic |

---

## Implementation Phases

### Phase A: Setup + Privacy Gate

**Scope**: Create vault/Rejected/, write privacy_gate.py, retrofit Gmail watcher.

**Key design decisions**:
- Privacy Gate is a pure module (`privacy_gate.py`) with no imports from watchers or orchestrator — zero circular dependency risk.
- Gmail watcher retrofit: single import + single call in `process_item()` before `atomic_write`. No existing logic changes.
- `vault/Rejected/` created with `.gitkeep` so git tracks the directory.

**Files to create/modify**:
1. `vault/Rejected/.gitkeep` — empty, creates directory
2. `watchers/privacy_gate.py` — `run_privacy_gate()` pure function + `PrivacyGateResult` dataclass + `PrivacyLogEntry` dataclass
3. `watchers/gmail_watcher.py` — add `from watchers.privacy_gate import run_privacy_gate`; call in `process_item()` before vault write

**Tests to create**:
- `tests/unit/test_privacy_gate.py`:
  - 6-digit OTP patterns: `"otp is 123456"` → `"otp is [REDACTED-OTP]"`
  - Password pattern: `"password: myS3cr3t"` → `"password: [REDACTED-PASSWORD]"`
  - Card number: `"card: 4111111111111111"` → `"card: [REDACTED-CARD]"`
  - Media block: `media_type="image"` → `body="[MEDIA — content not stored]"`, `media_blocked=True`
  - Clean text: no redaction applied, `redaction_applied=False`
  - False positive case: 6-digit order number (acceptable — errs on side of privacy)
  - Alert message content: never contains original sensitive text

---

### Phase B: WhatsApp Watcher

**Scope**: Build `watchers/whatsapp_watcher.py` that ingests messages via Go bridge.

**Key design decisions**:
- Go bridge polling: `GET http://localhost:8080/messages?since=<last_message_id>` returns new messages as JSON array.
- Deduplication: check if `vault/Needs_Action/*-wa-<message_id>.md` already exists before writing (idempotent — FR-005).
- `process_item()` flow: Privacy Gate → dedup check → `atomic_write` → privacy log → privacy alert (if needed).
- `validate_prerequisites()`: checks `OWNER_WHATSAPP_NUMBER` env var set, Go bridge reachable.

**Files to create**:
1. `watchers/whatsapp_watcher.py` — `WhatsAppWatcher(BaseWatcher)` with `poll()`, `process_item()`, `validate_prerequisites()`

**Tests to create**:
- `tests/unit/test_whatsapp_watcher.py`:
  - `process_item()` writes to `vault/Needs_Action/` with correct filename
  - Deduplication: same message_id → no second file written
  - Privacy Gate called before vault write (verify via mock)
  - Media message: vault file contains `[MEDIA — content not stored]`
  - Privacy alert sent when redaction occurs (mocked WhatsApp MCP client)
- `tests/integration/test_whatsapp_watcher_integration.py`:
  - Full flow with mocked Go bridge response + `tmp_path` vault
  - Verify correct YAML frontmatter in written vault file
  - Verify atomic_write used (no partial files during test)

---

### Phase C: WhatsApp MCP Server

**Scope**: Build `mcp_servers/whatsapp/` FastMCP server with `send_message` and `health_check`.

**Key design decisions**:
- `bridge.py` provides `send_via_go_bridge(to, body)` using `httpx.post()` — no retry in MCP layer (MCPClient handles retries via `_retry_with_backoff`).
- Number normalization: `+923001234567` (E.164) → `923001234567@s.whatsapp.net` (WhatsApp JID) for Go bridge calls.
- `health_check()` calls `GET http://localhost:8080/health` with 3s timeout; returns `{"status": "healthy"}` on 200, `{"status": "down"}` on timeout/error.
- Error returned as `CallToolResult(isError=True)` per ADR-0008 — never raises exception.

**Files to create**:
1. `mcp_servers/whatsapp/__init__.py` — empty
2. `mcp_servers/whatsapp/models.py` — `SendMessageInput`, `SendMessageResult`, `HealthCheckResult`, `MCPError`
3. `mcp_servers/whatsapp/bridge.py` — `GoBridge.send(to, body)` using `httpx`; `PywaStub` for future fallback
4. `mcp_servers/whatsapp/server.py` — `FastMCP("whatsapp")` + `@mcp.tool()` registrations + `async def main()` → `stdio`

**Tests to create**:
- `tests/contract/test_whatsapp_mcp_contracts.py`:
  - `send_message` output matches `whatsapp-tools.json` outputSchema
  - Error format matches `errorFormat` schema (isError=True + JSON body)
  - `health_check` responds within 3s
- `tests/integration/test_whatsapp_mcp_integration.py`:
  - `send_message` with mocked `httpx.post` → verify correct request body
  - `send_message` bridge failure → verify `send_failed` error returned
  - `health_check` with mocked bridge → verify `healthy` status

---

### Phase D: HITL Manager

**Scope**: Build `orchestrator/hitl_manager.py` — the heart of the Phase 5 HITL workflow.

**Key design decisions**:
- `submit_draft()` generates `draft_id = YYYYMMDD-HHMMSS-<8-hex>`, writes to `vault/Pending_Approval/`, adds to `_pending_notification_queue`, schedules batch notification after `HITL_BATCH_DELAY_SECONDS`.
- `send_batch_notification()`: compose batch message from queue (max 5); call WhatsApp MCP `send_message`; update `notified_at` in each draft frontmatter; clear queue.
- `handle_owner_reply()`: regex parse `^(approve|reject)\s+([0-9a-f\-]+)$` (case-insensitive). Invalid → clarification message. Valid → dispatch to `_approve()` or `_reject()`.
- `_approve()`: call Gmail MCP `send_email`; move file from `vault/Pending_Approval/` to `vault/Approved/`; write to `vault/Logs/hitl_decisions.jsonl`; send WhatsApp confirmation.
- `_reject()`: move file to `vault/Rejected/`; write decision log; send WhatsApp confirmation. No Gmail call.
- `check_timeouts()`: scan `vault/Pending_Approval/` on every poll cycle; update status field in frontmatter.

**Files to create**:
1. `orchestrator/hitl_manager.py` — `HITLManager` class with all 5 public methods + internal dispatch methods

**Tests to create**:
- `tests/unit/test_hitl_manager.py`:
  - `submit_draft()` → verify file created in `vault/Pending_Approval/` with correct frontmatter
  - `send_batch_notification()` → verify WhatsApp MCP called with correct batch message format
  - `handle_owner_reply("approve a1b2c3d4", owner)` → verify Gmail MCP called; file moved to Approved/
  - `handle_owner_reply("reject a1b2c3d4", owner)` → verify Gmail MCP NOT called; file moved to Rejected/
  - `handle_owner_reply("ok", owner)` → verify clarification message sent; no irreversible action
  - `check_timeouts()` 24h → status = awaiting_reminder; reminder sent
  - `check_timeouts()` 48h → status = timed_out; no email sent
  - Concurrent 3 drafts: approve draft 2 → only draft 2 moved; drafts 1 and 3 unaffected
- `tests/integration/test_hitl_integration.py`:
  - Full cycle: submit_draft → batch notification sent → owner "approve" → Gmail MCP called → file in Approved/
  - Full cycle: submit_draft → owner "reject" → Gmail MCP NOT called → file in Rejected/

---

### Phase E: Calendar MCP Server

**Scope**: Build `mcp_servers/calendar/` FastMCP server with `list_events`, `check_availability`, `health_check`.

**Key design decisions**:
- `auth.py` adapts `mcp_servers/gmail/auth.py` pattern exactly — same token refresh flow, same `build()` call, different service name (`calendar`, `v3`) and scope (`calendar.readonly`).
- `list_events()`: calls `service.events().list(calendarId="primary", ...)` with `singleEvents=True, orderBy="startTime"`.
- `check_availability()`: internally calls `list_events()` for the slot window; checks any event overlaps `(event.start < slot_end AND event.end > slot_start)`.
- If `time_max` not provided, defaults to `time_min + 7 days`.
- `health_check()`: calls `service.calendarList().get(calendarId="primary")` with 3s timeout.

**Files to create**:
1. `mcp_servers/calendar/__init__.py` — empty
2. `mcp_servers/calendar/models.py` — `ListEventsInput`, `CheckAvailabilityInput`, `CalendarEvent`, `EventList`, `AvailabilityResult`, `HealthCheckResult`, `MCPError`
3. `mcp_servers/calendar/auth.py` — `get_calendar_service()` using `CALENDAR_CREDENTIALS_PATH` + `CALENDAR_TOKEN_PATH`
4. `mcp_servers/calendar/server.py` — `FastMCP("calendar")` + 3 tool registrations + `async def main()`
5. `scripts/calendar_auth.py` — one-time OAuth2 flow to generate `calendar_token.json` (completes HT-011)

**Tests to create**:
- `tests/contract/test_calendar_mcp_contracts.py`:
  - `list_events` output matches `calendar-tools.json` outputSchema
  - `check_availability` returns `is_available=True` for empty window
  - `health_check` returns `auth_required` when token file missing
- `tests/integration/test_calendar_mcp_integration.py`:
  - `list_events` with mocked `build()` → verify `service.events().list()` called with correct params
  - `check_availability` slot with conflict → verify `is_available=False` and event in `conflicting_events`
  - Token refresh path: mock expired token → verify refresh called before API call

---

### Phase F: Orchestrator Integration

**Scope**: Wire Calendar MCP + HITLManager into `RalphWiggumOrchestrator`; implement tiered classifier.

**Key design decisions**:
- Tiered classifier implemented as private method `_classify_priority(subject, body)` → `PriorityClassification`.
- Layer 1 check first (fastest); if SKIP, return immediately — no LLM call.
- Layer 2 keyword check; if MED, set `trigger_calendar=True` for downstream Calendar MCP call.
- Layer 3 LLM call only for AMBIGUOUS; uses existing `self.provider` (Claude).
- Calendar context fetching: before drafting, if `trigger_calendar=True`, call `self.calendar_client.call_tool("list_events", {...})` with 7-day window. Catch `MCPUnavailableError` → set `calendar_context.error = "mcp_unavailable"`.
- HITL submission: after draft generated, call `self.hitl_manager.submit_draft(...)` instead of writing directly to vault/Drafts/.
- Owner WhatsApp reply routing: WhatsApp watcher detects sender == `OWNER_WHATSAPP_NUMBER` → routes message body to `self.hitl_manager.handle_owner_reply()` instead of writing to `vault/Needs_Action/`.

**Files to modify**:
1. `orchestrator/orchestrator.py`:
   - `__init__()`: add `self.whatsapp_client`, `self.calendar_client`, `self.hitl_manager`
   - `_run_poll_cycle()`: add `await self.hitl_manager.check_timeouts()`; add owner-reply routing
   - New method `_classify_priority(subject, body) → PriorityClassification`
   - New method `_fetch_calendar_context(time_min, time_max) → CalendarContext`
   - Modify `_process_email()`: tiered classifier → calendar fetch → draft → HITL submit

**Tests to create/modify**:
- `tests/unit/test_orchestrator_hitl.py`:
  - `_classify_priority()`: Layer 1 spam detected → priority=SKIP; no LLM call
  - `_classify_priority()`: Layer 2 "urgent" → priority=HIGH; no LLM call
  - `_classify_priority()`: Layer 2 "meeting" → priority=MED; trigger_calendar=True
  - `_classify_priority()`: no keywords → Layer 3 LLM called
  - `_fetch_calendar_context()`: MCPClient success → CalendarContext with events
  - `_fetch_calendar_context()`: MCPClient unavailable → CalendarContext with error field
  - `_process_email()` end-to-end: inbox email → classified → calendar fetched → draft submitted to HITL

---

### Phase G: MCP Registry Update

**Scope**: Register WhatsApp MCP and Calendar MCP in `ai-control/MCP.md`.

**Files to modify**:
1. `ai-control/MCP.md` — add `whatsapp_mcp` and `calendar_mcp` entries
2. `ai-control/HUMAN-TASKS.md` — update HT-011 status to DONE after calendar_auth.py created + run

---

### Phase H: Housekeeping + Exit Gate

**Scope**: Declare new dependency, update env template, update HUMAN-TASKS, run full QA gate.

**Files to modify**:
1. `requirements.txt` — add `httpx>=0.27`
2. `.env.example` (if exists) — add Phase 5 vars
3. `ai-control/HUMAN-TASKS.md` — HT-011 DONE; HT-012 remains DEFERRED

**QA gate** (must pass before Phase 5 marked complete):
- `pytest tests/ --tb=short` → all pass
- `pytest tests/ --cov --cov-fail-under=80` → ≥80% coverage
- Manual: send test WhatsApp message → verify vault file created ≤30s
- Manual: trigger draft → verify batch notification received ≤2min
- Manual: send "approve <draft_id>" → verify email sent ≤60s

---

## Risk Analysis

| Risk | Blast Radius | Mitigation |
|------|-------------|-----------|
| Go bridge unavailable during HITL test | WhatsApp MCP `send_message` fails; owner never receives HITL notification | All tests mock Go bridge with `httpx_mock`; integration tests use `httpx.MockTransport`; real bridge required only for manual smoke tests |
| Privacy Gate false positive redacts legitimate content (e.g., 6-digit order number) | Owner sees `[REDACTED]` in vault; can't read original in Obsidian | By design — errs on privacy; owner can view original in WhatsApp app; acceptable false positive rate vs. zero sensitive-data leaks |
| Calendar OAuth token expired before HT-011 completed | Calendar MCP returns `auth_required`; orchestrator falls back to "⚠️ Calendar data unavailable" note | Graceful degradation explicit in FR-027; tests mock auth; `scripts/calendar_auth.py` makes re-auth trivial |
| `_classify_priority()` Layer 3 LLM cost | Every AMBIGUOUS email (~20-30%) consumes LLM tokens | Layers 1+2 handle majority at zero cost; Layer 3 only for genuine ambiguity; acceptable cost vs. accuracy tradeoff |
| HITLManager batch notification delayed > 2 minutes | SC-002 violated; owner not notified promptly | `HITL_BATCH_DELAY_SECONDS` is configurable; default 120s (2 min); monitor `vault/Logs/hitl_decisions.jsonl` for timing |
| Concurrent draft ID collision (same second, same 8-hex) | Two drafts with same ID → one overwrites the other | Collision probability ~1/65536 per second; HITLManager detects file exists and increments suffix before writing |
| Privacy Gate retrofit breaks Phase 2/3 tests | Gmail watcher tests fail with unexpected `[REDACTED]` in fixture emails | Fixture emails contain no sensitive patterns; if they do, assert `[REDACTED]` = correct test update. Zero regression risk. |

---

## Acceptance Criteria (from spec.md)

- [ ] SC-001: WhatsApp messages appear in `vault/Needs_Action/` within ≤30 seconds
- [ ] SC-002: HITL batch notification sent within ≤2 minutes of first draft write
- [ ] SC-003: Approved email sent within ≤60 seconds of owner approval reply
- [ ] SC-004: Approve/reject routed to correct draft — 100% accuracy with 3 concurrent drafts
- [ ] SC-005: Zero emails sent without explicit "approve" reply (invariant test)
- [ ] SC-006: Calendar context in ≥95% of scheduling-keyword drafts when Calendar MCP available
- [ ] SC-007: Zero partial vault files observable during concurrent writes
- [ ] SC-008: Full recovery after 60-second Go bridge connectivity drop
- [ ] SC-009: Sensitive text (password/OTP/PIN) NEVER written to vault or sent to LLM — always `[REDACTED]`
- [ ] SC-010: Media content NEVER stored, processed by LLM, or forwarded

---

## Related Artifacts

| Artifact | Path |
|---------|------|
| Feature spec | `specs/008-hitl-whatsapp-silver/spec.md` |
| Research findings | `specs/008-hitl-whatsapp-silver/research.md` |
| Data model | `specs/008-hitl-whatsapp-silver/data-model.md` |
| WhatsApp tool contracts | `specs/008-hitl-whatsapp-silver/contracts/whatsapp-tools.json` |
| Calendar tool contracts | `specs/008-hitl-whatsapp-silver/contracts/calendar-tools.json` |
| Quickstart | `specs/008-hitl-whatsapp-silver/quickstart.md` |
| Spec checklist | `specs/008-hitl-whatsapp-silver/checklists/requirements.md` |
| Task list (next step) | `specs/008-hitl-whatsapp-silver/tasks.md` (created by `/sp.tasks`) |
| Constitution | `.specify/memory/constitution.md` |
| MCP registry | `ai-control/MCP.md` |
| Human tasks | `ai-control/HUMAN-TASKS.md` (HT-011/HT-012) |
| Phase 4 MCPClient | `orchestrator/mcp_client.py` (reused as-is) |
| BaseWatcher | `watchers/base_watcher.py` (inherited by WhatsApp watcher) |

---

*Governed by: `ai-control/AGENTS.md` | `ai-control/LOOP.md` | `ai-control/MCP.md` | `ai-control/SWARM.md`*
*Version: 1.0.0 | Date: 2026-03-02*
