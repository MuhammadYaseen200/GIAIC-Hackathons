# Research: HITL + WhatsApp Silver Tier — Phase 5

**Branch**: `008-hitl-whatsapp-silver` | **Date**: 2026-03-02
**Phase**: 0 — Research & Design Decisions

---

## Decision 1: WhatsApp Backend Selection

**Decision**: Go bridge at `:8080` as primary; pywa Cloud API as secondary fallback.

**Rationale**:
- HT-004 is DONE — WhatsApp Web session authenticated as `XXXXXXXXXXXX:4@s.whatsapp.net`; Go bridge running and tested.
- No Meta Developer account, webhook hosting, or phone number registration needed for Go bridge.
- pywa requires: Business API account, verified phone number, Meta review, ngrok/VPS for webhook — all blocked by HT-012.
- Go bridge exposes a REST API at `:8080` that wraps the WhatsApp Web protocol; the MCP server sends HTTP POST to `http://localhost:8080/send`.

**Alternatives considered**:
- **pywa (Cloud API)**: Best for production (Meta-supported, stable), but blocked by HT-012 and Meta approval process.
- **whatsapp-web.js (Node)**: JavaScript; inconsistent with Python stack; session management complexity.
- **Signal**: Different protocol; user doesn't want to change messaging apps.

**Implementation**: `WHATSAPP_BACKEND=go_bridge` (default). WhatsApp MCP detects this env var and sends via `httpx.post("http://localhost:8080/send", json={"to": number, "body": text})`. If `WHATSAPP_BACKEND=pywa`, uses pywa's `wa.send_message()` instead.

**Go bridge send endpoint** (from HT-004 testing):
```
POST http://localhost:8080/send
Content-Type: application/json
{"to": "923xxxxxxxxx@s.whatsapp.net", "body": "message text"}
Response: {"id": "msg_id", "status": "sent"}
```

---

## Decision 2: HITL State Machine Design

**Decision**: File-system state machine using `vault/Pending_Approval/` YAML frontmatter as state store.

**Rationale**:
- Consistent with existing Pattern: Phase 3/4 orchestrator uses vault as message bus (Constitution Principle V).
- No additional database dependency (Neon is Phase 6+).
- YAML frontmatter is human-readable — owner can inspect state in Obsidian.
- Atomic file moves between directories implement state transitions safely.

**State transitions**:
```
PENDING:           vault/Pending_Approval/<draft_id>.md  [status: pending]
  → APPROVED:      vault/Approved/<draft_id>.md          [status: approved]
  → REJECTED:      vault/Rejected/<draft_id>.md          [status: rejected]
  → TIMED_OUT:     vault/Pending_Approval/<draft_id>.md  [status: timed_out]
  → AWAITING_REMINDER: vault/Pending_Approval/<draft_id>.md [status: awaiting_reminder]
```

**Draft ID format**: `<YYYYMMDD-HHMMSS>-<8-char-hex>` (e.g., `20260302-143022-a1b2c3d4`).
- Collision probability: 1/4^8 = 1/65536 per second. Negligible.
- If collision detected (file exists), increment last hex digit.

**HITL Manager polling**:
- `HITLManager` runs as a coroutine inside the main `RalphWiggumOrchestrator._run_poll_cycle()`.
- Polls `vault/Pending_Approval/` every 60 seconds for new drafts.
- Parses owner WhatsApp reply to extract command + draft ID.
- Dispatch: `approve <draft_id>` → Gmail MCP send → move to `vault/Approved/`.
- Timeout check: runs on every poll cycle; marks drafts older than 24h as `awaiting_reminder`, 48h as `timed_out`.

---

## Decision 3: Privacy Gate Architecture

**Decision**: Shared utility module `watchers/privacy_gate.py` — pure functions, zero side effects, called as Layer 0 in `process_item()`.

**Rationale**:
- Shared between WhatsApp watcher (new) and Gmail watcher (retrofit) without duplication.
- Pure functions (no I/O, no state) make the gate independently unit-testable.
- Layer 0 position (before vault write AND before LLM call) guarantees nothing sensitive ever reaches disk or AI.

