# ADR-0023: MCP In-Place Extension Pattern for Phase 6.5

- **Status:** Accepted
- **Date:** 2026-04-11
- **Feature:** full-comms-automation (Phase 6.5)
- **Context:** Phase 6.5 adds 35+ new tools across 5 existing MCP servers (Gmail, Calendar,
  LinkedIn, Facebook/Instagram, Twitter/WhatsApp). Each server currently handles a narrow
  write-only (social posting) or read-only (calendar) scope. The question is: how should
  these new tools be organized? Three options exist: (1) extend the existing server files
  in-place, (2) create new MCP server files per capability group, or (3) build a single
  unified "communications MCP" that aggregates all platforms. The decision affects:
  - How MCP tools are discovered by the orchestrator and Claude
  - Whether existing tool contracts (ADR-0008 typed error contract) are preserved
  - How tests are organized (each server has its own contract test file)
  - Whether server startup/health check complexity grows
  - Whether MCP registration in `ai-control/MCP.md` needs major updates
  Phase 6.5 is also the phase where the system transitions from "posting only" to
  "full read/write/manage" — a fundamentally larger surface area per server.

## Decision

**Extend all existing MCP server files in-place.** Add new tools directly to
`mcp_servers/<platform>/server.py` rather than creating new server files. For capabilities
that require a significant access gate (LinkedIn DMs), create a single new sibling file
within the same package (`dm_server.py`) rather than a new MCP server registration.

### Extension Rules (applied per server)

**Rule 1: Add tools to existing server.py**
New tools for an existing platform are added to that platform's `server.py`. Server remains
a single FastMCP instance. Tool names follow existing conventions: `verb_noun` (e.g.,
`create_event`, `update_profile`, `list_comments`).

**Rule 2: Gated capabilities in sibling files**
When a capability requires a separate env variable gate (LinkedIn Messaging API key,
Twitter Basic tier), implement it in a sibling file (`dm_server.py`) and import conditionally:
```python
# In server.py:
if os.getenv("LINKEDIN_MESSAGING_API_KEY"):
    from .dm_server import register_dm_tools
    register_dm_tools(mcp)
```
This keeps the primary server healthy even when gated features are unavailable.

**Rule 3: Tool function signature consistency**
All new tools follow ADR-0008 typed error contract:
- Input: Pydantic model (not raw kwargs)
- Output: JSON string (for MCP protocol compatibility)
- Errors: typed exceptions from platform error taxonomy

**Rule 4: Shared business logic in new modules**
Cross-platform logic (rate limiter, model router, privacy gate) lives in new shared modules
(`classifiers/`, `orchestrator/hitl_queue.py`) — NOT in individual server files. Servers
call shared modules; they do not duplicate logic.

### Per-Server Extension Summary
- `mcp_servers/gmail/server.py`: +6 tools (create_draft, send_draft, trash_emails,
  classify_inbox, get_attachment_flags, send_auto_reply, get_daily_summary)
- `mcp_servers/calendar/server.py`: +5 tools (create_event, update_event, delete_event,
  check_conflicts, create_focus_block, extract_event_from_email)
- `mcp_servers/linkedin/server.py`: +11 tools (update_profile_field, get_analytics,
  react_post, comment_post, save_post, list_pending_connections, accept_connection,
  reject_connection, send_connection_request, search_profiles, follow_profile)
- `mcp_servers/linkedin/dm_server.py`: +3 tools GATED (list_conversations, send_dm,
  classify_dm_intent)
- `mcp_servers/facebook/server.py`: +7 tools (list_comments, reply_comment, hide_comment,
  list_dms, reply_dm, get_page_analytics, classify_dm_intent)
- `mcp_servers/twitter/server.py`: +6 tools (reply_tweet, like_tweet, follow_user,
  unfollow_user, get_tweet_analytics, list_dms GATED)
- `mcp_servers/whatsapp/server.py`: +5 tools (get_unread_summary, save_contact, broadcast,
  post_status, create_group) — bridge MCP tools used directly per ADR-0022

## Consequences

### Positive
- **No new MCP registrations**: `ai-control/MCP.md` entries and `.mcp.json` configs are
  unchanged — existing server processes just expose more tools on the same endpoints
- **Existing tests still pass**: Phase 6.5 additions are additive; no existing tool is
  modified or removed. Phase 5/6 test suite runs unchanged.
- **Single server process per platform**: No orchestration of multiple processes per platform.
  Simpler startup, simpler health checks, simpler cron management.
- **Contract tests map 1:1 to servers**: `tests/contract/test_gmail_contracts.py` covers all
  Gmail tools (old + new). No need for new test file per new tool group.
- **Tool discovery is natural**: Orchestrator calls `mcp__gmail__classify_inbox` the same
  way it calls `mcp__gmail__list_emails` — same server, same transport, same auth.

### Negative
- **Server files grow larger**: Gmail server will have ~13 tools after Phase 6.5. LinkedIn
  will have ~15 tools. Long files require discipline to keep organized (section comments,
  consistent ordering: health → read → write → admin).
- **Mixed read/write in one file**: Easier to accidentally call a write tool in a test
  context. Mitigation: write tools check `ALLOW_WRITES=true` env var in test mode.
- **Gated sibling file import**: Conditional import of `dm_server.py` is slightly unusual
  Python pattern. Developers may not immediately understand why some tools appear/disappear.
  Mitigation: comment in server.py explains gate condition; quickstart.md documents env vars.
- **No capability isolation**: A bug in one platform's new tool could crash the entire server
  process, taking down existing tools too. Mitigation: FastMCP error handling per tool (each
  tool has its own try/except — server does not crash on tool error per ADR-0007).

## Alternatives Considered

**Alternative A: New MCP server per capability group**
- E.g., `mcp_servers/gmail_write/`, `mcp_servers/gmail_drafts/`, `mcp_servers/linkedin_analytics/`
- Rejected: Creates 8+ new server registrations in `.mcp.json`. Each needs its own process,
  health check, OAuth token, and contract test. Overhead massively outweighs benefits for
  a single-user system. Tool discovery becomes confusing (which gmail server has which tool?).

**Alternative B: Single unified "communications" MCP**
- One new `mcp_servers/communications/` server that aggregates all 35+ new tools
- Rejected: Breaks the platform-per-server organization that ADR-0005 established. Mixing
  Gmail, LinkedIn, and Twitter tools in one server makes auth management (each platform has
  different OAuth token) extremely complex. Also loses the clean separation of concerns
  (platform-specific error handling, rate limiting, token refresh).

**Alternative C: Orchestrator calls platform APIs directly (bypass MCP for write ops)**
- New write operations call Google/LinkedIn/Twitter APIs directly in orchestrator code,
  bypassing MCP entirely
- Rejected: Constitution Principle IV (MCP-First External Actions) explicitly prohibits
  direct API calls from orchestrator. ADR-0005 established MCP as the required abstraction.
  Bypassing MCP breaks testability (can't mock direct API calls as cleanly as MCP tools).

## References

- Feature Spec: `specs/011-full-comms-automation/spec.md` (all FRs)
- Implementation Plan: `specs/011-full-comms-automation/plan.md` (Phases B, C, E, F)
- Contracts: `specs/011-full-comms-automation/contracts/` (all 5 contract files)
- Related ADRs: ADR-0005 (MCP framework stack), ADR-0007 (MCP fallback protocol),
  ADR-0008 (typed MCP error contract), ADR-0022 (WhatsApp two-layer architecture)
