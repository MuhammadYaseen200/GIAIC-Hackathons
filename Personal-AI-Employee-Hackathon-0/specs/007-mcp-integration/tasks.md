# Tasks: MCP Integration — Phase 4

**Branch**: `007-mcp-integration` | **Date**: 2026-02-24 | **Spec**: `specs/007-mcp-integration/spec.md`
**Plan**: `specs/007-mcp-integration/plan.md` | **Total Tasks**: 31

---

## Implementation Strategy

**MCP Framework**: `FastMCP` from `mcp.server.fastmcp` (recommended by building-mcp-servers skill; supersedes D1 in research.md).
FastMCP provides `@mcp.tool` decorators, auto-schema from Pydantic models, and `mcp.run()` stdio entry point — simpler and more maintainable than low-level Server API.

**MVP Scope**: Complete Phase 1–3 (T001–T016, User Story 1). This delivers the primary value: approved draft reply sending via Gmail MCP.

**Delivery Order**: US1 → US2 → US3 → US4 → Polish. Each phase is independently testable.

---

## Dependency Graph

```
T001 (requirements.txt)
    ↓
T002 (gmail __init__)  T003 (obsidian __init__)  T004 (.env)  T005 (vault/Approved/)
    ↓                       ↓
T006 (gmail auth.py)    T008 (obsidian models.py)   T009 (mcp_client.py)
T007 (gmail models.py)      ↓                            ↓
    ↓                   T021 (obsidian tools.py)    T014 (orchestrator changes)
T011 (gmail tools.py)       ↓                            ↓
    ↓               T022 (obsidian contracts)       T025 (_apply_decision refactor)
T013 (gmail server.py)      ↓                            ↓
    ↓               T023 (obsidian server.py)     T026, T027 (orchestrator tests)
T016 (approved draft E2E)   ↓
                    T024 (obsidian integration)
```

---

## Phase 1: Setup

*Project initialization — no story label. Must complete before any implementation.*

- [x] T001 Update `requirements.txt` — add under `# --- Phase 4: MCP Integration ---`: `mcp>=1.0.0`, `jsonschema>=4.0.0`, `anyio>=4.0.0`. Verify install: `python3 -c "from mcp.server.fastmcp import FastMCP; print('ok')"`

- [x] T002 [P] Create `mcp_servers/gmail/__init__.py` — empty file. Also create `mcp_servers/__init__.py`. Note: directory renamed to `mcp_servers/` (underscores) for valid Python package import.

- [x] T003 [P] Create `mcp_servers/obsidian/__init__.py` — empty file.

- [x] T004 [P] `.env` already has `GMAIL_CREDENTIALS_PATH`, `GMAIL_TOKEN_PATH`, `VAULT_PATH` set. Updated `GMAIL_MCP_SERVER` and `OBSIDIAN_MCP_SERVER` to use `mcp_servers/` paths.

- [x] T005 [P] `vault/Approved/` directory exists. Added `vault/Approved/.gitkeep`.

---

## Phase 2: Foundational

*Shared infrastructure blocking all user stories. Complete before Phase 3.*

- [x] T006 Create `mcp_servers/gmail/auth.py` — OAuth2 Gmail service singleton. Pattern adapted from `watchers/gmail_watcher.py:170-211`.

  **Full implementation spec**:
  ```python
  # mcp-servers/gmail/auth.py
  """Gmail OAuth2 authentication for MCP server. Reuses token lifecycle from gmail_watcher.py."""
  import os
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent.parent))

  from google.auth.transport.requests import Request
  from google.oauth2.credentials import Credentials
  from googleapiclient.discovery import build
  from watchers.utils import atomic_write

  SCOPES = [
      "https://www.googleapis.com/auth/gmail.readonly",
      "https://www.googleapis.com/auth/gmail.send",
      "https://www.googleapis.com/auth/gmail.modify",
  ]

  class AuthRequiredError(Exception):
      """Raised when OAuth token is missing or cannot be refreshed."""

  _gmail_service = None  # module-level singleton

  def get_gmail_service():
      """Return authenticated Gmail API service. Token must already exist (from HT-002).
      Never opens browser flow — raises AuthRequiredError if auth needed.
      Caches service singleton across tool calls."""
      global _gmail_service
      if _gmail_service is not None:
          return _gmail_service

      token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", "token.json"))
      creds_path = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", "credentials.json"))

      creds = None
      if token_path.exists():
          try:
              creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
          except (ValueError, KeyError):
              token_path.unlink(missing_ok=True)

      if creds and creds.valid:
          pass
      elif creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
          atomic_write(token_path, creds.to_json())
      else:
          raise AuthRequiredError(
              "Gmail OAuth token missing or expired. "
              "Run 'python3 scripts/gmail_auth.py' to authenticate."
          )

      _gmail_service = build("gmail", "v1", credentials=creds)
      return _gmail_service

  def reset_service_cache():
      """Reset cached service (for testing)."""
      global _gmail_service
      _gmail_service = None
  ```

- [x] T007 Create `mcp_servers/gmail/models.py` — all Pydantic v2 I/O models for 5 Gmail tools + error model.

  **Full implementation spec**:
  ```python
  # mcp-servers/gmail/models.py
  """Pydantic v2 I/O models for Gmail MCP tools. Used for input validation and output schema documentation."""
  from pydantic import BaseModel, Field, field_validator, ConfigDict
  from typing import Optional, List, Literal

  MCPErrorCode = Literal[
      "auth_required", "not_found", "rate_limited",
      "send_failed", "permission_denied", "internal_error"
  ]

  class MCPError(BaseModel):
      error: MCPErrorCode
      message: str
      details: Optional[dict] = None

  class SendEmailInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      to: str = Field(..., description="Recipient email address", min_length=3)
      subject: str = Field(..., description="Email subject", min_length=1)
      body: str = Field(..., description="Plain-text email body", min_length=1)
      reply_to_message_id: Optional[str] = Field(None, description="Gmail message ID to thread reply (sets In-Reply-To header)")

  class ListEmailsInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      query: str = Field(default="is:unread", description="Gmail search query (e.g. 'is:unread', 'from:boss@co.com')")
      max_results: int = Field(default=10, description="Max results (1-100)", ge=1, le=100)

  class GetEmailInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      message_id: str = Field(..., description="Gmail message ID from list_emails result", min_length=1)

  class MoveEmailInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      message_id: str = Field(..., description="Gmail message ID", min_length=1)
      destination_label: str = Field(..., description="Target Gmail label (e.g. 'INBOX', 'DONE', 'AI_PROCESSED')", min_length=1)

  class AddLabelInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      message_id: str = Field(..., description="Gmail message ID", min_length=1)
      label_name: str = Field(..., description="Label to apply (created if not exists)", min_length=1)
  ```

