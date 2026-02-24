# ADR-0007: MCP Fallback Protocol and Orchestrator Wiring

> **Scope**: Defines how the RalphWiggumOrchestrator calls MCP tools, handles MCP server unavailability, and maintains operational continuity via a fallback chain.

- **Status:** Accepted
- **Date:** 2026-02-24
- **Feature:** mcp-integration (007)
- **Context:** Constitution Principle X mandates graceful degradation. The spec (FR-015, FR-016) requires every MCP tool call in the orchestrator to be wrapped with the fallback protocol: attempt MCP → on failure log error → execute fallback → if fallback fails, escalate. The orchestrator's `_apply_decision()` currently calls `vault_ops.py` functions directly (5 decision branches, ~30 calls). Phase 4 replaces these with MCP calls while preserving the existing test suite (385 passing tests) and the `vault_ops.py` fallback path. The MCP servers run as subprocesses; a subprocess failure (startup crash, timeout) must never crash the orchestrator.

## Decision

Introduce a dedicated **`MCPClient` class** (`orchestrator/mcp_client.py`) implementing the fallback protocol as a reusable component, and refactor `_apply_decision()` to call vault operations through `MCPClient.call_tool()` with `vault_ops` functions as fallback callables.

Components:
- **`MCPClient(server_name, command, vault_path)`**: Encapsulates subprocess invocation, timeout handling, and the fallback chain for a single MCP server
- **`call_tool(tool_name, args, fallback=None, timeout=30.0)`**: Single entry point for all tool calls; implements the 3-step protocol:
  1. Attempt: Spawn subprocess, send JSON-RPC init + tool call, parse response
  2. On failure (exception, timeout, `isError=True`): log `mcp_fallback` event to `vault/Logs/mcp_fallback_{date}.jsonl` → run `fallback()` callable
  3. On fallback failure: log `mcp_escalation` → raise `MCPUnavailableError`
- **Fallback callables**: Lambda functions wrapping existing `vault_ops.py` functions (e.g., `lambda: move_to_done(filepath, done_dir)`)
- **Approved draft send loop**: New `_scan_approved_drafts()` + `_send_approved_draft()` methods in orchestrator; Gmail `MCPClient` with `fallback=lambda: log_and_keep_in_approved()` (cannot fall back to direct send — no sync Gmail API in orchestrator)
- **Dual MCPClient instances**: `self._gmail_mcp` + `self._obsidian_mcp` in orchestrator `__init__`; command paths from env vars
- **JSONL audit trail**: All fallback and escalation events logged with server, tool, error, timestamp — no silent failures

## Consequences

### Positive

- **SRP compliance**: Fallback protocol logic isolated in `MCPClient` — `_apply_decision()` reads as business logic, not infrastructure
- **Independently testable**: `MCPClient.call_tool()` unit tests cover fallback/escalation without touching orchestrator logic; orchestrator tests mock `MCPClient` entirely
- **Zero regression**: Existing 385 tests pass because the fallback path calls the same `vault_ops.py` functions as before — MCPClient is transparent when MCP is down
- **Operational safety**: `vault_ops.py` fallback ensures vault notes are processed even when MCP servers fail to start (e.g., missing Python env, port conflicts)
- **Audit compliance**: Every MCP failure creates a JSONL log entry — Constitution Principle IX requires pre-action logging for all external actions
- **Timeout protection**: 30-second `asyncio.wait_for` prevents subprocess hangs from blocking the orchestrator poll loop
- **Future-proof**: When a proper async MCP client library stabilizes, `MCPClient._invoke_tool()` can be replaced without changing `_apply_decision()` call sites

### Negative

- **Subprocess overhead**: Each `call_tool()` spawns a new subprocess (init handshake + tool call + terminate) — ~100-300ms overhead vs. direct `vault_ops` call; acceptable for ~100 emails/day, not for high-throughput
- **Simplified client**: The `MCPClient._invoke_tool()` implements a minimal JSON-RPC client (not a full MCP client session with capability negotiation) — works for tool calls but lacks resource subscriptions, progress reporting
- **Gmail fallback gap**: `send_email` has no meaningful fallback — approved draft stays in `vault/Approved/` for retry. This is intentional (HITL principle: never silently skip a send) but means email sends are unavailable when Gmail MCP is down
- **Subprocess test complexity**: Unit tests for `MCPClient._invoke_tool()` must mock `asyncio.create_subprocess_exec` — slightly complex mock setup

## Alternatives Considered

**Alternative A: Inline MCP calls directly in `_apply_decision()`**
- Pros: No new abstraction; simpler file structure
- Cons: Fallback protocol repeated 10+ times in `_apply_decision()`; mixing infrastructure (MCP) with business logic (decisions); impossible to unit test fallback independently
- Rejected: SRP violation; code duplication; poor testability

**Alternative B: Use official async MCP client library for session-based connection**
- Components: `mcp.ClientSession` + `mcp.StdioServerParameters` — persistent session kept alive across multiple tool calls
- Pros: Proper MCP session lifecycle; capability negotiation; resource subscriptions available; no per-call subprocess spawn
- Cons: MCP Python client library for persistent connections had instability at time of Phase 4 development; session management adds lifecycle complexity (startup, reconnect, shutdown); session failure would require reconnect logic adding even more complexity
- Rejected: Stability concerns; our subprocess-per-call approach is simpler and sufficient for ~100 emails/day; can migrate to session-based when the client SDK matures

**Alternative C: Keep `vault_ops.py` calls directly, no MCP wiring in orchestrator**
- Pros: Zero change to `_apply_decision()`; no new complexity; all 385 tests pass trivially
- Cons: Violates spec exit criteria (US4, FR-015, FR-016); violates Constitution Principle IV (all external actions must route through MCP)
- Rejected: Spec requirement; Constitution compliance; defeats the purpose of Phase 4

**Alternative D: MCP-only (no fallback to `vault_ops.py`)**
- Pros: Forces MCP adoption; removes dual-path complexity
- Cons: Violates spec (FR-015: "every MCP tool call MUST be wrapped with fallback protocol"); orchestrator crashes when Obsidian MCP is unavailable; breaks existing test patterns
- Rejected: Spec violation; fragility; Constitution Principle X (Graceful Degradation) explicitly requires fallback

## References

- Feature Spec: `specs/007-mcp-integration/spec.md` (FR-015, FR-016, US4, SC-003)
- Implementation Plan: `specs/007-mcp-integration/plan.md` (Phase C)
- Research: `specs/007-mcp-integration/research.md` (D7 — MCPClient design)
- Tasks: `specs/007-mcp-integration/tasks.md` (T009, T014, T015, T016, T025, T026, T027)
- Related ADRs: ADR-0002 (async pattern — MCPClient uses asyncio.create_subprocess_exec), ADR-0003 (JSONL logging — mcp_fallback.jsonl follows same format)
- MCP Registry: `ai-control/MCP.md` (fallback protocol specification)
- Constitution: `.specify/memory/constitution.md` Principle IV (MCP-First), Principle X (Graceful Degradation)
