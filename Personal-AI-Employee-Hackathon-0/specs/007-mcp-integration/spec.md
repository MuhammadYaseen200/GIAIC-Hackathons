# Feature Specification: MCP Integration — Phase 4

**Feature Branch**: `007-mcp-integration`
**Created**: 2026-02-23
**Status**: Complete ✅
**Phase**: 4 (MCP Integration)
**Input**: Phase 4 of H0 Personal AI Employee — build Gmail MCP server and Obsidian MCP server; wire RalphWiggumOrchestrator to use MCPs for all external actions; register both servers in Claude Code settings.

---

## Governance Alignment

> **Managed by**: [`ai-control/AGENTS.md`](../../Personal-AI-Employee-Hackathon-0/ai-control/AGENTS.md)

| Document | Principles Applied | Reference |
|----------|--------------------|-----------|
| Constitution | I (Spec-First), II (Local-First), III (HITL), IV (MCP-First External Actions), VII (Phase-Gated), IX (Security), X (Graceful Degradation) | `.specify/memory/constitution.md` |
| LOOP.md | Loop 1 (Spec-Driven), Loop 3 (HITL), Loop 4 (Directory Guard) | `ai-control/LOOP.md` |
| MCP.md | Gmail MCP (CRITICAL), Obsidian MCP (HIGH) — Needed MCP Servers table | `ai-control/MCP.md` |
| AGENTS.md | Backend-Builder (MCP impl), Modular-AI-Architect (design), QA-Overseer (gate) | `ai-control/AGENTS.md` |
| SWARM.md | Phase 4 config: Fan-Out (one MCP per parallel track) | `ai-control/SWARM.md` |
| HUMAN-TASKS.md | HT-002 (Gmail OAuth — DONE), HT-005 (MCP config registration — PENDING) | `ai-control/HUMAN-TASKS.md` |

---

## Phase 4 Entry / Exit Criteria

Per Constitution Principle VII, Phase 4 MUST NOT begin until Phase 3 exit criteria are met, and Phase 5 MUST NOT begin until Phase 4 exit criteria are met.

### Entry Criteria (from Phase 3) — VERIFIED ✅

- [x] RalphWiggumOrchestrator reads `vault/Needs_Action/` and applies 5 decision types
- [x] 385/385 tests pass, 97% orchestrator/ coverage
- [x] LLM provider abstraction supports 7 providers via `.env` config only
- [x] Draft replies written to `vault/Drafts/`, frontmatter updated atomically
- [x] Every decision logged to `vault/Logs/` with full JSONL audit trail
- [x] Phase 3 spec marked Complete, overview.md updated — 2026-02-23

### Exit Criteria (for Phase 4) — COMPLETE ✅

- [x] Gmail MCP server exposes tools: `send_email`, `list_emails`, `get_email`, `move_email`, `add_label`
- [x] Obsidian MCP server exposes tools: `read_note`, `write_note`, `list_notes`, `move_note`, `search_notes`
- [x] RalphWiggumOrchestrator routes all external actions (email send, vault write) through MCP tools
- [x] Both MCP servers registered and loadable in Claude Code settings (see HT-005 in HUMAN-TASKS.md)
- [x] MCP fallback protocol: if MCP unavailable, log error + write to `vault/Logs/`, never silently skip
- [x] Contract tests pass for all MCP tools (input schema, output schema, error responses)
- [x] Integration tests pass with mock MCP responses (no live Gmail calls required)
- [x] QA-Overseer validates all acceptance scenarios — 460/460 tests pass

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — AI Employee Sends an Approved Draft Reply via Gmail (Priority: P1)

The CEO approves a draft reply in `vault/Drafts/`. The orchestrator detects the approval, calls the Gmail MCP `send_email` tool, and logs the outcome. The CEO never has to open Gmail manually for routine replies.

**Why this priority**: This is the primary value unlock of Phase 4. Without it, every `draft_reply` decision produced in Phase 3 sits in `vault/Drafts/` with no execution path. Sending approved emails is the first real-world action the AI Employee takes.

**Independent Test**: Can be tested end-to-end by placing an approved draft in `vault/Approved/`, running the orchestrator, and verifying a `send_email` MCP tool call is made with the correct `to`, `subject`, and `body`. No actual Gmail connection needed — mock the MCP.

**Acceptance Scenarios**:

