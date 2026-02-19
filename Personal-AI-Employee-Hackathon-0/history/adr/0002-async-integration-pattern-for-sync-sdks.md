# ADR-0002: Async Integration Pattern for Sync SDKs

> **Scope**: Defines how synchronous third-party SDKs (starting with google-api-python-client) are integrated into the async watcher architecture.

- **Status:** Accepted
- **Date:** 2026-02-17
- **Feature:** gmail-watcher (005)
- **Context:** Constitution prohibits synchronous blocking I/O in watchers ("No synchronous blocking I/O in watchers; use async"). However, the Gmail Python SDK (`google-api-python-client`) is entirely synchronous. The Gmail MCP server is not yet operational (MCP.md status: "Needed #1"), so the MCP Fallback Protocol authorizes direct SDK usage. We need a pattern to bridge sync SDK calls into the async watcher lifecycle without blocking the event loop.

## Decision

Use **`asyncio.to_thread()`** to wrap all synchronous Gmail API calls, keeping the main watcher loop fully async with `asyncio.sleep()` for poll intervals.

Components:
- **Poll loop**: `async def start()` uses `await asyncio.sleep(poll_interval)` between cycles
- **SDK calls**: All `google-api-python-client` calls wrapped in `await asyncio.to_thread(sync_function, *args)`
- **Signal handling**: `asyncio.get_event_loop().add_signal_handler()` for SIGINT/SIGTERM graceful shutdown
- **Thread safety**: Each `to_thread()` call gets its own thread from the default executor; no shared mutable state between threads
- **Future migration**: When Gmail MCP becomes operational (Phase 4), the `to_thread()` calls are replaced with MCP tool calls -- same async interface, different backend

## Consequences

### Positive

- Fully compliant with Constitution's async mandate without replacing the well-documented, stable Gmail SDK
- Main event loop remains responsive -- future multi-watcher concurrency (GmailWatcher + CalendarWatcher running in same process) works naturally via `asyncio.gather()`
- `asyncio.to_thread()` is stdlib (Python 3.9+), zero additional dependencies
- Clean migration path to async MCP calls: replace `await asyncio.to_thread(sync_call)` with `await mcp_tool_call()` -- same `await` pattern
- Signal handling (Ctrl+C) works correctly with async loop

### Negative

- Thread pool overhead: each Gmail API call spawns a thread (negligible for 1-2 calls per 60s poll, but could matter with 10+ watchers)
- Error propagation from threads requires care -- exceptions in `to_thread()` propagate correctly but stack traces may be less clear
- Cannot cancel in-flight sync SDK calls -- `to_thread()` doesn't support cancellation of the underlying blocking call
- Two concurrency models in one process (asyncio + threads) increases cognitive complexity

## Alternatives Considered

**Alternative A: Fully synchronous watcher with `time.sleep()`**
- Pros: Simplest implementation, no async complexity
- Cons: Violates Constitution; blocks entire process; no multi-watcher concurrency; signal handling is unreliable during `time.sleep()`
- Rejected: Direct Constitution violation, blocks future multi-watcher architecture

**Alternative B: `aiohttp` + raw Gmail REST API**
- Pros: Fully async, no threads, native cancellation
- Cons: Must reimplement all Gmail API logic (pagination, auth, MIME parsing) that the SDK provides; much larger implementation surface; more bugs; no Google-supported error handling
- Rejected: Reinventing the wheel -- the SDK handles edge cases we'd miss

**Alternative C: `run_in_executor()` with custom ThreadPoolExecutor**
- Pros: Control over thread pool size and naming
- Cons: `to_thread()` is the modern equivalent (Python 3.9+) with cleaner API; custom executor is premature optimization for 1-2 API calls per minute
- Rejected: `to_thread()` is sufficient and simpler; can switch to custom executor later if needed

**Alternative D: Subprocess-based SDK execution**
- Pros: Complete isolation, can kill hanging processes
- Cons: Massive overhead (process spawn per poll), complex IPC for results, credential passing complexity
- Rejected: Overkill for wrapping a few HTTP calls

## References

- Feature Spec: `specs/005-gmail-watcher/spec.md` (Performance Limits, MCP Fallback Protocol)
- Implementation Plan: `specs/005-gmail-watcher/plan.md`
- Related ADRs: ADR-0001 (BaseWatcher defines the async lifecycle this pattern serves)
- Constitution: `.specify/memory/constitution.md` ("No synchronous blocking I/O in watchers; use async")
- MCP.md: `ai-control/MCP.md` (Gmail MCP status: Needed #1, Fallback Protocol)