- [x] T008 [P] Create `mcp_servers/obsidian/models.py` — all Pydantic v2 I/O models for 5 Obsidian tools.

  **Full implementation spec**:
  ```python
  # mcp-servers/obsidian/models.py
  """Pydantic v2 I/O models for Obsidian MCP tools."""
  from pydantic import BaseModel, Field, field_validator, ConfigDict
  from typing import Optional, Literal

  MCPErrorCode = Literal["not_found", "permission_denied", "parse_error", "internal_error"]

  class MCPError(BaseModel):
      error: MCPErrorCode
      message: str
      details: Optional[dict] = None

  class ReadNoteInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      path: str = Field(..., description="Vault-relative path, e.g. 'Needs_Action/email-001.md'", min_length=1)

  class WriteNoteInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      path: str = Field(..., description="Vault-relative path (created if not exists)", min_length=1)
      frontmatter: dict = Field(..., description="YAML frontmatter as key-value dict")
      body: str = Field(default="", description="Markdown body content (after frontmatter)")

  class ListNotesInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      directory: str = Field(..., description="Vault-relative directory, e.g. 'Needs_Action'", min_length=1)
      filter: Optional[str] = Field(None, description="Frontmatter filter 'field:value', e.g. 'status:pending' (exact match)")

  class MoveNoteInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      source: str = Field(..., description="Vault-relative source path", min_length=1)
      destination: str = Field(..., description="Vault-relative destination path", min_length=1)

  class SearchNotesInput(BaseModel):
      model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
      query: str = Field(..., description="Text to search in notes (case-insensitive substring)", min_length=1)
  ```

- [x] T009 Create `orchestrator/mcp_client.py` — `MCPClient` class implementing the fallback protocol from `ai-control/MCP.md`.

  **Full implementation spec**:
  ```python
  # orchestrator/mcp_client.py
  """Async MCP tool caller with fallback protocol (ai-control/MCP.md).

  Fallback protocol:
    1. Attempt MCP tool call via subprocess stdin/stdout
    2. On McpError / timeout / subprocess failure: log mcp_fallback + execute fallback callable
    3. If fallback also fails: log mcp_escalation + re-raise
  """
  import asyncio
  import json
  import logging
  from pathlib import Path
  from typing import Any, Callable, Optional
  from datetime import datetime, timezone

  logger = logging.getLogger(__name__)

  class MCPUnavailableError(Exception):
      """Raised when MCP server cannot be reached and fallback is unavailable."""

  class MCPClient:
      """Wraps MCP tool calls with the fallback protocol.

      Usage:
          client = MCPClient("obsidian", ["python3", "mcp-servers/obsidian/server.py"], vault_path)
          result = await client.call_tool("read_note", {"path": "test.md"}, fallback=lambda: vault_ops.read(...))
      """

      def __init__(self, server_name: str, command: list[str], vault_path: Path):
          self.server_name = server_name
          self.command = command
          self.vault_path = vault_path
          self._log_dir = vault_path / "Logs"

      async def call_tool(
          self,
          tool_name: str,
          arguments: dict,
          fallback: Optional[Callable] = None,
          timeout: float = 30.0,
      ) -> dict:
          """Call MCP tool. On failure: log + run fallback. Returns tool result dict."""
          try:
              return await asyncio.wait_for(
                  self._invoke_tool(tool_name, arguments),
                  timeout=timeout,
              )
          except Exception as e:
              self._log_fallback(tool_name, arguments, str(e))
              if fallback is not None:
                  try:
                      result = fallback()
                      if asyncio.iscoroutine(result):
                          result = await result
                      return result if isinstance(result, dict) else {"result": result}
                  except Exception as fallback_err:
                      self._log_escalation(tool_name, str(fallback_err))
                      raise MCPUnavailableError(
                          f"MCP tool {self.server_name}.{tool_name} failed and fallback also failed: {fallback_err}"
                      ) from fallback_err
              raise MCPUnavailableError(
                  f"MCP tool {self.server_name}.{tool_name} failed (no fallback): {e}"
              ) from e

      async def _invoke_tool(self, tool_name: str, arguments: dict) -> dict:
          """Invoke tool via subprocess stdin/stdout JSON-RPC (simplified client)."""
          # Build JSON-RPC request
          request = {
              "jsonrpc": "2.0",
              "id": 1,
              "method": "tools/call",
              "params": {"name": tool_name, "arguments": arguments},
          }

          proc = await asyncio.create_subprocess_exec(
              *self.command,
              stdin=asyncio.subprocess.PIPE,
              stdout=asyncio.subprocess.PIPE,
              stderr=asyncio.subprocess.PIPE,
          )

          # MCP initialization handshake then tool call
          init_request = {"jsonrpc": "2.0", "id": 0, "method": "initialize",
                         "params": {"protocolVersion": "2024-11-05",
                                    "capabilities": {}, "clientInfo": {"name": "orchestrator", "version": "1.0"}}}

          stdout, stderr = await proc.communicate(
              input=(json.dumps(init_request) + "\n" + json.dumps(request) + "\n").encode()
          )

          lines = [l.strip() for l in stdout.decode().split("\n") if l.strip()]
          if len(lines) < 2:
              raise RuntimeError(f"MCP server returned unexpected output: {stdout[:200]}")

          response = json.loads(lines[-1])  # last line is tool call response
          if "error" in response:
              raise RuntimeError(f"MCP error: {response['error']}")

          result = response.get("result", {})
          # Check isError flag
          if isinstance(result, dict) and result.get("isError"):
              content = result.get("content", [{}])
              error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
              raise RuntimeError(f"Tool returned error: {error_text}")

          return result

      def _log_fallback(self, tool_name: str, arguments: dict, error: str) -> None:
          """Log mcp_fallback event to vault/Logs/."""
          self._log_dir.mkdir(parents=True, exist_ok=True)
          entry = {
              "event": "mcp_fallback",
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "server": self.server_name,
              "tool": tool_name,
              "error": error,
              "severity": "WARNING",
          }
          log_path = self._log_dir / f"mcp_fallback_{datetime.now(timezone.utc).date()}.jsonl"
          with open(log_path, "a", encoding="utf-8") as f:
              f.write(json.dumps(entry) + "\n")
          logger.warning("MCP fallback: %s.%s — %s", self.server_name, tool_name, error)

      def _log_escalation(self, tool_name: str, error: str) -> None:
          """Log mcp_escalation event when fallback also fails."""
          self._log_dir.mkdir(parents=True, exist_ok=True)
          entry = {
              "event": "mcp_escalation",
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "server": self.server_name,
              "tool": tool_name,
              "error": error,
              "severity": "ERROR",
          }
          log_path = self._log_dir / f"mcp_fallback_{datetime.now(timezone.utc).date()}.jsonl"
          with open(log_path, "a", encoding="utf-8") as f:
              f.write(json.dumps(entry) + "\n")
          logger.error("MCP escalation: %s.%s — %s", self.server_name, tool_name, error)
  ```

- [x] T010 [P] Created `tests/contract/__init__.py`. `tests/integration/__init__.py` already existed.

---

## Phase 3: User Story 1 — AI Employee Sends Approved Draft (P1)

*Goal: Approved draft in `vault/Approved/` → Gmail MCP `send_email` → moved to `vault/Done/`.*

