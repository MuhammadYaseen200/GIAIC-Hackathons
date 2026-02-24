# ADR-0008: Typed MCP Error Contract and Taxonomy

> **Scope**: Defines how all MCP tool errors are represented, structured, and distinguished from success responses across both Gmail and Obsidian MCP servers.

- **Status:** Accepted
- **Date:** 2026-02-24
- **Feature:** mcp-integration (007)
- **Context:** MCP tools can return results in two ways: as structured data (success) or as `CallToolResult(isError=True, content=[...])` (error). Without a consistent error structure, the orchestrator cannot programmatically distinguish error types (auth failure vs. rate limit vs. not-found) to implement the correct fallback behavior. FastMCP catches unhandled exceptions and wraps them generically; this loses error type information. The spec requires "All tools MUST return structured JSON responses — never raw exception tracebacks" (FR-006, FR-014). Twelve tools across two servers must all follow the same error contract to enable the MCPClient fallback protocol.

## Decision

Define a **shared `MCPError` Pydantic model** with a **typed `MCPErrorCode` literal** in each server's `models.py`, and return errors as `json.dumps(MCPError(...).model_dump())` — never as raised exceptions reaching the MCP framework.

Components:
- **`MCPErrorCode`**: `Literal[...]` with 8 named codes covering all failure modes: `auth_required`, `not_found`, `rate_limited`, `send_failed`, `permission_denied`, `parse_error`, `mcp_unavailable`, `internal_error`
- **`MCPError` model**: `{error: MCPErrorCode, message: str, details: dict | None}` — same shape in both Gmail and Obsidian servers
- **Return shape**: All tools return `str` (JSON); errors are `json.dumps({"error": code, "message": "...", "details": {...}})` — same `str` return type as success; no isError flag needed at tool level
- **No exception propagation**: Every tool handler wraps its entire body in `try/except`; specific exception types mapped to specific error codes (e.g., `HttpError status 429` → `rate_limited`, `FileNotFoundError` → `not_found`)
- **MCPClient error detection**: `MCPClient._invoke_tool()` checks `result.get("error")` in returned dict — error detected by presence of `"error"` key, not by `isError` flag
- **Contract tests**: Each error code is independently tested in `tests/contract/` — any tool returning a non-contract error shape is caught immediately

## Consequences

### Positive

- **Programmatic error handling**: Orchestrator and Claude Code agents can `if result.get("error") == "auth_required":` — no string matching against error messages
- **No traceback exposure**: Raw Python exceptions never reach the MCP protocol boundary — users/agents never see `AttributeError`, `KeyError`, etc.
- **Consistent across 10+ tools**: `MCPError` shape is identical in Gmail and Obsidian servers — agents learn one error format for the entire system
- **Contract-testable**: `tests/contract/` tests the error shape independently of tool logic — breaking the error format is caught without integration test overhead
- **Actionable error messages**: Each error code has a prescribed message format that guides recovery (e.g., `auth_required` always includes the re-auth command)
- **Future servers**: Phase 5+ MCP servers (WhatsApp, Calendar) adopt the same error taxonomy — consistent error handling in the orchestrator across all tools

### Negative

- **Two separate `models.py` files**: Gmail and Obsidian each define `MCPError` and `MCPErrorCode` — technically duplicate model definitions (intentionally kept separate for server independence)
- **No HTTP analogy**: Unlike REST APIs, MCP tools return 200 (success at protocol level) for both tool success and tool errors — callers must check for `"error"` key, not HTTP status. This is MCP-idiomatic but different from REST conventions
- **`internal_error` catch-all**: Generic exception → `internal_error` mapping hides unexpected bugs behind a generic code. Mitigated by logging the original exception before returning the error object

## Alternatives Considered

**Alternative A: Raise exceptions and let FastMCP convert them**
- Components: Raise Python exceptions; FastMCP calls `_make_error_result(str(e))` and returns `CallToolResult(isError=True)`
- Pros: Less boilerplate; exception types self-document failure modes
- Cons: Exception string in `content[0].text` has no schema — cannot programmatically distinguish `AuthRequiredError` from `FileNotFoundError`; traceback may be exposed in message; no `details` field for structured metadata (e.g., `retry_after`)
- Rejected: Spec FR-006, FR-014 requires "typed error objects — never raw exception tracebacks"; orchestrator needs structured error codes for fallback decisions

**Alternative B: Use HTTP-style status codes in the response dict**
- Components: `{"status": 404, "error": "message"}` — HTTP-style numeric codes
- Pros: Familiar to REST developers; widely understood
- Cons: MCP is not HTTP; no benefit of HTTP routing/middleware; clients must maintain code→meaning mapping; `MCPErrorCode` literal strings are more readable and grep-able (`"not_found"` vs. `404`)
- Rejected: MCP-idiomatic approach is string error codes; Pydantic literal strings provide better IDE support and readability

**Alternative C: Separate success and error response shapes (union type)**
- Components: `SuccessResponse | ErrorResponse` union type; FastMCP `outputSchema` validation
- Pros: Type-safe at schema level; outputSchema validation catches wrong response shapes
- Cons: FastMCP `outputSchema` validation adds complexity; union type JSON Schema with `oneOf` is harder to validate in tests; all 10 tools must define both shapes
- Rejected: Simpler to use presence of `"error"` key as discriminator; `str` return type with JSON is already established in the FastMCP pattern

**Alternative D: Use MCP `isError` flag only (no structured error body)**
- Components: Return `CallToolResult(isError=True, content=[TextContent(text=message)])`
- Pros: Native MCP protocol error signaling; clients know to treat response as error
- Cons: Message is unstructured text — no programmatic error code; cannot distinguish `auth_required` from `not_found` without string parsing; loses `details` field for metadata
- Rejected: Insufficient for fallback protocol which needs error code discrimination; we already return `str` JSON — combining `isError=True` with JSON body is redundant complexity

## References

- Feature Spec: `specs/007-mcp-integration/spec.md` (FR-006, FR-014, US2 AS-3, US2 AS-4, US3 AS-4)
- Data Model: `specs/007-mcp-integration/data-model.md` (Error Taxonomy section, MCPError model)
- Contracts: `specs/007-mcp-integration/contracts/gmail-tools.json` (errorSchema), `contracts/obsidian-tools.json` (errorSchema)
- Tasks: `specs/007-mcp-integration/tasks.md` (T007, T008, T012, T019, T022 — contract test tasks)
- Related ADRs: ADR-0007 (MCPClient error detection uses `result.get("error")` key)
- Constitution: `.specify/memory/constitution.md` Principle IX (Security — no traceback exposure)
