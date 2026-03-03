# Tasks: HITL + WhatsApp Silver Tier — Phase 5

**Branch**: `008-hitl-whatsapp-silver` | **Date**: 2026-03-02
**Spec**: `specs/008-hitl-whatsapp-silver/spec.md`
**Plan**: `specs/008-hitl-whatsapp-silver/plan.md`
**Total Tasks**: 32

---

## Implementation Strategy

**Privacy Gate is foundational** — must complete before any watcher is written (Layer 0 of every `process_item()`).

**WhatsApp MCP is shared** — US1 needs it for privacy alerts; US2 needs it for HITL batch notifications. Built in US1's phase; US2 depends on it.

**MVP Scope**: Complete Phase 1–3 (T001–T015, Setup + Privacy Gate + User Story 1). This delivers WhatsApp message ingestion with privacy protection. Independently testable.

**Delivery Order**: Setup → Privacy Gate (Foundational) → US1 (WhatsApp Ingestion) → US2 (HITL Review) → US3 (Calendar Context) → Polish.

---

## Dependency Graph

```
T001 (vault/Rejected/)
    ↓
T002, T003, T004 [P] (requirements.txt, .env, __init__.py files)
    ↓
T005 (privacy_gate.py)  ←  T006 [P] (test_privacy_gate.py)
    ↓
T007 (gmail_watcher.py retrofit)
    ↓
T008 (regression check)
    ↓
T009, T010, T011 [P] (US1 test files)
T012, T013 [P]          (US1 model + bridge files)
    ↓
T014 (whatsapp MCP server.py) ← depends on T012, T013
    ↓
T015 (whatsapp_watcher.py) ← depends on T014 (needs WhatsApp MCP for privacy alerts)
    ↓
T016, T017, T018 [P] (US2 test files)
    ↓
T019 (hitl_manager.py) ← depends on T014 (WhatsApp MCP), existing Gmail MCP
    ↓
T020 (orchestrator.py HITL wiring) ← depends on T019
    ↓
T021, T022 [P]       (US3 test files)
T023, T024 [P]       (US3 model + auth files)
    ↓
T025 (calendar/server.py) ← depends on T023, T024
    ↓
T026 (scripts/calendar_auth.py) [P with T025]
    ↓
T027 (orchestrator.py Calendar wiring) ← depends on T025, T020
    ↓
T028, T029 [P] (MCP registry + HT updates)
T030–T032      (QA gate, smoke tests, spec status update)
```

---

## Phase 1: Setup

*Project initialization — no story label. Must complete before any Phase 5 implementation.*

- [ ] T001 Create `vault/Rejected/.gitkeep` (new vault directory required by FR-017/ADR-0011; does not yet exist per spec Assumptions)
- [ ] T002 [P] Add `httpx>=0.27` to `requirements.txt` under Phase 5 section (required for Go bridge REST client in mcp_servers/whatsapp/bridge.py)
- [ ] T003 [P] Add Phase 5 environment variables to `.env`: `WHATSAPP_BACKEND=go_bridge`, `WHATSAPP_BRIDGE_URL=http://localhost:8080`, `OWNER_WHATSAPP_NUMBER`, `CALENDAR_CREDENTIALS_PATH`, `CALENDAR_TOKEN_PATH`, `HITL_BATCH_DELAY_SECONDS=120`, `HITL_REMINDER_HOURS=24`, `HITL_TIMEOUT_HOURS=48`, `HITL_MAX_CONCURRENT_DRAFTS=5` (see quickstart.md Step 2)
- [ ] T004 [P] Create empty `mcp_servers/whatsapp/__init__.py` and `mcp_servers/calendar/__init__.py` (Python package markers; parallel write, different files)

**Checkpoint**: Setup complete — vault directory, dependency, env config, and package structure ready.

---

## Phase 2: Foundational — Privacy Gate

*Core pre-processing layer that MUST complete before any watcher is written or modified.*

**⚠️ CRITICAL**: No US1/US2/US3 watcher or MCP work can begin until this phase is complete — Privacy Gate is Layer 0 of every `process_item()` call.