1. **Given** a draft reply at `vault/Drafts/reply-001.md` with `status: pending_approval`, **When** the CEO moves it to `vault/Approved/`, **Then** the orchestrator calls `send_email` with the correct recipient, subject, and body within the next poll cycle.
2. **Given** `send_email` succeeds, **When** the tool returns success, **Then** the source email in `vault/Needs_Action/` is moved to `vault/Done/` and the log entry `email_sent` is written to `vault/Logs/`.
3. **Given** `send_email` fails (MCP unavailable or Gmail API error), **When** the error occurs, **Then** the draft is NOT deleted, the error is logged to `vault/Logs/` with severity=error, and the draft remains in `vault/Approved/` for retry.
4. **Given** a draft marked `status: rejected` by the CEO, **When** the orchestrator polls, **Then** the draft is archived to `vault/Done/` with decision=rejected and `send_email` is NOT called.

---

### User Story 2 — Claude Code Agent Uses Gmail MCP to Read and Act on Emails (Priority: P2)

A Claude Code agent (running in this project session) can call `list_emails` and `get_email` MCP tools directly — without knowing about OAuth, token.json, or Gmail API internals. The MCP server abstracts all authentication.

**Why this priority**: Per Constitution Principle IV, ALL external interactions must be routed through MCP. Currently the GmailWatcher calls Gmail API directly. Wrapping it as an MCP enables any agent in the system to read emails in a tool-native way — enabling future agents (WhatsApp watcher coordinator, CEO briefing generator) to access email data.

**Independent Test**: Can be tested by calling `list_emails` tool and verifying it returns a list of email objects with `id`, `subject`, `from`, `date`, `snippet` fields. Mock the underlying OAuth client.

**Acceptance Scenarios**:

1. **Given** the Gmail MCP server is running and `token.json` exists, **When** an agent calls `list_emails(query="is:unread", max_results=10)`, **Then** it returns up to 10 unread email summaries with required fields.
2. **Given** a valid `message_id`, **When** an agent calls `get_email(message_id="...")`, **Then** it returns the full email with `subject`, `from`, `to`, `date`, `body`, `has_attachments` fields.
3. **Given** `token.json` is expired or missing, **When** any tool is called, **Then** the MCP returns a structured error `{"error": "auth_required", "message": "Run scripts/gmail_auth.py to re-authenticate"}` — no crash, no traceback exposed.
4. **Given** Gmail API rate limit is hit, **When** a tool call is made, **Then** the MCP returns `{"error": "rate_limited", "retry_after": <seconds>}` and logs to `vault/Logs/`.

---

### User Story 3 — Obsidian Vault MCP Enables Any Agent to Read and Write Notes (Priority: P3)

Any agent can call `read_note`, `write_note`, `list_notes`, `move_note` without knowing about file paths, YAML frontmatter parsing, or atomic write patterns. The MCP server abstracts all vault file operations.

**Why this priority**: The orchestrator currently writes vault files via direct Python file I/O (`vault_ops.py`). Wrapping vault operations as an MCP means future agents (Phase 5 HITL approval workflow, Phase 6 CEO briefing) can interact with the vault in a tool-native, schema-validated way — consistent with Constitution Principle IV.

**Independent Test**: Can be tested by calling `write_note` with a test file path and YAML frontmatter dict, then calling `read_note` on the same path and verifying the content round-trips correctly.

**Acceptance Scenarios**:

1. **Given** the Obsidian MCP server is running, **When** an agent calls `write_note(path="vault/Needs_Action/test.md", frontmatter={...}, body="...")`, **Then** the file is written atomically and `read_note` on the same path returns identical content.
2. **Given** a note exists, **When** an agent calls `move_note(source="vault/Needs_Action/email.md", destination="vault/Done/email.md")`, **Then** the file is moved and no longer present at the source path.
3. **Given** `list_notes(directory="vault/Needs_Action", filter="status:pending")`, **When** called, **Then** returns a list of file paths matching the filter.
4. **Given** a path that does not exist, **When** `read_note` is called, **Then** returns `{"error": "not_found", "path": "<path>"}` — no FileNotFoundError traceback exposed.

---

### User Story 4 — Orchestrator Uses MCPs Instead of Direct File I/O (Priority: P4)

The RalphWiggumOrchestrator's `_apply_decision()` method calls Obsidian MCP tools instead of calling `vault_ops.py` functions directly. Gmail send actions route through the Gmail MCP.

**Why this priority**: This wires the Phase 3 brain to the Phase 4 tools. Architecturally necessary for Phase 5+ but lower priority than building the MCPs themselves.

**Independent Test**: Can be tested by running the orchestrator with MCP servers mocked — verifying that `write_note` and `move_note` MCP tool calls are made (not direct `atomic_write` calls) when processing a `draft_reply` decision.

**Acceptance Scenarios**:

