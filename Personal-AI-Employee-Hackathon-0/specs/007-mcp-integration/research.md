# Phase 0 Research: MCP Integration — Phase 4

**Branch**: `007-mcp-integration` | **Date**: 2026-02-24
**Sources**: Codebase scan (agent adb1988) + MCP SDK deep-dive (agent a0ac7bf)

---

## Decision 1: MCP SDK API — Low-Level Server vs. FastMCP

**Decision**: Use `mcp.server.lowlevel.server.Server` (low-level API).

**Rationale**:
- Explicit control over `@server.list_tools()` and `@server.call_tool()` decorators.
- Tool schemas are `pydantic.BaseModel.model_json_schema()` — integrates cleanly with existing Pydantic models.
- FastMCP adds an extra abstraction layer not needed for 5-tool servers.
- The low-level API is what the installed SDK exposes at `mcp.server.lowlevel.server.Server`.

**Alternatives Considered**:
- **FastMCP** (`mcp.server.fastmcp.server`) — rejected: hides tool schema declaration; less control over error response format.
- **Raw JSON-RPC** — rejected: reinventing the wheel; SDK handles framing.

**Key SDK Facts** (from `.venv/lib/python3.12/site-packages/mcp/`):
```python
from mcp.server.lowlevel.server import Server
from mcp.server import stdio
from mcp.types import Tool, TextContent, CallToolResult

server = Server("my-server", version="1.0.0")

@server.list_tools()
async def list_tools(): ...

@server.call_tool()
async def call_tool(name: str, arguments: dict): ...

async def main():
    async with stdio.stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
                         server.create_initialization_options())
```

---

## Decision 2: OAuth2 Reuse Pattern

**Decision**: Extract `_authenticate()` logic from `watchers/gmail_watcher.py` into `mcp-servers/gmail/auth.py` as a standalone function — no subclassing, no BaseWatcher.

**Rationale**:
- Lines 170–211 of `gmail_watcher.py` implement the complete OAuth2 lifecycle: load token → validate → refresh → reauth → `atomic_write` save.
- The Gmail MCP must NOT start a browser auth flow in MCP mode — token **must** already exist (from HT-002). The auth.py adapter will raise `RuntimeError` (logged as `auth_required`) if token is missing.
- `self._service = build("gmail", "v1", credentials=creds)` → store as module-level singleton in `auth.py` to avoid per-call auth overhead.

**Reuse pattern**:
```python
# mcp-servers/gmail/auth.py
def get_gmail_service() -> Resource:
    """Return authenticated Gmail service. Token must exist (from HT-002).
    Raises: AuthRequiredError if token missing/expired and cannot refresh."""
    token_path = Path(os.environ["GMAIL_TOKEN_PATH"])
    creds_path = Path(os.environ["GMAIL_CREDENTIALS_PATH"])
    creds = _load_and_refresh(token_path, creds_path)  # reuse pattern from gmail_watcher.py
    return build("gmail", "v1", credentials=creds)
```

**Alternatives Considered**:
- **Inherit from BaseWatcher** — rejected: MCP server is not a watcher; inheritance would pull in poll/process_item lifecycle.
- **Re-implement OAuth2 from scratch** — rejected: duplicates battle-tested logic; violates spec constraint (FR-007).

---

## Decision 3: Obsidian MCP File Operations

**Decision**: Import `atomic_write` and `render_yaml_frontmatter` directly from `watchers/utils.py`.

**Rationale**:
- `atomic_write(filepath, content)` is POSIX-atomic via temp+replace (lines 54–78 of `watchers/utils.py`). Already validated in 385-test suite.
- `render_yaml_frontmatter(fields: dict) -> str` handles pyyaml safe-dump with Unicode support (lines 130–143).
- Spec constraint: "Obsidian MCP MUST reuse `watchers/utils.py` `atomic_write`" (FR-010).

**Other utils to reuse**:
- `sanitize_filename(text)` — for note path sanitization.
- `sanitize_utf8(text)` — for note body content.

**YAML frontmatter parsing** (for `read_note`): use `pyyaml` `safe_load` directly — no new dependency.

---

## Decision 4: stdio Transport (not HTTP/SSE)

**Decision**: Both MCP servers use stdio JSON-RPC transport.