- [ ] T005 Create `watchers/privacy_gate.py`: implement `run_privacy_gate(body: str, media_type: str, caption: str | None) → PrivacyGateResult`; define `PrivacyGateResult` and `PrivacyLogEntry` dataclasses; define `SENSITIVE_PATTERNS` list with regex patterns for passwords/PINs/OTPs (6-digit standalone codes)/card numbers (13-19 digits)/CVV/secrets/API keys; implement media absolute block (`media_type != "text"` → body = `"[MEDIA — content not stored]"`, `media_blocked = True`); compose `alert_message` when redaction occurs (contains NO original content); pure function with no I/O — zero side effects (spec FR-031–FR-034, ADR-0010, data-model.md Section 1, plan.md Phase A)
- [ ] T006 [P] Write `tests/unit/test_privacy_gate.py`: 12+ test cases covering — 6-digit OTP detection (`"otp: 123456"` → `"[REDACTED-OTP]"`); standalone 6-digit code (`"Your code: 847291"` → `"[REDACTED-OTP]"`); password pattern (`"password: myS3cr3t"` → `"[REDACTED-PASSWORD]"`); PIN pattern (`"pin: 4829"` → `"[REDACTED-PIN]"`); card number 16 digits → `"[REDACTED-CARD]"`; API key pattern; media block (media_type="image" → body replaced, media_blocked=True); media with caption (caption also privacy-gated); clean text (no redaction, redaction_applied=False, media_blocked=False); alert_message contains no original sensitive content; double redaction (both password + OTP in same message); verify function returns `PrivacyGateResult` dataclass (spec SC-009, SC-010, ADR-0010)
- [ ] T007 Retrofit `watchers/gmail_watcher.py`: add `from watchers.privacy_gate import run_privacy_gate, PrivacyLogEntry` import; in `process_item()` before `atomic_write`, call `result = run_privacy_gate(body=email_body, media_type="text")`; use `result.body` as the content written to vault; append `PrivacyLogEntry` to `vault/Logs/privacy_gate.jsonl` using `atomic_write`; one-line change to existing logic (spec: Privacy Gate scope extended to Gmail watcher; ADR-0010; plan.md Phase A)
- [ ] T008 Run existing Phase 2/3/4 regression: `pytest tests/ -v` — verify all existing tests pass with no changes after Privacy Gate retrofit; if any test fails due to fixture email containing sensitive pattern, update fixture to assert `[REDACTED]` (the correct behavior); zero new failures acceptable (quickstart.md Step 5)

**Checkpoint**: Privacy Gate complete — run `pytest tests/unit/test_privacy_gate.py` → all pass. Gmail watcher tests still pass. Foundation cleared.

---

## Phase 3: User Story 1 — WhatsApp Message Ingestion (Priority: P1) 🎯 MVP

**Goal**: WhatsApp messages received by the monitored number are automatically captured and Privacy-Gated into `vault/Needs_Action/` within 30 seconds.

**Independent Test**: Start Go bridge at `:8080`. Send a WhatsApp text message. Within 30 seconds, verify a `.md` file appears in `vault/Needs_Action/` with correct YAML frontmatter (`type: whatsapp_message`, `sender_number`, `received_at`, `media_type`, `status: needs_action`). Send an image — verify `body: "[MEDIA — content not stored]"`. Send duplicate — verify no second file.

### Tests for User Story 1 ⚠️ (Write FIRST; verify FAIL before T012)

- [ ] T009 [P] [US1] Write `tests/unit/test_whatsapp_watcher.py`: mock Go bridge HTTP responses; test `process_item()` writes correct filename format `<YYYYMMDD-HHMMSS>-wa-<message_id>.md` to `vault/Needs_Action/`; test deduplication (same message_id → no second file); test Privacy Gate called BEFORE vault write (verify via mock assertion); test media message → body = `"[MEDIA — content not stored]"`; test privacy alert sent when redaction_applied=True (mock WhatsApp MCP client); test `validate_prerequisites()` raises when OWNER_WHATSAPP_NUMBER missing (plan.md Phase B)
- [ ] T010 [P] [US1] Write `tests/contract/test_whatsapp_mcp_contracts.py`: load `specs/008-hitl-whatsapp-silver/contracts/whatsapp-tools.json`; validate `send_message` success output matches outputSchema (message_id, status, sent_at fields); validate error response has `isError=True` + JSON body matching errorFormat schema; validate `health_check` returns within 3s; validate error codes limited to defined `MCPErrorCode` Literal values (contracts/whatsapp-tools.json, ADR-0008, plan.md Phase C)
- [ ] T011 [P] [US1] Write `tests/integration/test_whatsapp_watcher_integration.py`: use `pytest tmp_path` fixture as vault root; mock Go bridge with `httpx.MockTransport` returning 2 messages then empty; run full ingestion cycle; verify 2 vault files created with correct YAML frontmatter; verify `privacy_gate.jsonl` log entries created; verify no partial files on disk during write (atomic_write guarantee) (spec SC-001, SC-007, plan.md Phase B)