1. **Given** the orchestrator processes an email with decision=archive, **When** `_apply_decision()` runs, **Then** it calls `move_note` MCP tool (not `move_to_done()` directly) to move the file to `vault/Done/`.
2. **Given** the Obsidian MCP is unavailable, **When** `_apply_decision()` attempts a vault write, **Then** it falls back to direct `vault_ops.py` call, logs `mcp_fallback` warning, and continues processing.
3. **Given** the Gmail MCP is unavailable when a send is attempted, **When** the error occurs, **Then** the draft stays in `vault/Approved/`, `mcp_unavailable` is logged, and the cycle completes without crashing.

---

### Edge Cases

- What happens if an email is approved while the MCP server is restarting? → Draft stays in `vault/Approved/`, picked up on next poll cycle.
- What if `send_email` is called with an email address that bounces? → Gmail API returns delivery failure; logged as `email_delivery_failed`; draft moved to `vault/Logs/failed/`.
- What if two orchestrator instances both try to send the same approved draft? → File lock (existing `.orchestrator.lock`) prevents concurrent execution. Second instance raises RuntimeError and exits.
- What if `vault/Approved/` contains a file with corrupt frontmatter? → `read_note` returns error; orchestrator logs `read_error` and skips, does not crash.
- What if the Gmail MCP loses its OAuth token mid-session? → Tool returns `auth_required` error; orchestrator logs and pauses email-send actions; vault writes continue unaffected.

---

## Requirements *(mandatory)*

### Functional Requirements

**Gmail MCP Server**

- **FR-001**: The Gmail MCP server MUST expose a `send_email` tool that accepts `to`, `subject`, `body`, and optional `reply_to_message_id` parameters and sends the email via authenticated Gmail API.
- **FR-002**: The Gmail MCP server MUST expose a `list_emails` tool that accepts `query` (Gmail search query) and `max_results` parameters and returns a list of email summaries.
- **FR-003**: The Gmail MCP server MUST expose a `get_email` tool that accepts `message_id` and returns full email content including metadata and decoded body.
- **FR-004**: The Gmail MCP server MUST expose a `move_email` tool that accepts `message_id` and `destination_label` to move emails between Gmail labels/folders.
- **FR-005**: The Gmail MCP server MUST expose an `add_label` tool that accepts `message_id` and `label_name` to tag processed emails.
- **FR-006**: All Gmail MCP tools MUST return structured JSON responses — success OR typed error objects (never raw exception tracebacks).
- **FR-007**: The Gmail MCP server MUST reuse the existing OAuth2 token from `token.json` (set by HT-002). It MUST NOT require re-authentication on each request.
- **FR-008**: The Gmail MCP server MUST log every `send_email` call to `vault/Logs/` before execution (pre-action audit log per Constitution Principle IX).

**Obsidian MCP Server**

- **FR-009**: The Obsidian MCP server MUST expose a `read_note` tool that accepts a vault-relative path and returns `{frontmatter: {...}, body: "..."}`.
- **FR-010**: The Obsidian MCP server MUST expose a `write_note` tool that accepts path, frontmatter dict, and body string; writes atomically (temp file + rename pattern from `watchers/utils.py`).
- **FR-011**: The Obsidian MCP server MUST expose a `list_notes` tool that accepts directory path and optional `filter` (e.g., `"status:pending"`) and returns a list of matching file paths.
- **FR-012**: The Obsidian MCP server MUST expose a `move_note` tool that accepts source and destination paths and moves the file atomically.
- **FR-013**: The Obsidian MCP server MUST expose a `search_notes` tool that accepts a text query and returns matching file paths and matched snippets.
- **FR-014**: All Obsidian MCP tools MUST return typed error objects for not-found, permission-denied, or parse-error cases — never raw Python exceptions.

**MCP Fallback Protocol**

- **FR-015**: Every MCP tool call in the orchestrator MUST be wrapped with the fallback protocol from `ai-control/MCP.md`: attempt MCP → on failure log error → execute fallback → if fallback fails escalate.
- **FR-016**: The system MUST never silently skip an operation when MCP is unavailable. It MUST log the fallback or escalation.

**Registration**

- **FR-017**: Both MCP servers MUST be registered in Claude Code's MCP configuration (human action HT-005) with their entry point scripts documented in `ai-control/HUMAN-TASKS.md`.
- **FR-018**: Both MCP servers MUST have a `health_check` tool or startup validation that confirms the server is operational at session start.

### Key Entities

