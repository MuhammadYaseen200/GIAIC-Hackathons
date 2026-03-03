# Data Model: HITL + WhatsApp Silver Tier — Phase 5

**Branch**: `008-hitl-whatsapp-silver` | **Date**: 2026-03-02

---

## 1. Privacy Gate — `watchers/privacy_gate.py`

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PrivacyGateResult:
    body: str                      # redacted body (original never stored)
    caption: str | None            # redacted caption (for media messages)
    redaction_applied: bool        # True if any sensitive text was replaced
    media_blocked: bool            # True if message_type != "text"
    alert_message: str | None      # WhatsApp alert text (None if no redaction)

# Pure function — no I/O, testable in isolation
def run_privacy_gate(
    body: str,
    media_type: str,               # "text" | "image" | "audio" | "video" | "document"
    caption: str | None = None,
) -> PrivacyGateResult:
    """Apply Privacy Gate: media block + sensitive text redaction.

    Called as Layer 0 in process_item() before any vault write or LLM call.
    Returns PrivacyGateResult with redacted content. Original text discarded.
    """
    ...

@dataclass
class PrivacyLogEntry:
    message_id: str
    sender_number: str
    redaction_applied: bool
    media_blocked: bool
    timestamp: str                 # ISO 8601
    # NO original content logged — only presence flags
```

---

## 2. WhatsApp Watcher — `watchers/whatsapp_watcher.py`

All live in `watchers/whatsapp_watcher.py`. Inherits `BaseWatcher`.

```python
from watchers.base_watcher import BaseWatcher
from watchers.privacy_gate import run_privacy_gate, PrivacyLogEntry

class WhatsAppWatcher(BaseWatcher):
    """Monitors WhatsApp incoming messages via Go bridge or pywa.

    WHATSAPP_BACKEND=go_bridge → polls GET http://localhost:8080/messages
    WHATSAPP_BACKEND=pywa → uses @wa.on_message webhook handler
    """

    def poll(self) -> list[RawWhatsAppMessage]:
        """Fetch new incoming messages from backend."""
        ...

    def process_item(self, item: RawWhatsAppMessage) -> Path:
        """Apply Privacy Gate → deduplicate → atomic_write to vault/Needs_Action/."""
        ...

    def validate_prerequisites(self) -> None:
        """Check OWNER_WHATSAPP_NUMBER set; backend reachable."""
        ...
```

### Input Models (internal)

```python
@dataclass
class RawWhatsAppMessage:
    """Raw message from Go bridge REST response or pywa webhook event."""
    message_id: str                # WhatsApp message ID (for deduplication)
    sender_number: str             # E.164 format (e.g., "923001234567")
    sender_name: str | None        # Contact display name if available
    body: str                      # Message text (pre-privacy-gate)
    media_type: str                # "text" | "image" | "audio" | "video" | "document"
    caption: str | None            # Media caption (pre-privacy-gate)
    received_at: str               # ISO 8601 timestamp
```

### Vault Note Schema (written to `vault/Needs_Action/`)

Filename: `<YYYYMMDD-HHMMSS>-wa-<message_id>.md`

```yaml
---
type: whatsapp_message
message_id: "3EB0C767D61B84A12345"
sender_number: "923001234567"
sender_name: "Ahmed Khan"          # or null if unknown
received_at: "2026-03-02T14:30:22Z"
media_type: "text"
source: "known"                    # "known" | "unknown"
status: "needs_action"
privacy_redacted: false            # true if Privacy Gate redacted anything
---

# WhatsApp Message

**From**: Ahmed Khan (923001234567)
**Received**: 2026-03-02 14:30:22 UTC

[MEDIA — content not stored]       # for media messages
OR
Message body here (redacted if sensitive content detected)
```

---

## 3. WhatsApp MCP — `mcp_servers/whatsapp/`

All models live in `mcp_servers/whatsapp/models.py`.

### Input Models

```python
class SendMessageInput(BaseModel):
    to: str                        # E.164 phone number (e.g., "+923001234567")
    body: str                      # Text message content (max 4096 chars)

class HealthCheckInput(BaseModel):
    pass                           # No parameters required
```

### Output Models

```python
class SendMessageResult(BaseModel):
    message_id: str                # Sent message ID from backend
    status: str                    # "sent" | "queued"
    sent_at: str                   # ISO 8601 timestamp

class HealthCheckResult(BaseModel):
    status: str                    # "healthy" | "degraded" | "down"
    connected_number: str | None   # E.164 number if connected
    backend: str                   # "go_bridge" | "pywa"
    bridge_url: str | None         # Go bridge URL if applicable
```

### Shared Error Model (same as Phase 4 pattern)

```python
class MCPError(BaseModel):
    error: MCPErrorCode
    message: str
    details: dict | None = None