### Implementation for User Story 1

- [ ] T012 [P] [US1] Create `mcp_servers/whatsapp/models.py`: `SendMessageInput(BaseModel)` with `to: str` + `body: str`; `SendMessageResult(BaseModel)` with `message_id: str`, `status: str`, `sent_at: str`; `HealthCheckResult(BaseModel)` with `status: str`, `connected_number: str | None`, `backend: str`, `bridge_url: str | None`; `MCPError(BaseModel)` with `error: MCPErrorCode`, `message: str`, `details: dict | None`; `MCPErrorCode = Literal["auth_required", "not_found", "rate_limited", "permission_denied", "parse_error", "send_failed", "mcp_unavailable", "internal_error"]` (data-model.md Section 3, ADR-0008, contracts/whatsapp-tools.json)
- [ ] T013 [P] [US1] Create `mcp_servers/whatsapp/bridge.py`: `GoBridge` class with `async send(to: str, body: str) → SendMessageResult`; number normalization `_to_jid(number: str)` strips `+`, appends `@s.whatsapp.net`; uses `httpx.AsyncClient(timeout=10.0).post(f"{BRIDGE_URL}/send", json={"to": jid, "body": body})`; raises `send_failed` MCPError on non-200; `async health() → HealthCheckResult` calls `GET {BRIDGE_URL}/health` with 3s timeout; `PywaStub` class as placeholder (all methods raise `NotImplementedError("pywa not yet implemented")`); reads `WHATSAPP_BRIDGE_URL` from env (research.md Decision 1, ADR-0012, plan.md Phase C)
- [ ] T014 [US1] Create `mcp_servers/whatsapp/server.py`: `mcp = FastMCP("whatsapp")`; reads `WHATSAPP_BACKEND` env var; instantiates `GoBridge` (go_bridge) or raises clear error (pywa); `@mcp.tool() async def send_message(to: str, body: str) → dict`: calls `GoBridge.send()`; on exception returns `CallToolResult(isError=True, content=[TextContent(text=json.dumps(MCPError(...).model_dump()))])`; `@mcp.tool() async def health_check() → dict`: calls `GoBridge.health()`; `if __name__ == "__main__": mcp.run()` for stdio transport (spec FR-007–FR-011, ADR-0005, ADR-0012, plan.md Phase C)
- [ ] T015 [US1] Create `watchers/whatsapp_watcher.py`: `WhatsAppWatcher(BaseWatcher)` inheriting all BaseWatcher lifecycle methods; `poll()`: calls `GET {BRIDGE_URL}/messages?since={self._last_message_id}` with httpx; returns list of `RawWhatsAppMessage` dataclasses; `process_item(item)`: (1) `result = run_privacy_gate(item.body, item.media_type, item.caption)` (2) check dedup: if `vault/Needs_Action/*-wa-{item.message_id}.md` exists → return (3) build vault note content with YAML frontmatter (type, message_id, sender_number, sender_name, received_at, media_type, source, status, privacy_redacted) (4) `atomic_write(vault_path / "Needs_Action" / filename, content)` (5) append to `vault/Logs/privacy_gate.jsonl` (6) if `result.redaction_applied or result.media_blocked`: send privacy alert via WhatsApp MCP `send_message(OWNER_WHATSAPP_NUMBER, result.alert_message)`; `validate_prerequisites()`: assert `OWNER_WHATSAPP_NUMBER` set; assert Go bridge reachable; `_retry_with_backoff(max_retries=5, base_delay=30.0)` on connectivity loss (spec FR-001–FR-006, FR-031–FR-039, ADR-0001, ADR-0010, data-model.md Section 2, plan.md Phase B)

**Checkpoint**: User Story 1 complete — run `pytest tests/unit/test_whatsapp_watcher.py tests/contract/test_whatsapp_mcp_contracts.py tests/integration/test_whatsapp_watcher_integration.py` → all pass. Manual smoke: Go bridge running → send WhatsApp message → file in `vault/Needs_Action/` within 30s (SC-001).

---

## Phase 4: User Story 2 — HITL Draft Review via WhatsApp (Priority: P1)

**Goal**: Orchestrator-drafted email replies wait in `vault/Pending_Approval/` until owner approves or rejects via WhatsApp. No email ever sent without explicit "approve" command.

