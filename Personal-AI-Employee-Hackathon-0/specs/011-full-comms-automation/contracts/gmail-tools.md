# MCP Tool Contracts: Gmail (Phase 6.5 Extensions)

**MCP Server**: `mcp_servers/gmail/server.py`
**Date**: 2026-04-11

---

## New Tools (Phase 6.5 additions to existing server)

### `create_draft`
```
Input:
  to: str (email address)
  subject: str
  body: str
  reply_to_id: str | None  (Gmail message ID to reply to)
Output:
  draft_id: str
  created_at: str (ISO 8601)
Errors:
  GmailAuthError - OAuth token invalid or missing write scope
  GmailAPIError - API call failed
```

### `send_draft`
```
Input:
  draft_id: str
Output:
  message_id: str
  sent_at: str
Errors:
  GmailDraftNotFound - draft_id does not exist
  GmailAuthError
  HITL_REQUIRED - cannot call without prior HITL approval in CommunicationAction
```

### `label_emails`
```
Input:
  message_ids: list[str]
  add_labels: list[str]   (label names to add)
  remove_labels: list[str] | None  (label names to remove)
Output:
  labeled_count: int
  failed_ids: list[str]
```

### `trash_emails`
```
Input:
  message_ids: list[str]
Output:
  trashed_count: int
  failed_ids: list[str]
Notes:
  Moves to Trash only. Never permanent delete.
  CEO must empty Trash manually or after explicit second confirmation.
```

### `classify_inbox`
```
Input:
  max_emails: int (default 100, max 500)
  since_date: str | None (ISO 8601, default: last 7 days)
Output:
  ClassificationReport:
    total_classified: int
    categories:
      urgent: int
      opportunity: int
      promotional: int
      spam: int
      otc: int        (one-time codes)
      routine: int
    auto_replied: int
    sensitive_attachments: int
    labels_applied: int
    duration_seconds: float
```

### `get_attachment_flags`
```
Input:
  message_id: str
Output:
  AttachmentFlags:
    has_otp: bool
    has_password: bool
    has_legal_doc: bool
    has_suspicious_link: bool
    has_pii_media: bool
    flag_reason: str | None
```

### `send_auto_reply`
```
Input:
  message_id: str
  template_key: str  (key from auto_reply_templates.yaml)
Output:
  sent_message_id: str
  template_used: str
Notes:
  Only callable for emails with EmailClassification.is_auto_reply_candidate = TRUE
  Raises AutoReplyNotAllowed otherwise
```

### `get_daily_summary`
```
Input:
  date: str | None (ISO 8601 date, default: today)
Output:
  InboxSummary (see data-model.md)
```