MCPErrorCode = Literal[
    "auth_required", "not_found", "rate_limited",
    "permission_denied", "parse_error", "send_failed",
    "mcp_unavailable", "internal_error",
]
```

---

## 4. HITL Manager — `orchestrator/hitl_manager.py`

```python
from pydantic import BaseModel

class PendingDraft(BaseModel):
    """Loaded from vault/Pending_Approval/<draft_id>.md frontmatter."""
    draft_id: str                  # e.g., "20260302-143022-a1b2c3d4"
    reply_type: str                # "email" | "whatsapp"
    recipient: str                 # email address or WhatsApp number
    subject: str                   # Email subject (or WhatsApp context)
    body_preview: str              # First 500 chars of draft body
    status: str                    # "pending" | "awaiting_reminder" | "timed_out"
    created_at: str                # ISO 8601
    risk_level: str                # "low" | "medium" | "high"
    reversible: bool               # always False for email send
    priority: str                  # "HIGH" | "MED" | "LOW" (from tiered classifier)
    notified_at: str | None        # ISO 8601; None if batch not yet sent
    filepath: Path                 # absolute path to the draft .md file

class HITLDecision(BaseModel):
    """Written to vault/Logs/hitl_decisions.jsonl after each decision."""
    draft_id: str
    decision: str                  # "approve" | "reject" | "timeout"
    decided_at: str                # ISO 8601
    decided_by: str                # owner WhatsApp number
    sent_at: str | None            # ISO 8601; only if decision == "approve"
    gmail_message_id: str | None   # returned by Gmail MCP on send

class HITLManager:
    """Manages the HITL approval lifecycle.

    Responsibilities:
    - poll(): Write draft to vault/Pending_Approval/; enqueue for batch notification
    - send_batch_notification(): Send single WhatsApp message listing all pending drafts
    - handle_owner_reply(): Parse "approve/reject <draft_id>"; dispatch accordingly
    - check_timeouts(): Scan for drafts past 24h (reminder) or 48h (timeout)
    """

    def __init__(
        self,
        whatsapp_client: MCPClient,
        gmail_client: MCPClient,
        vault_path: Path,
        owner_number: str,
        batch_delay_seconds: int = 120,
        reminder_hours: int = 24,
        timeout_hours: int = 48,
        max_concurrent_drafts: int = 5,
    ) -> None: ...

    async def submit_draft(
        self,
        recipient: str,
        subject: str,
        body: str,
        reply_type: str,
        priority: str,
        risk_level: str,
        reply_to_message_id: str | None = None,
    ) -> str:
        """Write draft to vault/Pending_Approval/; return draft_id."""
        ...

    async def send_batch_notification(self) -> None:
        """Compose and send batch WhatsApp summary to owner."""
        ...

    async def handle_owner_reply(self, message_body: str, sender_number: str) -> None:
        """Parse approve/reject command and dispatch to _approve() or _reject()."""
        ...

    async def check_timeouts(self) -> None:
        """Mark drafts as awaiting_reminder or timed_out per configured thresholds."""
        ...
```

### Pending_Approval Vault Note Schema

Filename: `<YYYYMMDD-HHMMSS>-<draft_id>.md`
Located in: `vault/Pending_Approval/`

```yaml
---
type: approval_request
draft_id: "20260302-143022-a1b2c3d4"
action: send_email
reply_type: email
recipient: "boss@company.com"
subject: "Re: Urgent: Q1 Deadline"
status: pending
created_at: "2026-03-02T14:30:22Z"
decided_at: null
risk_level: high
reversible: false
priority: HIGH
notified_at: null
---

# Pending Approval: Re: Urgent: Q1 Deadline

**To**: boss@company.com
**Draft ID**: 20260302-143022-a1b2c3d4
**Priority**: 🔴 HIGH
**Risk**: HIGH | Reversible: NO

## Draft Body

[Full draft text here — owner can read in Obsidian for full context]

---
*Reply via WhatsApp: `approve 20260302-143022-a1b2c3d4` or `reject 20260302-143022-a1b2c3d4`*
```

---

## 5. Calendar MCP — `mcp_servers/calendar/`

All models live in `mcp_servers/calendar/models.py`.

### Input Models

```python
class ListEventsInput(BaseModel):
    time_min: str                  # ISO 8601 datetime string
    time_max: str                  # ISO 8601 datetime string
    max_results: int = 10          # 1–250; Calendar API upper bound

class CheckAvailabilityInput(BaseModel):
    time_slot_start: str           # ISO 8601 datetime string
    time_slot_end: str             # ISO 8601 datetime string

class HealthCheckInput(BaseModel):
    pass
```

### Output Models

```python
class CalendarEvent(BaseModel):
    event_id: str
    summary: str                   # Event title
    start: str                     # ISO 8601
    end: str                       # ISO 8601
    attendees: list[str]           # list of email addresses
    location: str | None

class EventList(BaseModel):
    events: list[CalendarEvent]
    calendar_id: str               # "primary" or email
    fetched_at: str                # ISO 8601 timestamp