**Depends on**: Phase 3 complete (WhatsApp MCP `send_message` required for batch notifications).

**Independent Test**: Manually call `hitl_manager.submit_draft(...)`. Verify `vault/Pending_Approval/<draft_id>.md` exists with correct YAML frontmatter. Verify within 2 minutes a WhatsApp message arrives on owner's phone listing the pending draft. Send "approve <draft_id>" via WhatsApp. Verify email sent via Gmail MCP. Verify file moved to `vault/Approved/`. Verify `vault/Logs/hitl_decisions.jsonl` has entry. Send "reject <draft_id2>" for second draft — verify Gmail NOT called; file in `vault/Rejected/`.

### Tests for User Story 2 ⚠️ (Write FIRST; verify FAIL before T019)

- [ ] T016 [P] [US2] Write `tests/unit/test_hitl_manager.py`: mock MCPClient (WhatsApp + Gmail); test `submit_draft()` creates file in `vault/Pending_Approval/` with correct YAML frontmatter (`type: approval_request`, `status: pending`, `risk_level`, `priority`, `reversible: false`, `notified_at: null`); test `send_batch_notification()` calls WhatsApp MCP `send_message` with batch format (🔴/🟡/🟢 emoji + draft_id + recipient + subject); test `handle_owner_reply("approve a1b2c3d4", owner)` → Gmail MCP `send_email` called + file moved to `vault/Approved/` + decision logged; test `handle_owner_reply("reject a1b2c3d4", owner)` → Gmail MCP NOT called + file moved to `vault/Rejected/`; test `handle_owner_reply("ok", owner)` → clarification sent, no irreversible action; test `check_timeouts()` at 24h → status = `awaiting_reminder` + reminder sent; test `check_timeouts()` at 48h → status = `timed_out` + no Gmail call; test 3 concurrent drafts: approve draft 2 only → drafts 1 and 3 unaffected; test draft ID collision detection (plan.md Phase D, spec FR-012–FR-020, ADR-0011)
- [ ] T017 [P] [US2] Write `tests/integration/test_hitl_integration.py`: use tmp_path vault; mock `MCPClient.call_tool` for both WhatsApp MCP and Gmail MCP; run full cycle: `submit_draft()` → `send_batch_notification()` → `handle_owner_reply("approve <id>")` → verify Gmail MCP `send_email` called with correct args + file in `vault/Approved/` + `hitl_decisions.jsonl` entry; run reject cycle: → verify Gmail NOT called + file in `vault/Rejected/`; run ambiguous reply → verify clarification sent, file still in `Pending_Approval/` (spec SC-002–SC-005, ADR-0011)
- [ ] T018 [P] [US2] Write `tests/unit/test_orchestrator_hitl.py`: mock MCPClient; test `_classify_priority(subject, body)` — Layer 1: `noreply@` sender → priority=`"SKIP"` + no LLM call; Layer 2: subject contains "urgent" → priority=`"HIGH"`, trigger_calendar=False, no LLM; Layer 2: body contains "meeting" → priority=`"MED"`, trigger_calendar=True, no LLM; Layer 3 path: no keywords → `_llm_classify()` called → priority from LLM response; test `_process_email()` end-to-end with mock email → HITL `submit_draft()` called (not direct vault write) (plan.md Phase F, spec FR-025)

### Implementation for User Story 2