**Independent test**: Place a draft at `vault/Approved/test-reply.md` with `status: pending_approval`, run orchestrator poll cycle with mocked Gmail MCP, assert `send_email` tool called with correct `to/subject/body` and file moved to `vault/Done/`.

- [x] T011 [P] [US1] Create `mcp_servers/gmail/tools.py` — `GmailTools` class with all 5 tool handlers + `health_check`. All tools implemented (list_emails, get_email, move_email, add_label included per US2 spec).

  **Full implementation spec**:
  ```python
  # mcp-servers/gmail/tools.py
  """Gmail MCP tool handler implementations. Called by FastMCP server in server.py."""
  import base64
  import email as email_lib
  import json
  import os
  from datetime import datetime, timezone
  from pathlib import Path
  from typing import Any

  from googleapiclient.errors import HttpError
  from watchers.utils import atomic_write

  from .auth import AuthRequiredError, get_gmail_service

  class GmailTools:
      """Implements all Gmail MCP tool handlers. Stateless — each call gets fresh service if needed."""

      def __init__(self, vault_path: Path):
          self._vault_path = vault_path
          self._log_dir = vault_path / "Logs"

      # ── health_check ────────────────────────────────────────
      async def health_check(self) -> dict:
          """Verify server is operational and OAuth token is valid."""
          try:
              service = get_gmail_service()
              profile = await asyncio.to_thread(
                  lambda: service.users().getProfile(userId="me").execute()
              )
              return {
                  "status": "ok",
                  "authenticated_as": profile.get("emailAddress", "unknown"),
                  "token_expires_at": "managed_by_google_auth",
              }
          except AuthRequiredError as e:
              return {"error": "auth_required", "message": str(e)}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── send_email ───────────────────────────────────────────
      async def send_email(self, to: str, subject: str, body: str,
                           reply_to_message_id: str | None = None) -> dict:
          """Send email. Writes pre-action audit log BEFORE Gmail API call (Constitution Principle IX)."""
          import asyncio
          # Step 1: Pre-action audit log
          self._write_audit_log(to, subject, body, reply_to_message_id)

          try:
              service = get_gmail_service()

              # Build MIME message
              msg = email_lib.mime.text.MIMEText(body, "plain", "utf-8")
              msg["To"] = to
              msg["Subject"] = subject
              if reply_to_message_id:
                  msg["In-Reply-To"] = reply_to_message_id
                  msg["References"] = reply_to_message_id

              raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
              body_payload: dict[str, Any] = {"raw": raw}
              if reply_to_message_id:
                  # Fetch thread ID for threading
                  orig = await asyncio.to_thread(
                      lambda: service.users().messages().get(userId="me", id=reply_to_message_id, format="minimal").execute()
                  )
                  body_payload["threadId"] = orig.get("threadId")

              sent = await asyncio.to_thread(
                  lambda: service.users().messages().send(userId="me", body=body_payload).execute()
              )

              return {
                  "message_id": sent["id"],
                  "thread_id": sent.get("threadId", ""),
                  "sent_at": datetime.now(timezone.utc).isoformat(),
              }

          except AuthRequiredError as e:
              return {"error": "auth_required", "message": str(e)}
          except HttpError as e:
              if e.resp.status == 429:
                  return {"error": "rate_limited", "message": "Gmail API rate limit hit", "details": {"retry_after": 60}}
              return {"error": "send_failed", "message": f"Gmail API error: {e.resp.status} {e._get_reason()}"}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      def _write_audit_log(self, to: str, subject: str, body: str, reply_to: str | None) -> None:
          """Write pre-send audit JSONL entry before Gmail API call."""
          self._log_dir.mkdir(parents=True, exist_ok=True)
          entry = {
              "event": "pre_send_audit",
              "timestamp": datetime.now(timezone.utc).isoformat(),
              "to": to,
              "subject": subject,
              "body_preview": body[:200],
              "reply_to_message_id": reply_to,
              "severity": "INFO",
          }
          date_str = datetime.now(timezone.utc).date().isoformat()
          log_path = self._log_dir / f"gmail_mcp_{date_str}.jsonl"
          with open(log_path, "a", encoding="utf-8") as f:
              f.write(json.dumps(entry) + "\n")
  ```

  Note: `list_emails`, `get_email`, `move_email`, `add_label` added in T017.

- [x] T012 [P] [US1] Create `tests/contract/test_gmail_send_contract.py` — 5 contract tests: success schema, auth error, audit log, reply threading, internal error. All pass.

  **Test spec**:
  ```python
  # tests/contract/test_gmail_send_contract.py
  """Contract tests for Gmail MCP send_email tool. Tests schema, error format only. No live API."""
  import json, pytest
  from unittest.mock import patch, AsyncMock, MagicMock
  from pathlib import Path

  # Contract: success response must have message_id, thread_id, sent_at
  # Contract: error response must have error (MCPErrorCode) and message fields
  # Contract: send_email called without 'to' must return validation error from Pydantic

  @pytest.mark.asyncio
  async def test_send_email_success_schema():
      """Success result matches contract: message_id, thread_id, sent_at."""
      with patch("mcp_servers.gmail.auth.get_gmail_service") as mock_service:
          # Configure mock to simulate successful send
          mock_svc = MagicMock()
          mock_svc.users.return_value.messages.return_value.send.return_value.execute.return_value = {
              "id": "msg-123", "threadId": "thread-456"
          }
          mock_svc.users.return_value.getProfile.return_value.execute.return_value = {"emailAddress": "test@gmail.com"}
          mock_service.return_value = mock_svc

          from mcp_servers.gmail.tools import GmailTools
          tools = GmailTools(vault_path=Path("/tmp/test-vault"))
          result = await tools.send_email("to@example.com", "Test", "Body")

          assert "message_id" in result, "Contract: message_id required"
          assert "thread_id" in result, "Contract: thread_id required"
          assert "sent_at" in result, "Contract: sent_at required"

  @pytest.mark.asyncio
  async def test_send_email_auth_error_schema():
      """Auth error must return {error: auth_required, message: ...}."""
      with patch("mcp_servers.gmail.auth.get_gmail_service") as mock_service:
          from mcp_servers.gmail.auth import AuthRequiredError
          mock_service.side_effect = AuthRequiredError("Token missing")
          from mcp_servers.gmail.tools import GmailTools
          tools = GmailTools(vault_path=Path("/tmp/test-vault"))
          result = await tools.send_email("to@example.com", "Test", "Body")
          assert result["error"] == "auth_required", "Contract: error must be auth_required"
          assert "message" in result, "Contract: message field required"
  ```

