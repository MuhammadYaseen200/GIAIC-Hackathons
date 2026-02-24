# ADR-0006: Gmail OAuth2 Architecture in MCP Context

> **Scope**: Defines how the Gmail MCP server authenticates with the Gmail API — token lifecycle, browser flow policy, singleton pattern, and test mocking strategy.

- **Status:** Accepted
- **Date:** 2026-02-24
- **Feature:** mcp-integration (007)
- **Context:** The Gmail MCP server must authenticate with the Gmail API without opening a browser. The existing `GmailWatcher._authenticate()` (Phase 2, `watchers/gmail_watcher.py:170-211`) implements the complete OAuth2 lifecycle (load → validate → refresh → reauth → atomic save). MCP servers are long-running processes that serve multiple sequential tool calls — per-call authentication would be unacceptably slow. The token was created in HT-002 (human task) and must be reused. The Gmail MCP server runs as a subprocess spawned by Claude Code, meaning there is no terminal available for interactive browser auth.

## Decision

Adapt the **existing `_authenticate()` pattern** from `watchers/gmail_watcher.py` into a standalone `get_gmail_service()` function in `mcp-servers/gmail/auth.py`, with:

- **Singleton service**: Module-level `_gmail_service` variable caches the authenticated `googleapiclient.Resource` after first initialization
- **No browser flow**: If `token.json` is missing or has no refresh token, raise `AuthRequiredError` immediately — never call `flow.run_local_server()` in MCP mode
- **Automatic token refresh**: If token is expired but has a refresh token, call `creds.refresh(Request())` and atomically save via `watchers.utils.atomic_write`
- **Startup warm-up**: Gmail server's FastMCP lifespan calls `get_gmail_service()` at startup; `AuthRequiredError` is caught and surfaced only when a tool is called (server stays alive)
- **Test reset hook**: `reset_service_cache()` function clears the singleton for test isolation
- **Path resolution**: `GMAIL_TOKEN_PATH` and `GMAIL_CREDENTIALS_PATH` env vars (consistent with Phase 2)

## Consequences

### Positive

- **Zero code duplication**: OAuth2 lifecycle logic is identical to Phase 2 — no new auth bugs introduced
- **Fast tool calls**: Service singleton initialized once at startup; subsequent tool calls skip all auth overhead
- **Safe for MCP subprocess mode**: No browser popup risk in `--single-user` or subprocess invocation scenarios
- **Atomic token refresh**: `atomic_write` from `watchers/utils.py` prevents corrupt `token.json` on crash during refresh
- **Testable**: `reset_service_cache()` + `patch("mcp_servers.gmail.auth.get_gmail_service")` gives full mock control without touching the file system
- **Clear error UX**: `AuthRequiredError` message tells users exactly which command to run (`python3 scripts/gmail_auth.py`) — not a traceback

### Negative

- **Singleton is global state**: Module-level `_gmail_service` makes auth state implicit; tests MUST call `reset_service_cache()` between test cases or auth state bleeds across tests
- **No multi-account support**: Singleton assumes one authenticated account per server process — fine for Phase 4 (spec constraint: "no multi-account"), but limits future expansion
- **Refresh failure is fatal**: If refresh fails (revoked token, network error), the entire server rejects all tool calls until re-authenticated — no graceful degradation within the auth subsystem
- **Tight coupling to env vars**: `GMAIL_TOKEN_PATH` must be set before import — if env not loaded, `auth.py` fails at import time; mitigated by `load_dotenv()` call in server.py

## Alternatives Considered

**Alternative A: Re-implement OAuth2 from scratch in auth.py**
- Pros: Independent of `watchers/gmail_watcher.py`; no coupling between `mcp-servers/` and `watchers/`
- Cons: Duplicates battle-tested OAuth2 lifecycle logic; introduces new surface area for token corruption bugs; spec explicitly prohibits this (FR-007: "MUST reuse existing OAuth2 token from token.json")
- Rejected: Violates FR-007; code duplication; unnecessary risk

**Alternative B: Inherit from `GmailWatcher` and expose its `_service`**
- Components: `class GmailMCPAuth(GmailWatcher)` — subclass to access service
- Pros: Direct reuse without copy-paste
- Cons: `GmailWatcher` inherits `BaseWatcher` which brings poll loop, file locking, state management — massive overhead for a simple auth concern; MCP server is not a watcher
- Rejected: ADR-0001 established BaseWatcher for watchers only; MCP servers are a different abstraction

**Alternative C: Per-call authentication (no singleton)**
- Pros: No global state; simpler for testing
- Cons: Every tool call pays ~200ms OAuth overhead (token validation + potential refresh); unacceptable for interactive Claude Code tool calls (FR-018 requires health_check in <3s)
- Rejected: Performance requirement eliminates this approach

**Alternative D: Store credentials in keychain / secrets manager**
- Components: `keyring` library or OS keychain
- Pros: More secure than filesystem token.json; no file permissions risk
- Cons: Adds `keyring` dependency; WSL2 keychain integration is unreliable; token.json is already OS-protected by file permissions; spec says no new auth infrastructure
- Rejected: Spec constraint (FR-007); WSL2 keychain reliability; over-engineered for local single-user deployment

## References

- Feature Spec: `specs/007-mcp-integration/spec.md` (FR-007)
- Implementation Plan: `specs/007-mcp-integration/plan.md` (Phase A)
- Research: `specs/007-mcp-integration/research.md` (D2 — OAuth2 Reuse Pattern)
- Tasks: `specs/007-mcp-integration/tasks.md` (T006 — auth.py full implementation)
- Source: `watchers/gmail_watcher.py:170-211` (`_authenticate()` reference implementation)
- Related ADRs: ADR-0002 (async SDK pattern — `asyncio.to_thread()` used for all Gmail API calls in tools.py)
- Human Tasks: `ai-control/HUMAN-TASKS.md` HT-002 (Gmail OAuth setup — token already created)