class AvailabilityResult(BaseModel):
    is_available: bool
    conflicting_events: list[CalendarEvent]  # events that overlap the slot
    suggested_alternatives: list[str] | None  # suggested free slots (future feature)

class HealthCheckResult(BaseModel):
    status: str                    # "healthy" | "degraded" | "down"
    calendar_id: str               # "primary" or email
    email: str                     # Google account email
```

---

## 6. Orchestrator — New / Modified Models

### Tiered Priority Classifier Result

```python
@dataclass
class PriorityClassification:
    priority: str                  # "SKIP" | "HIGH" | "MED" | "LOW" | "AMBIGUOUS"
    layer_used: int                # 1 (spam filter), 2 (keyword), 3 (LLM)
    trigger_calendar: bool         # True if MED from Layer 2 (keyword: meeting/schedule)
    reasoning: str | None          # Only populated for Layer 3 LLM output
```

### CalendarContext (passed to draft generation)

```python
@dataclass
class CalendarContext:
    query_time_min: str            # ISO 8601
    query_time_max: str            # ISO 8601
    events: list[CalendarEvent]
    has_conflicts: bool
    fetched_at: str                # ISO 8601
    error: str | None              # ADR-0008 error code if fetch failed
```

---

## 7. State Transitions

### HITL Draft State Machine

```
[Orchestrator produces draft reply]
         │
         ▼
vault/Pending_Approval/<draft_id>.md   [status: pending]
         │
         ├─── HITLManager batch notification sent ──────────► [notified_at: set]
         │
         │  Owner replies "approve <draft_id>"
         ├──────────────────────────────────────────────────► vault/Approved/<draft_id>.md
         │                                                      [status: approved]
         │                                                      Gmail MCP send_email()
         │                                                      vault/Logs/hitl_decisions.jsonl
         │
         │  Owner replies "reject <draft_id>"
         ├──────────────────────────────────────────────────► vault/Rejected/<draft_id>.md
         │                                                      [status: rejected]
         │                                                      WhatsApp confirmation sent
         │                                                      vault/Logs/hitl_decisions.jsonl
         │
         │  24 hours pass, no reply
         ├──────────────────────────────────────────────────► vault/Pending_Approval/<draft_id>.md
         │                                                      [status: awaiting_reminder]
         │                                                      Reminder notification sent
         │
         │  48 hours pass, still no reply
         └──────────────────────────────────────────────────► vault/Pending_Approval/<draft_id>.md
                                                               [status: timed_out]
                                                               NO email sent
```

### WhatsApp Message Processing State Machine

```
Go bridge (:8080) / pywa webhook
         │
         ▼
RawWhatsAppMessage
         │
         ▼ (Layer 0: MANDATORY)
Privacy Gate
  ├── media_type != "text" → body = "[MEDIA — content not stored]"; media_blocked = True
  └── sensitive text regex → replace with [REDACTED]; redaction_applied = True
         │
         ▼
Deduplication (check vault/Needs_Action/ for existing message_id)
  ├── duplicate found → SKIP (idempotent)
  └── new message
         │
         ▼
atomic_write → vault/Needs_Action/<YYYYMMDD-HHMMSS>-wa-<message_id>.md
         │
         ▼
vault/Logs/privacy_gate.jsonl (append log entry)
         │
         ▼ (if redaction_applied or media_blocked)
WhatsApp MCP send_message() → Privacy alert to OWNER_WHATSAPP_NUMBER
```

### Email Priority Classification State Machine

```
Incoming email
         │
         ▼ Layer 1: Spam/Auto-reply filter
  ├── noreply/newsletter/auto-reply matched → priority = "SKIP" → archive directly
  └── passes
         │
         ▼ Layer 2: Keyword heuristic
  ├── HIGH keyword → priority = "HIGH" → skip to draft
  ├── MED keyword → priority = "MED" + trigger_calendar = True → call Calendar MCP → draft
  └── no keyword → priority = "AMBIGUOUS"
         │
         ▼ Layer 3: LLM classification (AMBIGUOUS only)
         └── Claude API call → priority = "HIGH" | "MED" | "LOW" → draft
```

---

## 8. Vault Directory Structure (Phase 5)

```text
vault/
├── Needs_Action/         ← existing + WhatsApp messages added
├── Pending_Approval/     ← existing + HITL drafts
├── Approved/             ← existing + approved drafts moved here
├── Rejected/             ← NEW (created in T00 setup)
│   └── .gitkeep
├── Drafts/               ← existing (AI draft staging)
├── Done/                 ← existing (processed emails)
└── Logs/
    ├── hitl_decisions.jsonl     ← NEW: HITL audit log
    ├── privacy_gate.jsonl       ← NEW: Privacy Gate log
    ├── gmail_mcp_<date>.jsonl   ← existing: pre-send audit
    └── mcp_fallback_<date>.jsonl ← existing: fallback log
```

---

*Data model complete. Proceed to contracts/ and quickstart.md.*