**Rationale**:
- Claude Code registers MCPs as `{"command": "python3", "args": ["mcp-servers/gmail/server.py"]}` — Claude Code spawns the process and communicates over stdin/stdout.
- No network port needed; simpler for WSL2 environment.
- No streaming required (spec constraint: "No streaming tool responses").

**Alternatives Considered**:
- **SSE/HTTP transport** — rejected: adds HTTP server complexity; not needed for local tools; workspace-mcp (already registered) handles the interactive Claude Code session.

---

## Decision 5: Error Handling — Typed Error Objects

**Decision**: Return `CallToolResult(isError=True, content=[TextContent(...)])` with JSON error body — never raise exceptions.

**Error taxonomy** (from spec analysis):
```json
{ "error": "auth_required",   "message": "Run scripts/gmail_auth.py to re-authenticate" }
{ "error": "not_found",       "message": "...", "id": "..." }
{ "error": "rate_limited",    "message": "...", "retry_after": 60 }
{ "error": "permission_denied","message": "Path outside vault root" }
{ "error": "parse_error",     "message": "Corrupt frontmatter", "path": "..." }
```

**Rationale**: MCP protocol requires `isError=True` in `CallToolResult` for tool errors. The SDK also catches unhandled exceptions and wraps them in `_make_error_result()`, but explicit typed errors are testable and document the contract.

---

## Decision 6: Testing Strategy — In-Memory Streams + Mock OAuth

**Decision**:
- **Contract tests**: Use `anyio.streams.memory` to create in-memory send/receive streams; send JSON-RPC requests; assert on response structure.
- **Integration tests**: Mock the OAuth client (`unittest.mock.patch("mcp_servers.gmail.auth.get_gmail_service")`); use temp directory for vault in Obsidian tests.
- **No live Gmail API calls in CI**.

**Rationale**: Consistent with existing test patterns in `tests/` (Phase 2/3 used `MagicMock` for `_service`). Deterministic; fast; no auth overhead.

---

## Decision 7: Orchestrator MCP Wiring — New `mcp_client.py`

**Decision**: Add `orchestrator/mcp_client.py` as a lightweight async MCP tool caller with the fallback protocol.

**Rationale**:
- The fallback protocol (from `ai-control/MCP.md`) requires: attempt MCP → on failure log + execute fallback → if fallback fails escalate.
- Centralizing this in `MCPClient` keeps `_apply_decision()` clean and the fallback independently testable.
- `_apply_decision()` at lines 305–365 of `orchestrator/orchestrator.py` has 5 decision branches, each calling 1–3 `vault_ops` functions. Replacing with MCP calls requires ~30 lines of change.

**Approved draft polling** (new behavior for Phase 4):
- New method `_scan_approved_drafts()` polls `vault/Approved/` for files with `status: pending_approval`.
- Calls Gmail MCP `send_email` → on success moves file to `vault/Done/`.
- Runs in the same poll loop as `scan_pending_emails`.

---

## Decision 8: `mcp` Package Version Pinning

**Decision**: Add `mcp>=1.0.0` to `requirements.txt`.

**Current state**: `mcp` is installed in `.venv` but not declared in `requirements.txt`. This is fragile — a fresh `pip install -r requirements.txt` would not install it.

**Installed version discovery**:
```bash
python3 -c "import mcp; print(mcp.__version__)"
```
Pin to `>=1.0.0` (compatible with current install).

---

## Integration Readiness Summary

| Component | Status | Reuse Strategy |
|-----------|--------|----------------|
| `mcp` SDK | ✅ Installed | `Server`, `stdio_server`, `types` |
| OAuth2 pattern | ✅ Ready | Adapt from `gmail_watcher.py:170-211` |
| `atomic_write` | ✅ Ready | Direct import from `watchers/utils.py` |
| `render_yaml_frontmatter` | ✅ Ready | Direct import from `watchers/utils.py` |
| `_apply_decision` hook | ✅ Mapped | 5 branches → MCP calls + fallback |
| Pydantic models | ✅ Ready | `.model_json_schema()` for tool schemas |
| Test infrastructure | ✅ Ready | `anyio.streams.memory` + mocks |
| `mcp` in requirements.txt | ⚠️ Missing | Add `mcp>=1.0.0` |