- [ ] T019 [US2] Create `orchestrator/hitl_manager.py`: `HITLManager` class with `__init__(whatsapp_client, gmail_client, vault_path, owner_number, batch_delay_seconds=120, reminder_hours=24, timeout_hours=48, max_concurrent_drafts=5)`; `async submit_draft(recipient, subject, body, reply_type, priority, risk_level, reply_to_message_id) → str`: generate `draft_id` = `f"{now:%Y%m%d-%H%M%S}-{secrets.token_hex(4)}"`, check collision, build YAML frontmatter (type/action/draft_id/reply_type/recipient/subject/status:pending/created_at/risk_level/reversible:false/priority/notified_at:null), `atomic_write(vault_path/"Pending_Approval"/f"{draft_id}.md", content)`, add to `_pending_notification_queue`, schedule `send_batch_notification()` after `batch_delay_seconds`; `async send_batch_notification()`: pull up to 5 from queue, compose batch message with priority emojis, call `whatsapp_client.call_tool("send_message", {"to": owner_number, "body": batch_msg})`, update `notified_at` in each draft frontmatter; `async handle_owner_reply(message_body, sender_number)`: regex match `^(approve|reject)\s+([0-9a-f]{8}[\-0-9a-f]*)$` case-insensitive; valid → find draft file by ID prefix → dispatch to `_approve()` or `_reject()`; invalid/ambiguous → send clarification; `async _approve(draft)`: call `gmail_client.call_tool("send_email", {...})`; `atomic_write` move to `vault/Approved/`; append to `vault/Logs/hitl_decisions.jsonl`; send WhatsApp confirmation; `async _reject(draft)`: move to `vault/Rejected/`; append to `vault/Logs/hitl_decisions.jsonl`; send WhatsApp confirmation (no Gmail call); `async check_timeouts()`: scan `vault/Pending_Approval/*.md`; parse `created_at` from frontmatter; at 24h: update status=`awaiting_reminder`, send reminder; at 48h: update status=`timed_out` (spec FR-012–FR-020, FR-040–FR-041, ADR-0011, data-model.md Section 4)
- [ ] T020 [US2] Wire `orchestrator/orchestrator.py` for HITL: in `__init__()` add `self.whatsapp_client = MCPClient("whatsapp", ["python3", str(PROJECT_ROOT/"mcp_servers/whatsapp/server.py")], vault_path)` and `self.hitl_manager = HITLManager(whatsapp_client=self.whatsapp_client, gmail_client=self.gmail_client, vault_path=vault_path, owner_number=os.getenv("OWNER_WHATSAPP_NUMBER"))`; in `_run_poll_cycle()` add `await self.hitl_manager.check_timeouts()`; add owner-reply routing: when WhatsApp watcher event arrives from `OWNER_WHATSAPP_NUMBER`, route `message_body` to `await self.hitl_manager.handle_owner_reply(message_body, sender_number)` instead of writing to `vault/Needs_Action/`; replace any direct draft vault writes with `await self.hitl_manager.submit_draft(...)` (spec FR-028, ADR-0011, plan.md Phase F)

**Checkpoint**: User Story 2 complete — run `pytest tests/unit/test_hitl_manager.py tests/unit/test_orchestrator_hitl.py tests/integration/test_hitl_integration.py` → all pass. Manual: trigger draft → WhatsApp notification within 2min → "approve <id>" → email sent within 60s (SC-002, SC-003).

---

## Phase 5: User Story 3 — Google Calendar Context in Draft Replies (Priority: P2)

**Goal**: When the orchestrator drafts a reply to a scheduling-related email, it consults Google Calendar for the next 7 days and incorporates availability context into the draft. Graceful fallback if Calendar MCP is unavailable.

**Depends on**: Phase 2 (Privacy Gate). Calendar MCP is independent of WhatsApp Watcher and HITL Manager — can be developed in parallel with Phase 4 if team capacity allows.

**Independent Test**: Send an email with "are you available for a meeting next week?" Verify draft reply includes reference to calendar events (or "⚠️ Calendar data unavailable" if Calendar MCP token missing). `health_check()` returns `status: healthy` with valid `email` and `calendar_id` fields.

### Tests for User Story 3 ⚠️ (Write FIRST; verify FAIL before T023)

- [ ] T021 [P] [US3] Write `tests/contract/test_calendar_mcp_contracts.py`: load `specs/008-hitl-whatsapp-silver/contracts/calendar-tools.json`; verify `list_events` output matches outputSchema (events array, calendar_id, fetched_at); verify `list_events` returns empty events list (not error) when no events in window; verify `check_availability` returns `is_available: true` for empty slot; verify `check_availability` returns `is_available: false` + non-empty `conflicting_events` when event overlaps; verify `health_check` returns `auth_required` error when token file missing; verify all error responses have `isError=True` + JSON matching errorFormat; verify event overlap logic: `event.start < slot_end AND event.end > slot_start` (contracts/calendar-tools.json, ADR-0005, ADR-0008)
- [ ] T022 [P] [US3] Write `tests/integration/test_calendar_mcp_integration.py`: mock `google.oauth2.credentials.Credentials` + `googleapiclient.discovery.build()`; test `list_events` calls `service.events().list(calendarId="primary", singleEvents=True, orderBy="startTime")` with correct `timeMin`/`timeMax`; test `time_max` defaults to `time_min + 7 days` when not provided; test `check_availability` with one overlapping event returns `is_available: False`; test `check_availability` with no overlapping events returns `is_available: True`; test token refresh: mock expired `access_token` → verify `credentials.refresh()` called before API request (spec FR-021–FR-024, plan.md Phase E)

