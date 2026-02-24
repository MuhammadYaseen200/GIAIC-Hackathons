# Implementation Plan: MCP Integration — Phase 4

**Branch**: `007-mcp-integration` | **Date**: 2026-02-24 | **Spec**: `specs/007-mcp-integration/spec.md`
**Input**: Build Gmail MCP server (5 tools) and Obsidian MCP server (5 tools); wire RalphWiggumOrchestrator to route all external actions through MCPs; register both servers in Claude Code settings.

---

## Summary

Phase 4 wraps two existing subsystems — the Gmail API client (`watchers/gmail_watcher.py`) and vault filesystem operations (`watchers/utils.py`) — into two stdio MCP servers using the Python `mcp` SDK. The `RalphWiggumOrchestrator._apply_decision()` hook is then refactored to route vault writes through the Obsidian MCP and approved-draft sends through the Gmail MCP, with `vault_ops.py` as the fallback path. Both servers follow the fallback protocol from `ai-control/MCP.md`. Per Constitution Principle IV, all external actions route through MCP after Phase 4.

---

## Technical Context

| Field | Value |
|-------|-------|
| Language/Version | Python 3.12 (consistent with existing codebase) |
| Primary Dependencies | `mcp>=1.0.0` (installed; add to requirements.txt), `pydantic>=2.0`, `google-api-python-client`, `pyyaml`, `python-dotenv`, `anyio` (mcp dep) |
| Storage | `GMAIL_TOKEN_PATH` (OAuth token); `VAULT_PATH` filesystem; `vault/Logs/` for pre-send audit JSONL |
| Testing | `pytest`, `pytest-asyncio`, `anyio.streams.memory` (in-process MCP contract tests), `unittest.mock` |
| Target Platform | Linux/WSL2 local stdio process |
| Project Type | Single project (adds `mcp-servers/` to existing repo) |
| Performance Goals | `health_check` responds within 3 seconds; `send_email` completes within 10 seconds |
| Constraints | No live Gmail calls in tests; no breaking changes to `watchers/` or `orchestrator/`; all paths env-driven; no secrets in code |
| Scale/Scope | 2 MCP servers × 5+1 tools each = 12 total tools (incl. health_check); orchestrator processes ~100 emails/day |

---

## Constitution Check

*GATE: Must pass before implementation. All principles verified.*

| Principle | Requirement | Status |
|-----------|-------------|--------|
| I — Spec-First | spec.md complete, approved, all FRs covered | ✅ PASS |
| II — Local-First | stdio transport; vault on local filesystem; env-driven paths; no cloud services in Phase 4 | ✅ PASS |
| III — HITL | `vault/Approved/` is the HITL gate; `send_email` only executes on human-approved drafts | ✅ PASS |
| IV — MCP-First External Actions | Gmail API → Gmail MCP; vault file I/O → Obsidian MCP; orchestrator routes all external calls through MCP | ✅ PASS |
| VII — Phase-Gated | Phase 3 exit criteria met: 385/385 tests pass, 97% coverage, PR #18 merged | ✅ PASS |
| IX — Security | No secrets in code; `token.json` via env path; pre-action audit log written before every `send_email` | ✅ PASS |
| X — Graceful Degradation | Fallback to direct `vault_ops.py` if Obsidian MCP unavailable; draft preserved in `vault/Approved/` if Gmail MCP unavailable; `mcp_fallback` logged on every fallback | ✅ PASS |

**ALL GATES PASS** — cleared to proceed to implementation.

---

## Project Structure

### Documentation (this feature)

```text
specs/007-mcp-integration/
├── plan.md              ← This file
├── spec.md              ← Feature requirements (18 FRs, 4 user stories)
├── research.md          ← Phase 0 output: SDK decisions, reuse patterns
├── data-model.md        ← Phase 1 output: entities, state machines, error taxonomy
├── quickstart.md        ← Phase 1 output: setup, test, troubleshoot
├── contracts/
│   ├── gmail-tools.json       ← Phase 1 output: all 6 Gmail tool JSON schemas
│   └── obsidian-tools.json    ← Phase 1 output: all 6 Obsidian tool JSON schemas
└── tasks.md             ← Phase 2 output (/sp.tasks — NOT created by /sp.plan)
```

### Source Code (repository root)

