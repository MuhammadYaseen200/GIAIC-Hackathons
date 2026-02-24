# Data Model: MCP Integration — Phase 4

**Branch**: `007-mcp-integration` | **Date**: 2026-02-24

---

## Entities

### 1. Gmail MCP — Input Models

All live in `mcp-servers/gmail/models.py`.

#### `SendEmailInput`
```python
class SendEmailInput(BaseModel):
    to: str                           # recipient email address
    subject: str                      # email subject line
    body: str                         # plain-text or HTML body
    reply_to_message_id: str | None = None  # thread reply; uses In-Reply-To header
```

#### `ListEmailsInput`
```python
class ListEmailsInput(BaseModel):
    query: str = "is:unread"          # Gmail search query (same syntax as Gmail UI)
    max_results: int = 10             # 1–100; Gmail API enforces upper bound
```

#### `GetEmailInput`
```python
class GetEmailInput(BaseModel):
    message_id: str                   # Gmail message ID (from list_emails)
```

#### `MoveEmailInput`
```python
class MoveEmailInput(BaseModel):
    message_id: str                   # Gmail message ID
    destination_label: str            # Gmail label name, e.g. "INBOX", "DONE", custom label
```

#### `AddLabelInput`
```python
class AddLabelInput(BaseModel):
    message_id: str                   # Gmail message ID
    label_name: str                   # Label to apply, e.g. "AI_PROCESSED"
```

---

### 2. Gmail MCP — Output Models

#### `EmailSummary` (returned by `list_emails`)
```python
class EmailSummary(BaseModel):
    id: str                           # Gmail message ID
    subject: str                      # decoded subject header
    sender: str                       # From: header value
    date: str                         # ISO8601 date string
    snippet: str                      # Gmail snippet (~100 chars)
```

#### `EmailFull` (returned by `get_email`)
```python
class EmailFull(BaseModel):
    id: str
    subject: str
    sender: str                       # From: header
    to: str                           # To: header
    date: str                         # ISO8601
    body: str                         # decoded plain-text body
    has_attachments: bool             # True if MIME multipart with attachments
    attachment_names: list[str]       # filenames only — no content download
```

#### `SendEmailResult` (returned by `send_email`)
```python
class SendEmailResult(BaseModel):
    message_id: str                   # sent Gmail message ID
    thread_id: str                    # Gmail thread ID
    sent_at: str                      # ISO8601 timestamp
```

#### `AuditLogEntry` (written before every `send_email`)
```python
class AuditLogEntry(BaseModel):
    event: str = "pre_send_audit"
    timestamp: str                    # ISO8601
    to: str
    subject: str
    body_preview: str                 # first 200 chars of body
    reply_to_message_id: str | None
    severity: str = "INFO"
```
Written as JSONL to `vault/Logs/gmail_mcp_{date}.jsonl` before the Gmail API call.

---

### 3. Obsidian MCP — Input Models

All live in `mcp-servers/obsidian/models.py`.

#### `ReadNoteInput`
```python
class ReadNoteInput(BaseModel):
    path: str                         # vault-relative path, e.g. "Needs_Action/email-001.md"
```

#### `WriteNoteInput`
```python
class WriteNoteInput(BaseModel):
    path: str                         # vault-relative path (created if not exists)
    frontmatter: dict                 # YAML key-value pairs
    body: str                         # markdown body content
```

#### `ListNotesInput`
```python
class ListNotesInput(BaseModel):
    directory: str                    # vault-relative directory, e.g. "Needs_Action"
    filter: str | None = None         # frontmatter filter, e.g. "status:pending"
```

Filter syntax: `"field:value"` — matches notes where frontmatter `field == value`.

#### `MoveNoteInput`
```python
class MoveNoteInput(BaseModel):
    source: str                       # vault-relative source path
    destination: str                  # vault-relative destination path
```

#### `SearchNotesInput`
```python
class SearchNotesInput(BaseModel):
    query: str                        # text to search for in note body or frontmatter values
```

---

### 4. Obsidian MCP — Output Models

#### `NoteContent` (returned by `read_note`, `write_note`)
```python
class NoteContent(BaseModel):
    path: str                         # vault-relative path (canonical)
    frontmatter: dict                 # parsed YAML frontmatter
    body: str                         # body text (after frontmatter block)
```