- **GmailMCPServer**: MCP server process wrapping Gmail API. State: `token.json`. Tools: 5. Lives in `mcp-servers/gmail/`.
- **ObsidianMCPServer**: MCP server process wrapping vault filesystem. State: vault directory. Tools: 5. Lives in `mcp-servers/obsidian/`.
- **MCPToolCall**: Single invocation of a tool. Has input schema, output schema, typed error responses.
- **ApprovedDraft**: Vault file in `vault/Approved/` with `status: pending_approval` moved there by human. Consumed by orchestrator → Gmail MCP `send_email`.
- **AuditLogEntry**: Pre-action JSONL record in `vault/Logs/` written before every `send_email` call.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An approved draft reply is sent via `send_email` within one poll cycle (≤ 120 seconds of being placed in `vault/Approved/`).
- **SC-002**: All 5 Gmail MCP tools and all 5 Obsidian MCP tools are callable from Claude Code without knowing any implementation details (OAuth, file paths, YAML parsing).
- **SC-003**: MCP server unavailability does not crash the orchestrator — it logs the fallback and continues processing other emails.
- **SC-004**: Contract tests cover all tool input/output schemas — any breaking change to a tool signature is caught immediately.
- **SC-005**: Zero hardcoded Gmail OAuth secrets or vault paths in any MCP server code — all configuration via `.env`.
- **SC-006**: Both MCP servers pass `health_check` within 3 seconds of startup.

---

## Constraints

### NOT Supported in Phase 4

- **No WhatsApp MCP** — WhatsApp MCP is Phase 5 (Silver). Scope is Gmail + Obsidian only.
- **No Calendar MCP** — Calendar integration is Phase 5+.
- **No email summarisation or threading** — The MCP exposes raw email data. Summarisation remains in the orchestrator's LLM prompt.
- **No attachment downloading or analysis** — `get_email` returns attachment metadata (name, size, MIME type) but does NOT download attachment content.
- **No Obsidian plugin dependency** — The Obsidian MCP operates directly on the vault filesystem. It does NOT require the Obsidian Local REST API plugin (avoids HT-005 blocking the build).
- **No streaming tool responses** — All MCP tools return complete JSON responses synchronously.
- **No MCP server persistence / database** — Both servers are stateless. Gmail state lives in `token.json`; vault state lives in the filesystem.

### Technical Constraints

- Gmail MCP MUST reuse `watchers/gmail_watcher.py` OAuth client — no duplicate auth logic.
- Obsidian MCP MUST reuse `watchers/utils.py` `atomic_write` — no duplicate file write logic.
- Both servers MUST follow `ai-control/MCP.md` development standards: typed tools, stateless, contract tests, fallback defined, registered in registry.
- Both servers MUST be in `mcp-servers/` directory per `ai-control/LOOP.md` canonical directory map.

---

## Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| Phase 3 complete (RalphWiggumOrchestrator) | ✅ DONE | Provides `_apply_decision()` hook points for MCP wiring |
| Gmail OAuth `token.json` | ✅ DONE (HT-002) | Already exists from Phase 2 live run |
| `watchers/utils.py` `atomic_write` | ✅ DONE | Reused by Obsidian MCP |
| `watchers/gmail_watcher.py` OAuth client | ✅ DONE | Reused by Gmail MCP |
| HT-005: Register MCPs in Claude Code settings | ⏳ PENDING HUMAN | Human must add MCP config entries after servers are built |
| Phase 4 spec approved | ⏳ THIS SPEC | Required before implementation starts |

---

## Assumptions

1. The `mcp-servers/` directory will hold one subdirectory per MCP server (`mcp-servers/gmail/`, `mcp-servers/obsidian/`).
2. Both MCP servers are Python-based (consistent with the rest of the codebase) using the `mcp` Python SDK.
3. The Obsidian MCP does NOT require the Obsidian desktop app to be running — it operates directly on the vault directory.
4. Gmail `send_email` sends from the authenticated account only — no multi-account support.
5. The orchestrator's `_apply_decision()` will be refactored to call MCP tools where available, with direct `vault_ops.py` calls as fallback — NOT a full rewrite.
6. `vault/Approved/` is the trigger directory for email sends. The human moves drafts here to approve them (existing Loop 3 HITL pattern from `ai-control/LOOP.md`).

---

## Out of Scope

- WhatsApp, Calendar, Odoo MCPs (Phase 5+)
- MCP server deployment to cloud (Phase 7)
- LLM MCP server (no standard exists)
- Streaming tool responses
- Attachment content retrieval
- Multi-account Gmail support
- Obsidian plugin-based vault access

---

*Governed by: `ai-control/AGENTS.md` | `ai-control/LOOP.md` | `ai-control/MCP.md`*
*Version: 1.0.0 | Date: 2026-02-23*
