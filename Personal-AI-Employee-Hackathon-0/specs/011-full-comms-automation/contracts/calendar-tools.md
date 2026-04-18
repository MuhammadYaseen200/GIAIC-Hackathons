# MCP Tool Contracts: Google Calendar (Phase 6.5 Extensions)

**MCP Server**: `mcp_servers/calendar/server.py`
**Date**: 2026-04-11

---

## New Tools

### `create_event`
```
Input:
  title: str
  start: str (ISO 8601 datetime with timezone)
  end: str (ISO 8601 datetime with timezone)
  attendees: list[str] | None  (email addresses)
  location: str | None
  description: str | None
  notify_attendees: bool (default: True)
Output:
  EventResult:
    event_id: str
    html_link: str
    created_at: str
Errors:
  ConflictDetected - overlapping event exists (must check_conflicts first)
  CalendarAuthError - missing write scope
Notes:
  MUST call check_conflicts() before calling create_event().
  CEO must confirm conflict resolution if ConflictDetected raised.
```

### `update_event`
```
Input:
  event_id: str
  title: str | None
  start: str | None
  end: str | None
  attendees: list[str] | None
  location: str | None
  description: str | None
  notify_attendees: bool (default: True)
Output:
  EventResult
Notes:
  Only provided fields are updated (partial update).
  Requires HITL if attendees present (sends updated invite).
```

### `delete_event`
```
Input:
  event_id: str
  notify_attendees: bool (default: True)
Output:
  deleted: bool
  event_title: str  (for confirmation display)
Notes:
  If notify_attendees=True and attendees exist, cancellation email sent by Google.
  Requires HITL approval before execution.
```

### `check_conflicts`
```
Input:
  start: str (ISO 8601)
  end: str (ISO 8601)
  calendar_id: str (default: "primary")
Output:
  ConflictCheck:
    has_conflict: bool
    conflicting_events: list[EventSummary]  (id, title, start, end)
Notes:
  Called automatically before every create_event call.
  Returns empty list if no conflicts (free slot).
```

### `create_focus_block`
```
Input:
  start: str (ISO 8601)
  end: str (ISO 8601)
  title: str (default: "Focus Time / Deep Work")
Output:
  EventResult
Notes:
  Status set to BUSY. Attendees list empty. No notifications.
  Still calls check_conflicts first.
```

### `extract_event_from_email`
```
Input:
  email_subject: str
  email_body_snippet: str  (max 500 chars — metadata only per FR-043 if using Tier 1)
  sender_email: str
Output:
  EventProposal:
    title: str | None
    proposed_start: str | None  (ISO 8601)
    proposed_end: str | None
    attendee_email: str | None  (sender's email)
    confidence: float
    raw_date_mentions: list[str]  (extracted date strings for CEO review)
Notes:
  Uses Tier 1 model (metadata only). Confidence < 0.7 = return raw_date_mentions only.
  CEO confirms EventProposal via HITL before create_event is called.
```