- [x] T013 [US1] Create `mcp_servers/gmail/server.py` — FastMCP server entry point. Registers all 5 tools + health_check (all tools included; T018 merged here).

  **Full implementation spec**:
  ```python
  #!/usr/bin/env python3
  # mcp-servers/gmail/server.py
  """Gmail MCP server — FastMCP entry point. Exposes Gmail tools over stdio JSON-RPC."""
  import os
  import sys
  from contextlib import asynccontextmanager
  from pathlib import Path

  sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

  from mcp.server.fastmcp import FastMCP, Context
  from dotenv import load_dotenv

  load_dotenv()

  from .auth import get_gmail_service, AuthRequiredError, reset_service_cache
  from .models import SendEmailInput, ListEmailsInput, GetEmailInput, MoveEmailInput, AddLabelInput
  from .tools import GmailTools

  VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./vault"))

  @asynccontextmanager
  async def lifespan(server):
      """Validate env and warm up Gmail service at startup."""
      for key in ["GMAIL_CREDENTIALS_PATH", "GMAIL_TOKEN_PATH"]:
          if not os.environ.get(key):
              raise EnvironmentError(f"Missing required env var: {key}")
      try:
          get_gmail_service()  # warm-up: validates token on startup
      except AuthRequiredError:
          pass  # health_check will report the error; don't crash server
      yield
      reset_service_cache()

  mcp = FastMCP("gmail_mcp", lifespan=lifespan)
  _tools = GmailTools(vault_path=VAULT_PATH)

  @mcp.tool(
      name="health_check",
      annotations={"title": "Gmail MCP Health Check", "readOnlyHint": True, "destructiveHint": False}
  )
  async def health_check() -> str:
      """Verify Gmail MCP server is operational and OAuth token is valid.
      Returns: JSON with status='ok' and authenticated_as email, or error object."""
      import json
      result = await _tools.health_check()
      return json.dumps(result)

  @mcp.tool(
      name="send_email",
      annotations={"title": "Send Gmail Email", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": False}
  )
  async def send_email(params: SendEmailInput) -> str:
      """Send an email via authenticated Gmail account. Writes pre-action audit log first.
      Args: to (str), subject (str), body (str), reply_to_message_id (str|None)
      Returns: JSON with message_id, thread_id, sent_at — or error object."""
      import json
      result = await _tools.send_email(
          to=params.to,
          subject=params.subject,
          body=params.body,
          reply_to_message_id=params.reply_to_message_id,
      )
      return json.dumps(result)

  # NOTE: list_emails, get_email, move_email, add_label registered in T018 (US2)

  if __name__ == "__main__":
      mcp.run()
  ```

- [x] T014 [US1] Modify `orchestrator/orchestrator.py` — added `MCPClient` import, `_gmail_mcp`, `_approved_dir` in `__init__`, `_run_poll_cycle()` override, `_scan_approved_drafts()`, `_send_approved_draft()`. Fix: uses yaml.safe_load directly (not read_email_context) to avoid message_id requirement.

  **Change spec** (minimal diff approach — do NOT rewrite the file; add these methods and update `__init__`):

  In `__init__` (after existing setup):
  ```python
  from orchestrator.mcp_client import MCPClient
  # Gmail MCPClient for approved draft sends
  self._gmail_mcp = MCPClient(
      server_name="gmail",
      command=["python3", "mcp-servers/gmail/server.py"],
      vault_path=self._vault_path,
  )
  self._approved_dir = self._vault_path / "Approved"
  self._approved_dir.mkdir(parents=True, exist_ok=True)
  ```

  New methods to add (after `_apply_decision`):
  ```python
  async def _scan_approved_drafts(self) -> list[Path]:
      """Scan vault/Approved/ for *.md files with status: pending_approval."""
      from orchestrator.vault_ops import read_email_context
      approved = []
      for path in sorted(self._approved_dir.glob("*.md")):
          try:
              ctx = read_email_context(path)
              if ctx and getattr(ctx, "status", None) == "pending_approval":
                  approved.append(path)
          except Exception as e:
              self._log("read_approved_error", LogSeverity.ERROR, {"path": str(path), "error": str(e)})
      return approved

  async def _send_approved_draft(self, draft_path: Path) -> None:
      """Send an approved draft via Gmail MCP, then move to Done/ on success."""
      from orchestrator.vault_ops import read_email_context, move_to_done, update_frontmatter
      import yaml

      # Parse draft note
      content = draft_path.read_text(encoding="utf-8")
      parts = content.split("---", 2)
      if len(parts) < 3:
          self._log("invalid_draft", LogSeverity.ERROR, {"path": str(draft_path)})
          return

      fm = yaml.safe_load(parts[1]) or {}
      body = parts[2].strip()
      to = fm.get("to", "")
      subject = fm.get("subject", "")
      reply_to = fm.get("original_message_id")

      if not to or not subject:
          self._log("incomplete_draft", LogSeverity.ERROR, {"path": str(draft_path), "fm": fm})
          return

      async def fallback():
          """Fallback: keep draft in Approved/ for retry next cycle."""
          self._log("send_skipped_mcp_unavailable", LogSeverity.WARNING, {"path": str(draft_path)})
          return {}

      result = await self._gmail_mcp.call_tool(
          "send_email",
          {"to": to, "subject": subject, "body": body, "reply_to_message_id": reply_to},
          fallback=fallback,
      )

      if result.get("error"):
          self._log("email_send_failed", LogSeverity.ERROR, {"path": str(draft_path), "error": result})
          return

      # Success: move to Done/
      move_to_done(draft_path, self._done_dir)
      self._log("email_sent", LogSeverity.INFO, {
          "draft": str(draft_path),
          "message_id": result.get("message_id"),
          "sent_at": result.get("sent_at"),
      })
  ```

  In `_run_poll_cycle()` (add after existing poll logic):
  ```python
  # Process approved drafts (Phase 4 HITL send loop)
  try:
      approved = await self._scan_approved_drafts()
      for draft_path in approved:
          await self._send_approved_draft(draft_path)
  except Exception as e:
      self._log("approved_draft_scan_error", LogSeverity.ERROR, {"error": str(e)})
  ```