```text
mcp-servers/                        ← NEW (per LOOP.md canonical directory map)
├── gmail/
│   ├── __init__.py
│   ├── server.py                   ← MCP server entry point; stdio transport; health_check
│   ├── auth.py                     ← OAuth2 client (adapted from gmail_watcher.py:170-211)
│   ├── tools.py                    ← Tool handlers: 5 tools + audit log for send_email
│   └── models.py                   ← Pydantic I/O models for all 5 Gmail tools
└── obsidian/
    ├── __init__.py
    ├── server.py                   ← MCP server entry point; stdio transport; health_check
    ├── tools.py                    ← Tool handlers: 5 tools; reuses atomic_write + render_yaml_frontmatter
    └── models.py                   ← Pydantic I/O models for all 5 Obsidian tools

orchestrator/
├── orchestrator.py                 ← MODIFIED: _apply_decision() → MCP calls + vault_ops fallback
│                                     NEW: _scan_approved_drafts() → send_email via Gmail MCP
├── mcp_client.py                   ← NEW: MCPClient with fallback protocol (ai-control/MCP.md)
└── vault_ops.py                    ← UNCHANGED: fallback path for Obsidian MCP

tests/
├── contract/                       ← New directory
│   ├── test_gmail_mcp_contracts.py    ← Schema validation; error format; isError flag
│   └── test_obsidian_mcp_contracts.py ← Schema validation; error format; round-trip
├── integration/                    ← Existing directory (augmented)
│   ├── test_gmail_mcp_integration.py  ← All 5 Gmail tools; mocked OAuth; no live API
│   └── test_obsidian_mcp_integration.py ← All 5 Obsidian tools; tmp vault directory
└── unit/                           ← Existing directory (augmented)
    ├── test_mcp_client.py             ← Fallback protocol: MCP down → fallback → log
    └── test_orchestrator_mcp.py       ← _apply_decision() with mocked MCPClient

requirements.txt                    ← MODIFIED: add mcp>=1.0.0
.env                                ← MODIFIED: add VAULT_PATH, GMAIL_MCP_SERVER, OBSIDIAN_MCP_SERVER
ai-control/HUMAN-TASKS.md           ← MODIFIED: update HT-005 with exact Claude Code config entries
```

---

## Complexity Tracking

| Addition | Why Needed | Simpler Alternative Rejected |
|---------|------------|------------------------------|
| `orchestrator/mcp_client.py` | Centralize MCP tool calling + fallback protocol; independently testable | Inline MCP calls in orchestrator.py violates SRP; makes fallback hard to test |
| `mcp-servers/` top-level directory | Constitution Principle IV + spec constraint + LOOP.md canonical dir map | Already required; not a new decision |
| `tests/contract/` directory | Contract tests cover tool schemas independently of integration behavior | Merging into integration tests makes schema regressions harder to catch |

---

## Implementation Phases

### Phase A: Gmail MCP Server

**Scope**: Build the `mcp-servers/gmail/` package that wraps Gmail API.

**Key design decisions** (from research.md):
- `auth.py` adapts `_authenticate()` from `gmail_watcher.py:170-211`; no browser prompt (token must exist from HT-002); raises `auth_required` error if token missing.
- `tools.py` writes JSONL audit entry to `vault/Logs/` **before** calling Gmail API for `send_email` (FR-008, Constitution Principle IX).
- All tools return `dict` (success) or `CallToolResult(isError=True, content=[TextContent(text=json.dumps(error))])` for errors — never raise exceptions to the MCP framework.
- `server.py` validates env vars on startup; registers all tools; runs `stdio_server`.

**Files to create**:
1. `mcp-servers/gmail/__init__.py` — empty
2. `mcp-servers/gmail/models.py` — Pydantic models: `SendEmailInput`, `ListEmailsInput`, `GetEmailInput`, `MoveEmailInput`, `AddLabelInput`; error models; output models
3. `mcp-servers/gmail/auth.py` — `get_gmail_service()` singleton; `_load_and_refresh()` token lifecycle
4. `mcp-servers/gmail/tools.py` — `GmailTools` class with 5 async tool handlers
5. `mcp-servers/gmail/server.py` — `Server("gmail")` + all `@server.list_tools()`, `@server.call_tool()` registrations; `async def main()` → `stdio_server`

**Tests to create**:
- `tests/contract/test_gmail_mcp_contracts.py` — schema validation for all 6 tools; error format; `isError=True` flag verification
- `tests/integration/test_gmail_mcp_integration.py` — all 5 tools with `unittest.mock.patch("mcp_servers.gmail.auth.get_gmail_service")`

---

### Phase B: Obsidian MCP Server

**Scope**: Build the `mcp-servers/obsidian/` package that wraps vault filesystem operations.

**Key design decisions** (from research.md):
- `tools.py` imports `atomic_write`, `render_yaml_frontmatter`, `sanitize_utf8` directly from `watchers.utils` (FR-010).
- YAML frontmatter parsed with `yaml.safe_load()` — no extra dependency.
- All paths validated to be inside `VAULT_PATH` root to prevent path traversal (FR-014, Constitution Principle IX).
- `search_notes` uses Python `pathlib` glob + case-insensitive string match — no external search engine needed for Phase 4 scale.

**Files to create**:
1. `mcp-servers/obsidian/__init__.py` — empty
2. `mcp-servers/obsidian/models.py` — Pydantic models for all 5 tools; error models
3. `mcp-servers/obsidian/tools.py` — `ObsidianTools` class with 5 async tool handlers
4. `mcp-servers/obsidian/server.py` — `Server("obsidian")` + registrations; `async def main()` → `stdio_server`

