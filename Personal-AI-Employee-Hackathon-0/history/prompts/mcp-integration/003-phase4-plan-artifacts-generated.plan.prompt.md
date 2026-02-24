---
id: "003"
title: Phase 4 MCP Plan Artifacts Generated
stage: plan
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: MuhammadYaseen200
command: /sp.plan
labels: ["phase4", "mcp", "gmail-mcp", "obsidian-mcp", "plan", "research", "contracts", "data-model", "quickstart"]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-mcp-integration/plan.md (created)
  - specs/007-mcp-integration/research.md (created)
  - specs/007-mcp-integration/data-model.md (created)
  - specs/007-mcp-integration/quickstart.md (created)
  - specs/007-mcp-integration/contracts/gmail-tools.json (created)
  - specs/007-mcp-integration/contracts/obsidian-tools.json (created)
tests: []
---

## Prompt

phase 4 (MCP Integration)
after my /sp.plan command you and your team start the work, then limit reach and everything break in mid, now the limit reset, you and your team can continue where the loss, first you need to identify how much they done and how much remain
see where it break:
 Resuming /sp.plan for Phase 4 MCP Integration. Let me check the background research agents.

● Task Output(non-blocking) adb1988 — Research MCP SDK patterns and codebase
● Task Output(non-blocking) a0ac7bf — Research MCP SDK best practices via web

Both agents completed. Then hit context limit before generating plan artifacts.

now:
  you have constitution, spec, adr, plan, tasks, research and phr file for backup support and as resource and Reusable intelligence to start planning
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows
- use skills, sub-agents, mcps, plugins, hooks

## Response snapshot

**Governance execution**:
- Identified break-point: both research agents (adb1988, a0ac7bf) had completed; spec.md read; context limit hit before Phase 1 artifact generation
- Resumed at Phase 1: generated all 6 plan artifacts in sequence
- Task #30 (Phase 0 Research) → completed; Task #31 (Phase 1 Generate artifacts) → in_progress → completed

**Phase 0 Research (already complete from prior session)**:
- Agent adb1988: OAuth2 pattern from gmail_watcher.py:170-211, atomic_write from utils.py, BaseWatcher interface, _apply_decision() 5 decision branches, MCP SDK confirmed installed
- Agent a0ac7bf: mcp.server.lowlevel.server.Server decorator pattern, stdio_server context manager, Pydantic model_json_schema() for tool schemas, CallToolResult(isError=True) error pattern

**Phase 1 Artifacts Generated**:

1. `specs/007-mcp-integration/research.md` — 8 decisions documented:
   - D1: Low-level MCP Server API (not FastMCP)
   - D2: OAuth2 reuse from gmail_watcher.py (no subclassing)
   - D3: atomic_write direct import from watchers/utils.py
   - D4: stdio transport (not HTTP/SSE)
   - D5: Typed error objects via CallToolResult(isError=True)
   - D6: In-memory stream mocking + mock OAuth for tests
   - D7: New orchestrator/mcp_client.py for fallback protocol
   - D8: Add mcp>=1.0.0 to requirements.txt

2. `specs/007-mcp-integration/data-model.md` — all Pydantic models documented:
   - 5 Gmail input models + 3 output models + AuditLogEntry
   - 5 Obsidian input models + 2 output models
   - Shared MCPError model with 8-code error taxonomy
   - Email processing state machine diagram
   - vault/Approved/ directory added to vault structure

3. `specs/007-mcp-integration/plan.md` — full implementation plan:
   - Constitution check: all 7 principles PASS
   - Project structure: mcp-servers/gmail/, mcp-servers/obsidian/, orchestrator/mcp_client.py, tests/contract/
   - Phase A: Gmail MCP Server (5 files + 2 test files)
   - Phase B: Obsidian MCP Server (4 files + 2 test files)
   - Phase C: Orchestrator MCP Wiring (_apply_decision refactor + _scan_approved_drafts)
   - Phase D: Housekeeping (requirements.txt, .env, HUMAN-TASKS.md)
   - Risk analysis: 3 risks with mitigations

4. `specs/007-mcp-integration/contracts/gmail-tools.json` — 6 tools (incl. health_check):
   - send_email, list_emails, get_email, move_email, add_label, health_check
   - Full JSON Schema for inputSchema + outputSchema + errorCodes

5. `specs/007-mcp-integration/contracts/obsidian-tools.json` — 6 tools (incl. health_check):
   - read_note, write_note, list_notes, move_note, search_notes, health_check
   - Full JSON Schema for inputSchema + outputSchema + errorCodes

6. `specs/007-mcp-integration/quickstart.md` — developer guide:
   - Install deps, run both servers, register in Claude Code, run tests, E2E approval flow, troubleshooting table

**Next step**: Run `/sp.tasks` to generate `specs/007-mcp-integration/tasks.md`