### Implementation for User Story 3

- [ ] T023 [P] [US3] Create `mcp_servers/calendar/models.py`: `ListEventsInput(BaseModel)` with `time_min: str`, `time_max: str | None = None`, `max_results: int = 10`; `CheckAvailabilityInput(BaseModel)` with `time_slot_start: str`, `time_slot_end: str`; `CalendarEvent(BaseModel)` with `event_id: str`, `summary: str`, `start: str`, `end: str`, `attendees: list[str]`, `location: str | None = None`; `EventList(BaseModel)` with `events: list[CalendarEvent]`, `calendar_id: str`, `fetched_at: str`; `AvailabilityResult(BaseModel)` with `is_available: bool`, `conflicting_events: list[CalendarEvent]`, `suggested_alternatives: list[str] | None = None`; `HealthCheckResult(BaseModel)` with `status: str`, `calendar_id: str`, `email: str`; shared `MCPError + MCPErrorCode` (same as WhatsApp MCP, or import from shared location) (data-model.md Section 5, contracts/calendar-tools.json, ADR-0008)
- [ ] T024 [P] [US3] Create `mcp_servers/calendar/auth.py`: `get_calendar_service()` function — reads `CALENDAR_CREDENTIALS_PATH` + `CALENDAR_TOKEN_PATH` from env; loads `Credentials` from token JSON; if expired and `refresh_token` present: call `credentials.refresh(Request())`; re-save refreshed token to `CALENDAR_TOKEN_PATH`; if missing: raises `MCPError(error="auth_required", message="calendar_token.json missing — run scripts/calendar_auth.py")`; returns `build("calendar", "v3", credentials=creds)`; follows exact same pattern as `mcp_servers/gmail/auth.py` (research.md Decision 6, ADR-0006, plan.md Phase E)
- [ ] T025 [US3] Create `mcp_servers/calendar/server.py`: `mcp = FastMCP("calendar")`; `@mcp.tool() async def list_events(time_min: str, time_max: str | None = None, max_results: int = 10) → dict`: call `get_calendar_service()`; if `time_max` is None set to `time_min + 7 days`; call `service.events().list(calendarId="primary", timeMin=time_min, timeMax=time_max, maxResults=max_results, singleEvents=True, orderBy="startTime").execute()`; parse results into `EventList`; on `auth_required` raise → return error; `@mcp.tool() async def check_availability(time_slot_start: str, time_slot_end: str) → dict`: call `list_events()` for the slot window; check overlap: `event.start < slot_end AND event.end > slot_start`; return `AvailabilityResult`; `@mcp.tool() async def health_check() → dict`: call `service.calendarList().get(calendarId="primary").execute()` with 3s timeout; return `HealthCheckResult`; `if __name__ == "__main__": mcp.run()` (spec FR-021–FR-024, ADR-0005, plan.md Phase E)
- [ ] T026 [US3] Create `scripts/calendar_auth.py`: one-time OAuth2 authorization script for HT-011 completion; `InstalledAppFlow.from_client_secrets_file(CALENDAR_CREDENTIALS_PATH, ["https://www.googleapis.com/auth/calendar.readonly"])`; `flow.run_local_server(port=0)`; serialize token to `calendar_token.json` at `CALENDAR_TOKEN_PATH`; print confirmation with token path; include `--help` usage; update `ai-control/HUMAN-TASKS.md` HT-011 instructions to say "run `python3 scripts/calendar_auth.py`" (quickstart.md Step 3, research.md Decision 6, HT-011)
- [ ] T027 [US3] Wire `orchestrator/orchestrator.py` for Calendar + tiered classifier: add `self.calendar_client = MCPClient("calendar", ["python3", str(PROJECT_ROOT/"mcp_servers/calendar/server.py")], vault_path)` in `__init__()`; implement `_classify_priority(subject: str, body: str) → PriorityClassification`: (1) Layer 1 spam regex scan on sender + subject → if match return `PriorityClassification(priority="SKIP", layer_used=1, trigger_calendar=False)`; (2) Layer 2 keyword scan — HIGH_KEYWORDS check → return HIGH; MED_KEYWORDS check → return MED + trigger_calendar=True; (3) Layer 3 LLM call via existing provider for AMBIGUOUS → return HIGH/MED/LOW with reasoning; implement `async _fetch_calendar_context(time_min, time_max) → CalendarContext`: call `self.calendar_client.call_tool("list_events", {...})`; on `MCPUnavailableError` → return `CalendarContext(error="mcp_unavailable", events=[])`; in `_process_email()`: run `_classify_priority()` first → if SKIP: archive directly; if HIGH: draft immediately; if MED: call `_fetch_calendar_context(now, now+7days)` then draft with context; draft submission routes through `self.hitl_manager.submit_draft(...)` (spec FR-025–FR-028, ADR-0013, plan.md Phase F)