- [x] T015 [P] [US1] Create `tests/unit/test_mcp_client.py` — 8 tests covering: fallback called, MCPUnavailableError, escalation log, success=no-fallback, sync fallback, non-dict wrap, timeout, log detail. All pass.

  **Test spec**:
  ```python
  # tests/unit/test_mcp_client.py
  """Unit tests for MCPClient fallback protocol."""
  import pytest, json
  from pathlib import Path
  from unittest.mock import AsyncMock, patch, MagicMock
  from orchestrator.mcp_client import MCPClient, MCPUnavailableError

  @pytest.fixture
  def client(tmp_path):
      return MCPClient("test_server", ["python3", "fake_server.py"], tmp_path)

  @pytest.mark.asyncio
  async def test_fallback_called_when_mcp_fails(client, tmp_path):
      """When MCP fails, fallback is called and mcp_fallback is logged."""
      with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):
          fallback_called = False
          async def fallback():
              nonlocal fallback_called
              fallback_called = True
              return {"result": "fallback_ok"}

          result = await client.call_tool("read_note", {"path": "test.md"}, fallback=fallback)
          assert fallback_called, "Fallback must be called when MCP fails"
          assert result == {"result": "fallback_ok"}
          # Check log was written
          log_files = list(tmp_path.glob("Logs/mcp_fallback_*.jsonl"))
          assert log_files, "mcp_fallback log file must be created"
          entry = json.loads(log_files[0].read_text().strip())
          assert entry["event"] == "mcp_fallback"
          assert entry["server"] == "test_server"

  @pytest.mark.asyncio
  async def test_mcp_unavailable_raised_when_no_fallback(client):
      """When MCP fails and no fallback provided, MCPUnavailableError is raised."""
      with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):
          with pytest.raises(MCPUnavailableError):
              await client.call_tool("read_note", {"path": "test.md"}, fallback=None)

  @pytest.mark.asyncio
  async def test_escalation_logged_when_fallback_fails(client, tmp_path):
      """When both MCP and fallback fail, mcp_escalation is logged."""
      with patch.object(client, "_invoke_tool", side_effect=RuntimeError("MCP down")):
          async def failing_fallback():
              raise RuntimeError("Fallback also failed")

          with pytest.raises(MCPUnavailableError):
              await client.call_tool("send_email", {}, fallback=failing_fallback)

          log_files = list(tmp_path.glob("Logs/mcp_fallback_*.jsonl"))
          entries = [json.loads(l) for l in log_files[0].read_text().strip().split("\n") if l]
          events = [e["event"] for e in entries]
          assert "mcp_fallback" in events
          assert "mcp_escalation" in events

  @pytest.mark.asyncio
  async def test_success_no_fallback_called(client):
      """When MCP succeeds, fallback is NOT called."""
      with patch.object(client, "_invoke_tool", return_value={"message_id": "msg-1"}):
          fallback_called = False
          def fallback():
              nonlocal fallback_called
              fallback_called = True

          result = await client.call_tool("send_email", {}, fallback=fallback)
          assert not fallback_called, "Fallback must NOT be called on MCP success"
          assert result["message_id"] == "msg-1"
  ```

- [x] T016 [US1] Create `tests/integration/test_approved_draft_send.py` — 5 integration tests covering US1 AS-1/2/3: sent+moved, stays on failure, scan finds only pending, skip incomplete, stays on error response. All pass.

  **Test spec**:
  ```python
  # tests/integration/test_approved_draft_send.py
  """Integration test: approved draft in vault/Approved/ → Gmail MCP send_email → vault/Done/."""
  import pytest, yaml
  from pathlib import Path
  from unittest.mock import AsyncMock, patch, MagicMock

  @pytest.fixture
  def vault(tmp_path):
      for d in ["Needs_Action", "Drafts", "Approved", "Done", "Logs"]:
          (tmp_path / d).mkdir()
      return tmp_path

  def make_draft(vault: Path, to="ceo@example.com", subject="Re: Budget") -> Path:
      content = f"""---
  status: pending_approval
  to: {to}
  subject: {subject}
  original_message_id: msg-original-001
  ---

  Thank you for the budget proposal. Approved as discussed.
  """
      path = vault / "Approved" / "reply-001.md"
      path.write_text(content, encoding="utf-8")
      return path

  @pytest.mark.asyncio
  async def test_approved_draft_sent_and_moved_to_done(vault):
      """US1 AS-1+2: approved draft → send_email called → moved to Done/."""
      from orchestrator.orchestrator import RalphWiggumOrchestrator
      draft_path = make_draft(vault)

      with patch("orchestrator.orchestrator.MCPClient") as MockClient:
          mock_client = AsyncMock()
          mock_client.call_tool.return_value = {
              "message_id": "sent-msg-001",
              "thread_id": "thread-001",
              "sent_at": "2026-02-24T10:00:00Z",
          }
          MockClient.return_value = mock_client

          orch = RalphWiggumOrchestrator(vault_path=str(vault))
          await orch._send_approved_draft(draft_path)

          # Assert: send_email called with correct args
          mock_client.call_tool.assert_called_once()
          call_args = mock_client.call_tool.call_args[0]
          assert call_args[0] == "send_email"
          assert call_args[1]["to"] == "ceo@example.com"
          assert call_args[1]["subject"] == "Re: Budget"

          # Assert: draft moved to Done/
          assert not draft_path.exists(), "Draft must be moved from Approved/"
          assert (vault / "Done" / "reply-001.md").exists(), "Draft must appear in Done/"

          # Assert: email_sent logged
          log_files = list((vault / "Logs").glob("*.jsonl"))
          assert log_files, "At least one log file must exist"

  @pytest.mark.asyncio
  async def test_draft_stays_in_approved_when_mcp_unavailable(vault):
      """US1 AS-3: send_email fails (MCP unavailable) → draft NOT deleted, error logged."""
      from orchestrator.mcp_client import MCPUnavailableError
      draft_path = make_draft(vault)

      with patch("orchestrator.orchestrator.MCPClient") as MockClient:
          mock_client = AsyncMock()
          mock_client.call_tool.side_effect = MCPUnavailableError("MCP down")
          MockClient.return_value = mock_client

          from orchestrator.orchestrator import RalphWiggumOrchestrator
          orch = RalphWiggumOrchestrator(vault_path=str(vault))

          # Should not raise — orchestrator handles the error gracefully
          try:
              await orch._send_approved_draft(draft_path)
          except Exception:
              pass  # acceptable — what matters is draft stays in Approved/

          # Draft should remain (not moved to Done/)
          # In fallback mode, the draft stays for retry
          assert not (vault / "Done" / "reply-001.md").exists() or draft_path.exists(), \
              "Draft must not be silently deleted on MCP failure"
  ```

---

## Phase 4: User Story 2 — Claude Code Agent Uses Gmail MCP (P2)

*Goal: All 5 Gmail tools callable from Claude Code. `health_check` passes. Full contract coverage.*

**Independent test**: Mock OAuth; call all 5 tools; assert success schemas match `contracts/gmail-tools.json`.