**Tests to create**:
- `tests/contract/test_obsidian_mcp_contracts.py` — schema validation; round-trip `write_note` → `read_note`; error format
- `tests/integration/test_obsidian_mcp_integration.py` — all 5 tools with `tmp_path` pytest fixture as vault root

---

### Phase C: Orchestrator MCP Wiring

**Scope**: Wire the existing `RalphWiggumOrchestrator` to route through MCP. No rewrite — targeted changes only.

**Key design decisions** (from research.md):
- New `orchestrator/mcp_client.py`: `MCPClient` class with `call_tool(tool_name, args, fallback=None)`. Fallback protocol: attempt → on `McpError` / timeout → log `mcp_fallback` → call `fallback()` → if `fallback` raises → log `mcp_escalation`.
- `orchestrator.py` `_apply_decision()` refactored: each `vault_ops` call becomes `mcp_client.call_tool("obsidian", tool, args, fallback=vault_ops_fn)`.
- New `_scan_approved_drafts()` method: polls `vault/Approved/*.md` for `status: pending_approval`; calls `mcp_client.call_tool("gmail", "send_email", {...})` on each; on success moves to `vault/Done/`.
- `_scan_approved_drafts()` integrated into `_run_poll_cycle()` alongside `scan_pending_emails`.

**Files to create/modify**:
1. `orchestrator/mcp_client.py` — `MCPClient(server_name, command, vault_path)` with `call_tool()` + fallback
2. `orchestrator/orchestrator.py` — modify `_apply_decision()` (5 branches); add `_scan_approved_drafts()`; add `_send_approved_draft(draft)` using Gmail MCPClient

**Tests to create/modify**:
- `tests/unit/test_mcp_client.py` — fallback protocol; `mcp_fallback` log entry; escalation path
- `tests/unit/test_orchestrator_mcp.py` (or modify `tests/unit/test_orchestrator.py`) — `_apply_decision()` with mocked `MCPClient`

---

### Phase D: Housekeeping + Registration

**Scope**: Declare dependencies, update env config, prepare human-task docs.

**Files to modify**:
1. `requirements.txt` — add `mcp>=1.0.0` under Phase 4 section
2. `.env` — add `VAULT_PATH`, `GMAIL_MCP_SERVER`, `OBSIDIAN_MCP_SERVER`
3. `ai-control/HUMAN-TASKS.md` — update HT-005 with exact `~/.claude.json` MCP config entries for both servers (using project absolute paths)

---

## Risk Analysis

| Risk | Blast Radius | Mitigation |
|------|-------------|-----------|
| OAuth token expired between Phase 2 live run and Phase 4 | Gmail MCP `health_check` fails; no email send | `health_check` tool detects early; `auth.py` refresh logic handles token refresh automatically |
| `_apply_decision()` refactor breaks 385 existing tests | All orchestrator tests fail | Keep `vault_ops.py` as fallback path; tests use mocked `MCPClient` that returns success by default; fallback path keeps old behavior intact |
| `mcp` SDK breaking change in future | Both MCP servers broken | Pin `mcp>=1.0.0` in requirements.txt; contract tests catch API changes |

---

## Acceptance Criteria (from spec.md)

- [ ] Gmail MCP: `health_check` passes within 3s of startup (SC-006)
- [ ] Gmail MCP: `send_email` sends via live Gmail without credentials in code (SC-005)
- [ ] Obsidian MCP: `write_note` → `read_note` round-trips correctly (User Story 3, AS-1)
- [ ] Orchestrator: `_apply_decision(archive)` calls `obsidian.move_note` (not `move_to_done` directly) (User Story 4, AS-1)
- [ ] Fallback: Obsidian MCP unavailable → orchestrator logs `mcp_fallback` and continues (SC-003)
- [ ] Contract tests: all 10 tool schemas pass validation with contract test suite (SC-004)
- [ ] Zero secrets hardcoded (SC-005)
- [ ] `mcp` in requirements.txt (housekeeping)

---

## Related Artifacts

| Artifact | Path |
|---------|------|
| Feature spec | `specs/007-mcp-integration/spec.md` |
| Research findings | `specs/007-mcp-integration/research.md` |
| Data model | `specs/007-mcp-integration/data-model.md` |
| Gmail tool contracts | `specs/007-mcp-integration/contracts/gmail-tools.json` |
| Obsidian tool contracts | `specs/007-mcp-integration/contracts/obsidian-tools.json` |
| Quickstart | `specs/007-mcp-integration/quickstart.md` |
| Task list (next step) | `specs/007-mcp-integration/tasks.md` (created by `/sp.tasks`) |
| Constitution | `.specify/memory/constitution.md` |
| MCP registry | `ai-control/MCP.md` |
| Human tasks | `ai-control/HUMAN-TASKS.md` (HT-005) |

---

*Governed by: `ai-control/AGENTS.md` | `ai-control/LOOP.md` | `ai-control/MCP.md`*
*Version: 1.0.0 | Date: 2026-02-24*
