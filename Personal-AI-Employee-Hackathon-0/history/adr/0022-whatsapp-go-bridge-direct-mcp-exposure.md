# ADR-0022: WhatsApp Go Bridge Direct MCP Exposure Architecture

- **Status:** Accepted
- **Date:** 2026-04-11
- **Feature:** full-comms-automation (Phase 6.5)
- **Context:** ADR-0012 defined WhatsApp as using a Go bridge backend abstracted through a
  Python MCP server wrapper (`mcp_servers/whatsapp/server.py`). The Python wrapper had 2
  tools: `send_message` and `health_check`. Phase 6.5 planning initially assumed all media
  and management operations needed to be added to the Python wrapper AND the Go bridge HTTP API.
  However, investigation of the live MCP environment (`.mcp.json` configuration) revealed
  that the Go bridge itself exposes a richer set of tools DIRECTLY as MCP tools, bypassing
  the Python wrapper entirely:
  - `mcp__whatsapp__send_message` (text)
  - `mcp__whatsapp__send_file` (images, videos, documents)
  - `mcp__whatsapp__send_audio_message`
  - `mcp__whatsapp__download_media`
  - `mcp__whatsapp__list_chats`
  - `mcp__whatsapp__list_messages`
  - `mcp__whatsapp__get_chat`
  - `mcp__whatsapp__search_contacts`
  - `mcp__whatsapp__get_contact_chats`
  - `mcp__whatsapp__get_direct_chat_by_contact`
  - `mcp__whatsapp__get_last_interaction`
  - `mcp__whatsapp__get_message_context`
  Two architectural layers now co-exist: (1) Go bridge MCP tools (rich, direct), and
  (2) Python MCP wrapper (thin, 2 tools). Phase 6.5 must decide how to organize tool access.

## Decision

**Use the Go bridge MCP tools directly for all WhatsApp operations that the bridge already
supports. Use the Python MCP wrapper only for operations requiring Python-side business logic
(HITL queueing, rate limiting, PII scrubbing, CEOverified contact gate).** Do NOT duplicate
Go bridge functionality in the Python wrapper.

### Architecture (Two-Layer)

**Layer 1 — Go Bridge MCP Tools (direct, no Python intermediary)**
- Use directly from orchestrators and watchers via `mcp__whatsapp__*` tool calls
- Covers: send_message, send_file, send_audio_message, download_media, list_chats,
  list_messages, get_chat, search_contacts, get_contact_chats, get_last_interaction,
  get_message_context
- Called AFTER HITL approval is confirmed — the bridge does not know about HITL

**Layer 2 — Python Wrapper (`mcp_servers/whatsapp/server.py`) — Business Logic Only**
- `get_unread_summary()`: calls bridge list_chats + list_messages → applies Tier 0
  priority classifier → returns structured summary (PII-masked)
- `save_contact()`: CEO-verified gate → writes to `contacts.db` ContactRecord
- `broadcast()`: enforces ≤10 recipient cap (FR-040) → then calls bridge send_message
- `post_status()`: wraps any future bridge status endpoint (not yet in bridge)
- `create_group()`: wraps any future bridge group endpoint (not yet in bridge)

### Missing Bridge Capabilities (extend Go bridge HTTP API for Phase D)
The following are NOT in the current bridge and require Go code extension:
- `POST /status` — post WhatsApp Status (text or media)
- `POST /group` — create group with name, members, description
- `GET /profile` — get own profile info (for profile management FR-010)

These three endpoints are the only Go code changes needed. All other operations (media
send, contact search, message history) already exist.

### HITL Integration Pattern
All send operations follow this invariant:
```
HITL approved → orchestrator calls mcp__whatsapp__send_message (or send_file)
```
The HITL queue (ADR-0021) holds the action. On approval, `execute_approved()` calls
the appropriate bridge MCP tool directly. The bridge never decides whether to send —
it only executes confirmed sends.

## Consequences

### Positive
- **Minimal Go code changes**: Only 3 new HTTP endpoints needed vs originally feared full
  media rewrite. 80% of Phase D (media send, contact search, message history) is already
  done in the bridge.
- **No Python wrapper duplication**: `mcp_servers/whatsapp/server.py` stays thin and focused
  on business logic (HITL, rate limiting, PII). Bridge handles raw protocol operations.
- **Immediate capability gain**: `send_file`, `send_audio_message`, `search_contacts`,
  `list_messages` are available NOW — Phase D starts from a much stronger baseline.
- **Separation of concerns**: Protocol (Go bridge) vs Business rules (Python wrapper).
  Changes to Go bridge don't require Python changes and vice versa.

### Negative
- **Two tool namespaces**: `mcp__whatsapp__*` (bridge) and Python MCP tools exist in parallel.
  Developers must know which layer to call. Mitigation: document in quickstart.md which
  tool to use for each operation type.
- **Go bridge is external binary**: Cannot unit-test Python code against it without a running
  bridge. Bridge tool calls must be mocked in unit tests. Contract tests require a live bridge.
- **Status and Group features blocked**: Three missing bridge endpoints (status, group, profile)
  require Go code contribution to `~/whatsapp-mcp/whatsapp-bridge/`. If bridge maintainer
  doesn't accept changes, these features are blocked.
- **Bridge version drift**: If bridge updates its API, both Python wrapper and orchestrator
  code may need updates. Mitigation: pin bridge binary version in setup docs.

## Alternatives Considered

**Alternative A: Rewrite all WhatsApp ops through Python wrapper (ignore bridge MCP tools)**
- Add all 12+ bridge capabilities to Python wrapper as pass-through wrappers
- Rejected: Creates ~300 lines of boilerplate wrappers that add zero business logic.
  Violates DRY principle. Bridge MCP tools are already available — use them directly.

**Alternative B: Replace Go bridge with Python-native WhatsApp library**
- Use `pywa` (Meta Cloud API) or `whatsapp-chatbot-python` for all operations
- Rejected: pywa requires Meta Business verification + webhook hosting (HT-012 pending
  since Phase 5, still blocked). Python-native Web Protocol libraries are unstable and
  get banned. ADR-0012 already established Go bridge as primary — it's stable and
  authenticated.

**Alternative C: Single unified Python MCP server wrapping all bridge calls**
- One Python MCP server that wraps ALL bridge operations (no direct bridge tool calls)
- Rejected: Contradicts the finding that bridge MCP tools are already available and well-
  tested. Adding a Python pass-through layer for 12 already-working tools is unnecessary
  complexity. Only add Python layer where business logic (HITL, rate limiting) is needed.

## References

- Feature Spec: `specs/011-full-comms-automation/spec.md` (FR-001 through FR-010)
- Implementation Plan: `specs/011-full-comms-automation/plan.md` (Phase D)
- Research: `specs/011-full-comms-automation/research.md` (Section 1: WhatsApp MCP)
- Supersedes: ADR-0012 §Python Wrapper Scope (extends, not supersedes — bridge selection
  from ADR-0012 is preserved; this ADR clarifies the two-layer tool access pattern)
- Related ADRs: ADR-0012 (backend selection), ADR-0021 (HITL queue), ADR-0010 (privacy gate)