**Sensitive text regex patterns**:
```python
SENSITIVE_PATTERNS = [
    (r'\b(password|passwd|pwd|pass)\s*[:=]\s*\S+', "[REDACTED-PASSWORD]"),
    (r'\b(pin)\s*[:=]?\s*\d{4,6}\b', "[REDACTED-PIN]"),
    (r'\b(otp|one.?time.?password|verification.?code)\s*[:=]?\s*\d{4,8}\b', "[REDACTED-OTP]"),
    (r'\b\d{6}\b', "[REDACTED-OTP]"),           # 6-digit standalone numbers (common OTP format)
    (r'\b\d{13,19}\b', "[REDACTED-CARD]"),       # Card numbers (13-19 digits)
    (r'\b(cvv|cvc)\s*[:=]?\s*\d{3,4}\b', "[REDACTED-CVV]"),
    (r'\b(secret|token|api.?key|private.?key)\s*[:=]\s*\S+', "[REDACTED-SECRET]"),
]
```

**Media block**: Unconditional — if `media_type != "text"`, the body field is set to `"[MEDIA — content not stored]"` regardless of caption content. Caption still passes through sensitive-text filter.

**Privacy alert**: Sent via WhatsApp MCP `send_message()` to `OWNER_WHATSAPP_NUMBER`. Contains NO portion of original content — only sender name/number and redaction flag.

**Logging**: `vault/Logs/privacy_gate.jsonl` — `{message_id, sender_number, redaction_applied, media_blocked, timestamp}`.

---

## Decision 4: Batch HITL Notification Design

**Decision**: Single batch WhatsApp message covering all pending unnotified drafts (max 5), sent within 2 minutes of first new draft.

**Rationale**:
- Individual pings per draft create notification fatigue on busy days.
- Batch message gives complete picture in one glance; owner sees all pending work.
- 2-minute batch window reduces message count by ~80% on multi-email processing runs.
- Max 5 cap prevents overwhelming the owner; overflow held in memory queue.

**Batch message format**:
```
📋 3 drafts pending approval:

1. 🔴 [HIGH] a1b2c3d4 — boss@company.com — Re: Urgent: Deadline
2. 🟡 [MED] e5f6g7h8 — client@example.com — Re: Meeting Next Week
3. 🟢 [LOW] i9j0k1l2 — newsletter@service.com — Re: Your inquiry

Reply: approve a1b2c3d4 / reject e5f6g7h8
(Use first 8 chars of draft ID)
```

**Polling / batching logic**:
- `HITLManager` maintains `_pending_notification_queue: list[DraftID]`.
- On new draft: add to queue; schedule batch send after `HITL_BATCH_DELAY_SECONDS` (default: 120).
- If already scheduled, update queue (add new entry); updated batch sent at scheduled time.
- After batch send: clear queue; update `notified_at` frontmatter in each draft file.

---

## Decision 5: Tiered Email Priority Classifier

**Decision**: Three-layer classifier in `orchestrator/orchestrator.py` before drafting.

**Rationale**:
- Token cost: Layer 1+2 handle ~70-80% of emails at zero LLM cost.
- Accuracy: Layer 3 LLM classification is accurate for the ~20-30% genuinely ambiguous emails.
- Priority tag directly drives the batch notification emoji (🔴/🟡/🟢).

**Layer 1 — Spam/Auto-reply filter (zero tokens)**:
```python
SKIP_DRAFTING_PATTERNS = [
    r'noreply@', r'no-reply@', r'donotreply@',
    r'unsubscribe', r'newsletter', r'automated response',
    r'out of office', r'auto-reply', r'vacation notice',
    r'delivery status notification', r'mailer-daemon',
]
```
If matched → `priority = "SKIP"` → no draft created; email archived directly.

**Layer 2 — Keyword heuristic (zero tokens)**:
```python
HIGH_KEYWORDS = ['urgent', 'asap', 'deadline', 'overdue', 'immediate', 'critical', 'emergency']
MED_KEYWORDS = ['meeting', 'schedule', 'availability', 'call', 'appointment', 'calendar', 'reschedule']
```
If HIGH keyword matched → `priority = "HIGH"`.
If MED keyword matched → `priority = "MED"` AND trigger Calendar MCP query.
Neither → `priority = "AMBIGUOUS"` → Layer 3.