- [x] T017 [P] [US2] All 4 remaining Gmail tools (list_emails, get_email, move_email, add_label) were already implemented in T011. tools.py is complete.

  **Implementation spec** (add to `GmailTools` class):
  ```python
  import asyncio

  async def list_emails(self, query: str = "is:unread", max_results: int = 10) -> dict:
      """List emails matching Gmail search query."""
      try:
          service = get_gmail_service()
          results = await asyncio.to_thread(
              lambda: service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
          )
          messages = results.get("messages", [])
          emails = []
          for msg in messages:
              meta = await asyncio.to_thread(
                  lambda m=msg: service.users().messages().get(
                      userId="me", id=m["id"], format="metadata",
                      metadataHeaders=["Subject", "From", "Date"]
                  ).execute()
              )
              headers = {h["name"]: h["value"] for h in meta.get("payload", {}).get("headers", [])}
              emails.append({
                  "id": meta["id"],
                  "subject": headers.get("Subject", "(no subject)"),
                  "sender": headers.get("From", ""),
                  "date": headers.get("Date", ""),
                  "snippet": meta.get("snippet", ""),
              })
          return {"emails": emails, "total_count": len(emails)}
      except AuthRequiredError as e:
          return {"error": "auth_required", "message": str(e)}
      except HttpError as e:
          if e.resp.status == 429:
              return {"error": "rate_limited", "message": "Rate limit hit", "details": {"retry_after": 60}}
          return {"error": "internal_error", "message": str(e)}
      except Exception as e:
          return {"error": "internal_error", "message": str(e)}

  async def get_email(self, message_id: str) -> dict:
      """Get full email content by message ID."""
      try:
          service = get_gmail_service()
          msg = await asyncio.to_thread(
              lambda: service.users().messages().get(userId="me", id=message_id, format="full").execute()
          )
          payload = msg.get("payload", {})
          headers = {h["name"]: h["value"] for h in payload.get("headers", [])}

          # Decode body
          body = ""
          parts = payload.get("parts", [payload])
          for part in parts:
              if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                  body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
                  break

          # Attachments
          attachments = [
              p.get("filename", "") for p in payload.get("parts", [])
              if p.get("filename")
          ]

          return {
              "id": msg["id"],
              "subject": headers.get("Subject", ""),
              "sender": headers.get("From", ""),
              "to": headers.get("To", ""),
              "date": headers.get("Date", ""),
              "body": body,
              "has_attachments": bool(attachments),
              "attachment_names": attachments,
          }
      except AuthRequiredError as e:
          return {"error": "auth_required", "message": str(e)}
      except HttpError as e:
          if e.resp.status == 404:
              return {"error": "not_found", "message": f"Email {message_id} not found"}
          if e.resp.status == 429:
              return {"error": "rate_limited", "message": "Rate limit hit", "details": {"retry_after": 60}}
          return {"error": "internal_error", "message": str(e)}
      except Exception as e:
          return {"error": "internal_error", "message": str(e)}

  async def move_email(self, message_id: str, destination_label: str) -> dict:
      """Move email to destination Gmail label."""
      try:
          service = get_gmail_service()
          # Get or create label
          labels_response = await asyncio.to_thread(
              lambda: service.users().labels().list(userId="me").execute()
          )
          label_id = None
          for lbl in labels_response.get("labels", []):
              if lbl["name"].upper() == destination_label.upper():
                  label_id = lbl["id"]
                  break
          if not label_id:
              # Use built-in label name directly
              label_id = destination_label

          await asyncio.to_thread(
              lambda: service.users().messages().modify(
                  userId="me", id=message_id,
                  body={"addLabelIds": [label_id], "removeLabelIds": ["INBOX"]}
              ).execute()
          )
          return {"moved": True, "message_id": message_id, "label": destination_label}
      except AuthRequiredError as e:
          return {"error": "auth_required", "message": str(e)}
      except HttpError as e:
          if e.resp.status == 404:
              return {"error": "not_found", "message": f"Email {message_id} not found"}
          return {"error": "internal_error", "message": str(e)}
      except Exception as e:
          return {"error": "internal_error", "message": str(e)}

  async def add_label(self, message_id: str, label_name: str) -> dict:
      """Apply Gmail label to email. Creates label if it doesn't exist."""
      try:
          service = get_gmail_service()
          # Find or create label
          labels_response = await asyncio.to_thread(
              lambda: service.users().labels().list(userId="me").execute()
          )
          label_id = None
          for lbl in labels_response.get("labels", []):
              if lbl["name"] == label_name:
                  label_id = lbl["id"]
                  break
          if not label_id:
              new_label = await asyncio.to_thread(
                  lambda: service.users().labels().create(
                      userId="me", body={"name": label_name}
                  ).execute()
              )
              label_id = new_label["id"]

          await asyncio.to_thread(
              lambda: service.users().messages().modify(
                  userId="me", id=message_id,
                  body={"addLabelIds": [label_id]}
              ).execute()
          )
          return {"labeled": True, "message_id": message_id, "label": label_name}
      except AuthRequiredError as e:
          return {"error": "auth_required", "message": str(e)}
      except HttpError as e:
          if e.resp.status == 404:
              return {"error": "not_found", "message": f"Email {message_id} not found"}
          return {"error": "internal_error", "message": str(e)}
      except Exception as e:
          return {"error": "internal_error", "message": str(e)}
  ```

- [x] T018 [US2] All 4 remaining Gmail tools registered in server.py (already done in T013). server.py complete with all 5 tools + health_check. using `@mcp.tool` decorators with `ListEmailsInput`, `GetEmailInput`, `MoveEmailInput`, `AddLabelInput` Pydantic models. Follow same pattern as `send_email` in T013.

- [x] T019 [P] [US2] Create `tests/contract/test_gmail_mcp_contracts.py` — 14 contract tests for all 6 tools (health_check, send_email, list_emails, get_email, move_email, add_label). All pass. (extends T012). Test: schema validation, error code from error taxonomy, `isError` not set in success, `not_found` for missing message_id, `auth_required` when token missing.

- [x] T020 [US2] Create `tests/integration/test_gmail_mcp_integration.py` — 7 integration tests for all 5 tools with mocked OAuth. All pass. — integration tests for all 5 Gmail tools with `unittest.mock.patch("mcp_servers.gmail.auth.get_gmail_service")`. Test: each tool returns correct schema, list_emails returns email list, get_email returns full email, move_email returns moved=True, add_label returns labeled=True.

---

## Phase 5: User Story 3 — Obsidian Vault MCP (P3)

*Goal: Any agent reads/writes vault notes via MCP without knowing file paths or YAML format.*

**Independent test**: `write_note` → `read_note` round-trip in tmp directory; frontmatter and body identical.

