# MCP Tool Contracts: WhatsApp (Phase 6.5 Extensions)

**MCP Server**: `mcp_servers/whatsapp/server.py`
**Date**: 2026-04-11

---

## New/Extended Tools

### `send_image`
```
Input:
  to: str (JID or contact name)
  path: str (local file path)
  caption: str | None
Output:
  message_id: str
  sent_at: str
Notes:
  ALL sends go through HITL queue first. Never called directly by orchestrator.
```

### `send_document`
```
Input:
  to: str
  path: str
  filename: str
Output:
  message_id: str
```

### `send_location`
```
Input:
  to: str
  latitude: float
  longitude: float
  name: str | None
Output:
  message_id: str
```

### `create_group`
```
Input:
  name: str
  members: list[str]  (JIDs or contact names, resolved via search_contacts)
  description: str | None
Output:
  group_id: str
  group_name: str
  member_count: int
Notes:
  Requires HITL approval before execution.
```

### `post_status`
```
Input:
  text: str | None
  media_path: str | None
  privacy: str (default: "contacts")  # contacts | everyone | nobody | contacts_except
Output:
  status_id: str
  posted_at: str
Notes:
  At least one of text or media_path required.
```

### `save_contact`
```
Input:
  name: str
  phone: str  (E.164 format)
  ceo_verified: bool (MUST be True — verification step completed before call)
Output:
  contact_id: str (ContactRecord.id)
  whatsapp_jid: str
Notes:
  ceo_verified=False raises ContactSaveNotVerified.
  CEO must confirm name/number before this is called.
```

### `get_unread_summary`
```
Input: none
Output:
  UnreadSummary:
    total_unread: int
    chats: list[ChatSummary]
      chat_id: str
      display_name: str
      unread_count: int
      last_message_preview: str  (max 50 chars, NO PII in logs)
      is_group: bool
      priority: str  (high | normal | low)
Notes:
  Priority determined by Tier 0 classifier (keyword urgency signals).
  display_name is contact name if saved, else "Unknown (***xxxx)" masked number.
```

### `broadcast`
```
Input:
  recipients: list[str]  (max 10, raises WhatsAppBanRiskError if exceeded)
  message: str
Output:
  sent_count: int
  failed_count: int
Errors:
  WhatsAppBanRiskError - raised if len(recipients) > 10 (FR-040)
```