#### `NoteList` (returned by `list_notes`, `search_notes`)
```python
class NoteList(BaseModel):
    notes: list[NoteMatch]

class NoteMatch(BaseModel):
    path: str                         # vault-relative path
    snippet: str | None = None        # matched text context (search_notes only)
```

---

### 5. Shared Error Model

All errors across both servers use the same JSON structure, returned as
`CallToolResult(isError=True, content=[TextContent(type="text", text=json.dumps(error))])`.

```python
class MCPError(BaseModel):
    error: MCPErrorCode               # see Error Taxonomy below
    message: str                      # human-readable description
    details: dict | None = None       # optional structured context
```

#### Error Taxonomy

| `error` code | Trigger | HTTP analogy |
|-------------|---------|-------------|
| `auth_required` | OAuth token missing/expired; no refresh token | 401 |
| `not_found` | Email or note does not exist | 404 |
| `rate_limited` | Gmail API quota exceeded | 429 |
| `permission_denied` | Vault path outside `VAULT_PATH` root | 403 |
| `parse_error` | Corrupt YAML frontmatter | 422 |
| `send_failed` | Gmail API returned non-200 on send | 502 |
| `mcp_unavailable` | Orchestrator: MCP server not responding (fallback logged) | 503 |
| `internal_error` | Unexpected exception — generic catch | 500 |

```python
MCPErrorCode = Literal[
    "auth_required", "not_found", "rate_limited",
    "permission_denied", "parse_error", "send_failed",
    "mcp_unavailable", "internal_error",
]
```

---

### 6. Orchestrator — New/Modified Models

#### `MCPClient` (new, `orchestrator/mcp_client.py`)
```python
class MCPClient:
    """Wraps MCP tool calls with the fallback protocol from ai-control/MCP.md."""

    def __init__(self, server_name: str, command: list[str], vault_path: Path):
        self.server_name = server_name    # "gmail" or "obsidian"
        self.command = command            # e.g. ["python3", "mcp-servers/gmail/server.py"]
        self.vault_path = vault_path      # for fallback log writes

    async def call_tool(
        self,
        tool_name: str,
        arguments: dict,
        fallback: Callable | None = None,
    ) -> dict:
        """Call MCP tool. On failure: log error, execute fallback if provided."""
        ...
```

#### `ApprovedDraft` (new concept, read from `vault/Approved/`)
```python
class ApprovedDraft(BaseModel):
    filepath: Path                    # absolute path to the draft .md file
    to: str                           # recipient (from frontmatter)
    subject: str                      # subject (from frontmatter)
    body: str                         # reply body (from note body)
    reply_to_message_id: str | None   # original Gmail message ID (from frontmatter)
```

---

## State Transitions

### Email Processing State Machine

```
Gmail Inbox
    │
    ▼
vault/Needs_Action/email.md   [status: pending]
    │
    ├─ LLM → draft_reply ──► vault/Drafts/reply.md [status: pending_approval]
    │                              │
    │                         Human approves
    │                              │
    │                         vault/Approved/reply.md [status: pending_approval]
    │                              │
    │                         Orchestrator polls vault/Approved/
    │                              │
    │                    Gmail MCP send_email ──► vault/Done/ [status: done]
    │                         (on failure: stays in vault/Approved/ for retry)
    │
    ├─ LLM → archive ──► vault/Done/email.md [status: done]
    ├─ LLM → needs_info ──► vault/Needs_Action/email.md [status: needs_info]
    ├─ LLM → urgent ──► vault/Drafts/reply.md [status: pending_approval, priority: urgent]
    └─ LLM → delegate ──► vault/Needs_Action/email.md [status: pending_approval]
                              (delegation note appended to body)
```

### Vault Note State (Obsidian MCP)

```
write_note(path, frontmatter, body) → NoteContent
    │
read_note(path) → NoteContent  (round-trips correctly)
    │
list_notes(directory, filter) → NoteList
    │
move_note(source, destination) → {"moved": true}
    │
(note no longer at source path)
```

---

## Vault Directory Structure (Phase 4)

```text
vault/
├── Needs_Action/      ← pending emails (existing)
├── Drafts/            ← AI-generated draft replies (existing)
├── Approved/          ← NEW: human-approved drafts awaiting send
├── Done/              ← processed emails (existing)
└── Logs/
    ├── gmail_mcp_2026-02-24.jsonl   ← pre-send audit log (NEW)
    └── orchestrator_state.json      ← existing watcher state
```