**Layer 3 — LLM classification (AMBIGUOUS emails only)**:
- Single Claude API call with email subject + body snippet (≤500 chars).
- Prompt: `"Classify this email as HIGH (urgent/important business action needed), MED (moderate importance, can wait 24h), or LOW (FYI/informational only). Reply with exactly: HIGH, MED, or LOW."`
- Returns: `priority = "HIGH" | "MED" | "LOW"`.
- Token estimate: ~150-200 tokens per ambiguous email.

---

## Decision 6: Calendar MCP Integration

**Decision**: Read-only Google Calendar MCP with `calendar.readonly` scope; 7-day default look-ahead window.

**Rationale**:
- HT-011 IN_PROGRESS: `calendar.readonly` scope added to existing OAuth consent screen.
- Same `credentials.json` file works for both Gmail and Calendar (same Google Cloud project).
- Only `calendar_token.json` needs to be generated separately (run `scripts/calendar_auth.py`).
- Read-only scope is minimal privilege — satisfies Constitution Principle IX.
- 7-day window covers "this week + next week" — the most common scheduling horizon.

**Google Calendar API pattern** (same as Gmail OAuth2):
```python
service = build("calendar", "v3", credentials=creds)
events = service.events().list(
    calendarId="primary",
    timeMin=time_min.isoformat() + "Z",
    timeMax=time_max.isoformat() + "Z",
    maxResults=max_results,
    singleEvents=True,
    orderBy="startTime",
).execute()
```

**Trigger**: Layer 2 keyword heuristic sets `priority = "MED"` → orchestrator calls `calendar_mcp.call_tool("list_events", {...})` before drafting.

**Fallback**: `MCPClient.call_tool("list_events", ..., fallback=None)` — Calendar MCP unavailable → `MCPUnavailableError` caught → draft created with "⚠️ Calendar data unavailable" note.

---

## Decision 7: vault/Rejected/ Directory

**Decision**: Create `vault/Rejected/` in Phase 5 setup task T00 before any HITL tests.

**Rationale**:
- Does not exist currently (confirmed by directory audit).
- Required by FR-017 (rejected draft archival).
- Must be created with `vault/Rejected/.gitkeep` to persist in version control (empty dirs aren't tracked by git).

---

## Decision 8: Orchestrator Wiring Architecture

**Decision**: Add Calendar MCPClient + HITLManager as attributes of `RalphWiggumOrchestrator`; initialize in `__init__`; call in `_run_poll_cycle()`.

**Rationale**:
- Minimal change to existing orchestrator — only `__init__` and `_run_poll_cycle()` need modification.
- All existing watchers and loops remain unchanged.
- MCPClient pattern (ADR-0009) already established for Gmail + Obsidian; Calendar MCP follows same pattern.

**New MCPClient instances in orchestrator**:
```python
self.whatsapp_client = MCPClient(
    "whatsapp",
    ["python3", str(PROJECT_ROOT / "mcp_servers/whatsapp/server.py")],
    vault_path,
)
self.calendar_client = MCPClient(
    "calendar",
    ["python3", str(PROJECT_ROOT / "mcp_servers/calendar/server.py")],
    vault_path,
)
self.hitl_manager = HITLManager(
    whatsapp_client=self.whatsapp_client,
    gmail_client=self.gmail_client,  # existing
    vault_path=vault_path,
)
```

---

## Packages & Versions

| Package | Version | Purpose |
|---------|---------|---------|
| `mcp` | `>=1.0.0` | FastMCP + stdio transport (already installed) |
| `pydantic` | `>=2.0` | Input/output models (already installed) |
| `google-api-python-client` | `>=2.0` | Calendar API (already installed for Gmail) |
| `google-auth-oauthlib` | `>=1.0` | Calendar OAuth2 (already installed for Gmail) |
| `httpx` | `>=0.27` | Go bridge REST calls from WhatsApp MCP |
| `pyyaml` | `>=6.0` | Vault YAML frontmatter (already installed) |
| `pytest` | `>=8.0` | Testing (already installed) |
| `pytest-asyncio` | `>=0.23` | Async test support (already installed) |

**New dependency**: `httpx>=0.27` for the Go bridge HTTP client in `mcp_servers/whatsapp/server.py`.

---

*Research complete. All NEEDS CLARIFICATION items resolved. Proceed to Phase 1: data-model.md + contracts/ + quickstart.md.*