**Checkpoint**: User Story 3 complete — run `pytest tests/contract/test_calendar_mcp_contracts.py tests/integration/test_calendar_mcp_integration.py` → all pass. Manual: Calendar MCP `health_check` returns healthy; send scheduling email → draft includes calendar context (SC-006).

---

## Phase 6: Polish & Cross-Cutting Concerns

*Finalization — MCP registry, human tasks, full QA gate, smoke test, spec status update.*

- [ ] T028 [P] Update `ai-control/MCP.md`: add `whatsapp_mcp` entry (server name: `whatsapp_mcp`, path: `mcp_servers/whatsapp/server.py`, command: `python3 mcp_servers/whatsapp/server.py`, tools: `send_message`/`health_check`, env: `WHATSAPP_BACKEND`/`WHATSAPP_BRIDGE_URL`/`OWNER_WHATSAPP_NUMBER`, fallback: `MCPUnavailableError` logged to `vault/Logs/`); add `calendar_mcp` entry (server name: `calendar_mcp`, path: `mcp_servers/calendar/server.py`, tools: `list_events`/`check_availability`/`health_check`, env: `CALENDAR_CREDENTIALS_PATH`/`CALENDAR_TOKEN_PATH`, fallback: orchestrator uses "⚠️ Calendar data unavailable" note) (spec MCP Servers table, plan.md Phase G, ADR-0012)
- [ ] T029 [P] Update `ai-control/HUMAN-TASKS.md`: mark HT-011 as `IN_PROGRESS` → `DONE` after `scripts/calendar_auth.py` is created and run; confirm HT-012 remains `DEFERRED` (Go bridge primary; pywa not yet configured); add note that `CALENDAR_TOKEN_PATH` token must be present before Calendar MCP live tests (spec Human Tasks table, plan.md Phase G, quickstart.md Step 3)
- [ ] T030 Run full Phase 5 test suite: `pytest tests/ -v --cov=mcp_servers --cov=watchers --cov=orchestrator --cov-report=term-missing`; verify ALL 32 test files pass; verify coverage ≥ 80% for `watchers/privacy_gate.py`, `watchers/whatsapp_watcher.py`, `mcp_servers/whatsapp/`, `mcp_servers/calendar/`, `orchestrator/hitl_manager.py`; fix any failures before proceeding (quickstart.md Step 8, SC-007, plan.md Phase H QA gate)
- [ ] T031 Manual smoke test per `quickstart.md` Steps 9–10: run `python3 -c "..."` snippet from quickstart.md to verify WhatsApp MCP `health_check` returns `status: healthy`; run Calendar MCP `list_events` snippet and verify events from next 7 days return correctly (quickstart.md Steps 9-10; validates SC-001 and SC-006 live)
- [ ] T032 Update `specs/008-hitl-whatsapp-silver/spec.md` header: change `**Status**: Draft` → `**Status**: Complete`; verify all Exit Criteria X1–X10 met in `spec.md` Exit Criteria table by checking against completed tasks and passing tests (spec Exit Criteria X1–X10, plan.md Acceptance Criteria checklist)

**Checkpoint**: Phase 5 complete — all 32 tasks done; full test suite passes; coverage ≥80%; smoke tests pass; spec.md status = Complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Privacy Gate)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1 WhatsApp Ingestion)**: Depends on Phase 2 — MVP deliverable
- **Phase 4 (US2 HITL Review)**: Depends on Phase 3 (WhatsApp MCP from US1 is required for HITL notifications)
- **Phase 5 (US3 Calendar)**: Depends on Phase 2; CAN run in parallel with Phase 4 (Calendar MCP independent of HITL Manager)
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5

### User Story Dependencies

- **US1 (P1 — WhatsApp Ingestion)**: Can start after Phase 2 complete. No dependency on US2 or US3.
- **US2 (P1 — HITL Review)**: Depends on US1 completion (needs WhatsApp MCP `send_message` for batch notifications).
- **US3 (P2 — Calendar Context)**: Can start after Phase 2 complete. Independent of US1 and US2 (Calendar MCP has no WhatsApp dependency).
- **US4 (P3 — WhatsApp Triage)**: DEFERRED — out of scope for Phase 5.