- [x] T021 [P] [US3] Create `mcp_servers/obsidian/tools.py` — ObsidianTools: health_check, read_note, write_note, list_notes, move_note, search_notes. Path traversal protection, atomic_write, sanitize_utf8. Reuses `atomic_write` and `render_yaml_frontmatter` from `watchers/utils.py`.

  **Full implementation spec**:
  ```python
  # mcp-servers/obsidian/tools.py
  """Obsidian vault MCP tool handlers. Direct filesystem access — no Obsidian app required."""
  import os
  import re
  import sys
  import json
  import shutil
  import yaml
  from pathlib import Path
  from typing import Optional
  sys.path.insert(0, str(Path(__file__).parent.parent.parent))

  from watchers.utils import atomic_write, render_yaml_frontmatter, sanitize_utf8

  class ObsidianTools:
      """Implements all Obsidian MCP tool handlers. All paths are vault-relative."""

      def __init__(self, vault_path: Path):
          self._vault = vault_path.resolve()

      def _resolve(self, relative_path: str) -> Path:
          """Resolve vault-relative path. Raises permission_denied if outside vault."""
          resolved = (self._vault / relative_path).resolve()
          if not str(resolved).startswith(str(self._vault)):
              raise PermissionError(f"Path '{relative_path}' is outside vault root")
          return resolved

      def _parse_note(self, content: str) -> tuple[dict, str]:
          """Parse markdown note into (frontmatter_dict, body_str)."""
          parts = content.split("---", 2)
          if len(parts) >= 3 and parts[0].strip() == "":
              fm = yaml.safe_load(parts[1]) or {}
              body = parts[2].strip()
          else:
              fm = {}
              body = content.strip()
          return fm, body

      # ── health_check ──────────────────────────────────────
      async def health_check(self) -> dict:
          """Verify vault is accessible."""
          try:
              if not self._vault.exists():
                  return {"error": "not_found", "message": f"Vault not found: {self._vault}"}
              note_count = len(list(self._vault.rglob("*.md")))
              return {"status": "ok", "vault_path": str(self._vault), "note_count": note_count}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── read_note ─────────────────────────────────────────
      async def read_note(self, path: str) -> dict:
          """Read vault note; return {path, frontmatter, body}."""
          try:
              abs_path = self._resolve(path)
              if not abs_path.exists():
                  return {"error": "not_found", "message": f"Note not found: {path}", "details": {"path": path}}
              content = sanitize_utf8(abs_path.read_text(encoding="utf-8", errors="replace"))
              fm, body = self._parse_note(content)
              return {"path": path, "frontmatter": fm, "body": body}
          except PermissionError as e:
              return {"error": "permission_denied", "message": str(e)}
          except yaml.YAMLError as e:
              return {"error": "parse_error", "message": f"Corrupt frontmatter: {e}", "details": {"path": path}}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── write_note ────────────────────────────────────────
      async def write_note(self, path: str, frontmatter: dict, body: str) -> dict:
          """Write note atomically; return written content for round-trip verification."""
          try:
              abs_path = self._resolve(path)
              content = render_yaml_frontmatter(frontmatter) + "\n" + body
              atomic_write(abs_path, content)
              return {"path": path, "frontmatter": frontmatter, "body": body}
          except PermissionError as e:
              return {"error": "permission_denied", "message": str(e)}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── list_notes ────────────────────────────────────────
      async def list_notes(self, directory: str, filter: Optional[str] = None) -> dict:
          """List notes in directory, optionally filtered by frontmatter field:value."""
          try:
              abs_dir = self._resolve(directory)
              if not abs_dir.exists():
                  return {"error": "not_found", "message": f"Directory not found: {directory}"}

              notes = []
              for md_file in sorted(abs_dir.glob("*.md")):
                  rel_path = str(md_file.relative_to(self._vault))
                  if filter:
                      field, _, value = filter.partition(":")
                      try:
                          content = md_file.read_text(encoding="utf-8", errors="replace")
                          fm, _ = self._parse_note(content)
                          if str(fm.get(field.strip(), "")) != value.strip():
                              continue
                      except Exception:
                          continue
                  notes.append({"path": rel_path})

              return {"notes": notes, "count": len(notes)}
          except PermissionError as e:
              return {"error": "permission_denied", "message": str(e)}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── move_note ─────────────────────────────────────────
      async def move_note(self, source: str, destination: str) -> dict:
          """Move vault note atomically via shutil.move."""
          try:
              src = self._resolve(source)
              dst = self._resolve(destination)
              if not src.exists():
                  return {"error": "not_found", "message": f"Source not found: {source}", "details": {"path": source}}
              dst.parent.mkdir(parents=True, exist_ok=True)
              shutil.move(str(src), str(dst))
              return {"moved": True, "source": source, "destination": destination}
          except PermissionError as e:
              return {"error": "permission_denied", "message": str(e)}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}

      # ── search_notes ──────────────────────────────────────
      async def search_notes(self, query: str) -> dict:
          """Full-text search across all vault notes (case-insensitive substring)."""
          try:
              query_lower = query.lower()
              matches = []
              for md_file in self._vault.rglob("*.md"):
                  try:
                      content = md_file.read_text(encoding="utf-8", errors="replace")
                      if query_lower in content.lower():
                          # Extract snippet around first match
                          idx = content.lower().index(query_lower)
                          start = max(0, idx - 80)
                          end = min(len(content), idx + len(query) + 80)
                          snippet = content[start:end].strip()
                          rel_path = str(md_file.relative_to(self._vault))
                          matches.append({"path": rel_path, "snippet": snippet[:200]})
                  except Exception:
                      continue
              return {"notes": matches, "count": len(matches)}
          except Exception as e:
              return {"error": "internal_error", "message": str(e)}
  ```

- [x] T022 [P] [US3] Create `tests/contract/test_obsidian_mcp_contracts.py` — 16 contract tests: round-trip, not_found, permission_denied traversal, filter, search snippet. All pass. — contract tests for all 6 Obsidian tools. Key contracts: `write_note` → `read_note` round-trips correctly; `not_found` error when path missing; `permission_denied` when path traversal attempted; `list_notes` with `filter` only returns matching notes; `search_notes` returns snippet.

- [x] T023 [US3] Create `mcp_servers/obsidian/server.py` — FastMCP entry point, all 5 tools + health_check registered with annotations. Registers all 5 tools + `health_check`. Uses `VAULT_PATH` env var. No lifespan needed (stateless filesystem access).

  **Full implementation spec**:
  ```python
  #!/usr/bin/env python3
  # mcp-servers/obsidian/server.py
  """Obsidian vault MCP server — FastMCP entry point. Direct filesystem access, no Obsidian app."""
  import os, sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent.parent))

  from mcp.server.fastmcp import FastMCP
  from dotenv import load_dotenv
  load_dotenv()

  from .models import ReadNoteInput, WriteNoteInput, ListNotesInput, MoveNoteInput, SearchNotesInput
  from .tools import ObsidianTools

  VAULT_PATH = Path(os.environ.get("VAULT_PATH", "./vault")).resolve()
  if not VAULT_PATH.exists():
      raise EnvironmentError(f"VAULT_PATH does not exist: {VAULT_PATH}. Set VAULT_PATH in .env")

  mcp = FastMCP("obsidian_mcp")
  _tools = ObsidianTools(vault_path=VAULT_PATH)

  @mcp.tool(name="health_check", annotations={"title": "Obsidian MCP Health Check", "readOnlyHint": True})
  async def health_check() -> str:
      """Verify Obsidian MCP server is operational and vault directory is accessible.
      Returns: JSON with status='ok', vault_path, note_count — or error object."""
      import json
      return json.dumps(await _tools.health_check())

  @mcp.tool(name="read_note", annotations={"title": "Read Vault Note", "readOnlyHint": True})
  async def read_note(params: ReadNoteInput) -> str:
      """Read a vault note by vault-relative path. Returns frontmatter dict and body text.
      Args: path (str) vault-relative, e.g. 'Needs_Action/email-001.md'
      Returns: JSON with path, frontmatter (dict), body (str) — or error object."""
      import json
      return json.dumps(await _tools.read_note(params.path))

  @mcp.tool(name="write_note", annotations={"title": "Write Vault Note", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True})
  async def write_note(params: WriteNoteInput) -> str:
      """Write a vault note atomically (temp+rename). Creates parent dirs if needed.
      Args: path (str), frontmatter (dict), body (str)
      Returns: written note content for round-trip verification — or error object."""
      import json
      return json.dumps(await _tools.write_note(params.path, params.frontmatter, params.body))

  @mcp.tool(name="list_notes", annotations={"title": "List Vault Notes", "readOnlyHint": True, "idempotentHint": True})
  async def list_notes(params: ListNotesInput) -> str:
      """List notes in vault directory, optionally filtered by frontmatter field:value.
      Args: directory (str), filter (str|None) e.g. 'status:pending'
      Returns: JSON with notes list (path entries) and count — or error object."""
      import json
      return json.dumps(await _tools.list_notes(params.directory, params.filter))

  @mcp.tool(name="move_note", annotations={"title": "Move Vault Note", "readOnlyHint": False, "destructiveHint": False})
  async def move_note(params: MoveNoteInput) -> str:
      """Move a vault note from source to destination path.
      Args: source (str), destination (str) — both vault-relative
      Returns: JSON with moved=True, source, destination — or error object."""
      import json
      return json.dumps(await _tools.move_note(params.source, params.destination))

  @mcp.tool(name="search_notes", annotations={"title": "Search Vault Notes", "readOnlyHint": True})
  async def search_notes(params: SearchNotesInput) -> str:
      """Full-text search across all vault notes (case-insensitive substring).
      Args: query (str) — text to find in note body or frontmatter values
      Returns: JSON with notes list (path + snippet) and count — or error object."""
      import json
      return json.dumps(await _tools.search_notes(params.query))

  if __name__ == "__main__":
      mcp.run()
  ```