### Within Each User Story (required order)

```
Tests (FIRST — verify FAIL) → Models → Auth/Bridge → Server → Watcher/Manager → Orchestrator wiring
```

### Parallel Opportunities

- T002, T003, T004 can all run in parallel (different files)
- T006 (Privacy Gate tests) can run in parallel with T005 (Privacy Gate implementation), as long as the interface is agreed
- T009, T010, T011 (US1 tests) can all be written in parallel
- T012, T013 (WhatsApp MCP models + bridge) can be written in parallel
- T016, T017, T018 (US2 tests) can all be written in parallel
- T021, T022 (US3 tests) can be written in parallel
- T023, T024 (Calendar models + auth) can be written in parallel
- T025 (Calendar server) can run in parallel with T026 (calendar_auth.py) after T023+T024
- T028, T029 (MCP registry + HT update) can run in parallel

---

## Parallel Example: User Story 1

```bash
# Write all US1 tests together (before any implementation):
Task T009: tests/unit/test_whatsapp_watcher.py
Task T010: tests/contract/test_whatsapp_mcp_contracts.py
Task T011: tests/integration/test_whatsapp_watcher_integration.py

# Write US1 models + bridge together (after tests):
Task T012: mcp_servers/whatsapp/models.py
Task T013: mcp_servers/whatsapp/bridge.py

# Then sequentially:
Task T014: mcp_servers/whatsapp/server.py  (depends on T012, T013)
Task T015: watchers/whatsapp_watcher.py    (depends on T014)
```

## Parallel Example: User Story 3 (alongside US2)

```bash
# US2 and US3 tests can be written in parallel:
Task T016-T018: US2 test files (HITL Manager + Orchestrator HITL)
Task T021-T022: US3 test files (Calendar MCP contracts + integration)

# US3 models/auth in parallel:
Task T023: mcp_servers/calendar/models.py
Task T024: mcp_servers/calendar/auth.py

# Then US3 implementation:
Task T025: mcp_servers/calendar/server.py
Task T026: scripts/calendar_auth.py
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only — Silver Tier Core)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Privacy Gate (T005–T008) — **CRITICAL, blocks everything**
3. Complete Phase 3: US1 WhatsApp Ingestion (T009–T015)
4. **STOP and VALIDATE**: Send WhatsApp message → vault file in 30s; privacy gate logs correct
5. Complete Phase 4: US2 HITL Review (T016–T020)
6. **STOP and VALIDATE**: Full HITL cycle — draft → notification → approve → email sent

### Incremental Delivery

1. Setup + Privacy Gate → Foundation ready
2. Add US1 → Independently testable → WhatsApp ingestion working
3. Add US2 → HITL loop complete → Silver tier core delivered ✅
4. Add US3 → Calendar context → Email draft quality improved
5. Polish → Registry + QA → Phase 5 DONE

### Constitution Compliance Checkpoints

| Checkpoint | Principle | Gate |
|------------|-----------|------|
| After T008 | Privacy Gate active on Gmail watcher | pytest tests/ pass with zero regressions |
| After T015 | WhatsApp messages ingested with Privacy Gate | SC-009, SC-010 pass |
| After T020 | No email sent without "approve" | SC-005 invariant: zero unauthorized sends |
| After T027 | Calendar context in 95%+ scheduling drafts | SC-006 sampling test |
| After T030 | All Phase 5 tests pass at ≥80% coverage | QA gate cleared |

---

## Notes

- [P] tasks = different files, no dependencies on incomplete prior tasks — run in parallel
- [USN] label maps each task to its user story for traceability
- Privacy Gate (Phase 2) is the highest-priority foundational task — it is a non-negotiable religious and security requirement; never skip or defer
- Tests are REQUIRED (explicitly specified in plan.md Phase A–H); write each test phase BEFORE implementing that phase
- Each user story phase should be independently completable and testable before starting the next
- `vault/Rejected/` (T001) must be created before ANY HITL test can run
- `scripts/calendar_auth.py` (T026) must be run manually (HT-011) before Calendar MCP live tests work
- Stop at each checkpoint to validate story independently before proceeding
- Commit after each task or logical group (T001–T004 → commit "chore(phase-5): setup"; T005–T008 → "feat(privacy-gate): add shared privacy gate utility"; etc.)