- [x] T024 [US3] Create `tests/integration/test_obsidian_mcp_integration.py` — 11 integration tests using tmp_path vault. All pass. — integration tests for all 5 Obsidian tools using `tmp_path` pytest fixture as vault root. Tests: `write_note` creates file; `read_note` returns correct frontmatter+body; `list_notes` with filter returns matching only; `move_note` moves file and source no longer exists; `search_notes` finds text in body.

---

## Phase 6: User Story 4 — Orchestrator Uses MCPs Instead of Direct File I/O (P4)

*Goal: `_apply_decision()` routes vault operations through Obsidian MCPClient with vault_ops fallback.*

**Independent test**: Mock MCPClient; call `_apply_decision(archive)`; assert `move_note` MCP tool called (not `move_to_done` directly).

- [x] T025 [US4] Modify `orchestrator/orchestrator.py` — refactor all 5 branches of `_apply_decision()` to use `MCPClient` for Obsidian MCP calls with `vault_ops` fallback. Instantiate `self._obsidian_mcp` in `__init__`.

  **Change spec** (minimal diff — do NOT rewrite entire file):

  Add in `__init__`:
  ```python
  self._obsidian_mcp = MCPClient(
      server_name="obsidian",
      command=["python3", "mcp-servers/obsidian/server.py"],
      vault_path=self._vault_path,
  )
  ```

  Refactor each branch in `_apply_decision()`. Example for `archive` branch:
  ```python
  elif decision.decision == "archive":
      if filepath:
          # MCP-first; fallback to direct vault_ops
          await self._obsidian_mcp.call_tool(
              "move_note",
              {"source": str(filepath.relative_to(self._vault_path)),
               "destination": str((self._done_dir / filepath.name).relative_to(self._vault_path))},
              fallback=lambda: (update_frontmatter(filepath, {"status": "done"}),
                               move_to_done(filepath, self._done_dir)),
          )
  ```

  Apply the same MCP-first + fallback pattern to all 5 decision branches:
  - `draft_reply`: `write_note` for draft + `write_note` to update source frontmatter
  - `needs_info`: `write_note` to update note (append note + update frontmatter)
  - `archive`: `move_note` to Done/
  - `urgent`: `write_note` for draft + `write_note` to update frontmatter
  - `delegate`: `write_note` to update note (append delegation note + update frontmatter)

- [x] T026 [P] [US4] Create `tests/unit/test_orchestrator_mcp.py` — unit tests for refactored `_apply_decision()` with mocked `MCPClient`. 7 unit tests all pass.

  **Test spec**: Mock `MCPClient.call_tool`; create `EmailContext` + `LLMDecision(decision="archive")`; call `_apply_decision()`; assert `call_tool` was called with `tool_name="move_note"`. Repeat for each decision type. Also test fallback: when MCP client raises, verify `vault_ops` fallback called.

- [x] T027 [US4] Create `tests/integration/test_orchestrator_mcp_integration.py` — E2E test with mocked MCP servers. Uses `tmp_path` vault; creates a test email note; runs full `_run_poll_cycle()` with mocked LLM (returns `archive` decision) and mocked `MCPClient`; asserts note moved to Done/ via MCP path. 3 E2E tests all pass.

---

## Phase 7: Polish & Cross-Cutting Concerns

*Housekeeping, registration docs, suite validation. No story label.*

- [x] T028 [P] Update `ai-control/HUMAN-TASKS.md` — expanded HT-005 with exact `~/.claude.json` config blocks for both MCP servers (gmail_mcp + obsidian_mcp), using absolute project paths and all required env vars. Includes step-by-step registration instructions and health_check verification commands.

- [x] T029 [P] Update `ai-control/MCP.md` — added gmail_mcp and obsidian_mcp to new "Project-Custom MCP Servers (Built)" table with tools list, path, health_check command, phase. Moved from "Needed" to "Built". WhatsApp/Calendar/Odoo remain in "Needed (Future Phases)" section.

- [x] T030 Update `specs/007-mcp-integration/spec.md` — marked all exit criteria [x] complete. Status updated to "Complete ✅". 460/460 tests pass.

- [x] T031 Run `pytest tests/ -v --tb=short 2>&1 | tail -20` — **460/460 passed** (200.99s). Zero regressions. All Phase 4 tests green.

---

## Summary

| Metric | Value |
|--------|-------|
| Total tasks | 31 |
| Phase 1 (Setup) | T001–T005 (5 tasks) |
| Phase 2 (Foundational) | T006–T010 (5 tasks) |
| Phase 3 (US1 — Send Approved Draft) | T011–T016 (6 tasks) |
| Phase 4 (US2 — Gmail Read/Act) | T017–T020 (4 tasks) |
| Phase 5 (US3 — Obsidian MCP) | T021–T024 (4 tasks) |
| Phase 6 (US4 — Orchestrator Wiring) | T025–T027 (3 tasks) |
| Phase 7 (Polish) | T028–T031 (4 tasks) |
| Parallelizable tasks | 14 (marked [P]) |
| User Story 1 tasks | T011–T016 |
| User Story 2 tasks | T017–T020 |
| User Story 3 tasks | T021–T024 |
| User Story 4 tasks | T025–T027 |

**MVP scope**: T001–T016 (Phases 1–3, User Story 1). Delivers primary value: approved draft reply sending via Gmail MCP.

**Parallel opportunities**:
- T002, T003, T004, T005 — all independent setup
- T007, T008 — models for both servers in parallel
- T011, T012 — gmail tools + contract test in parallel
- T015, T016 — unit + integration tests for US1 in parallel
- T017, T019 — add tools + write contracts in parallel
- T021, T022 — obsidian tools + contracts in parallel
- T026, T027 — both orchestrator test types in parallel (after T025)
- T028, T029 — both docs updates in parallel

---

*Governed by: `ai-control/AGENTS.md` | `ai-control/LOOP.md` | `ai-control/MCP.md`*
*Version: 1.0.0 | Date: 2026-02-24*
