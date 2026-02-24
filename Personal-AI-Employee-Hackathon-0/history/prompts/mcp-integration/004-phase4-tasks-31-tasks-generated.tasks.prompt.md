---
id: "004"
title: Phase 4 MCP Integration 31 Tasks Generated
stage: tasks
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: MuhammadYaseen200
command: /sp.tasks
labels: ["phase4", "mcp", "gmail-mcp", "obsidian-mcp", "tasks", "fastmcp", "building-mcp-servers", "orchestrator-wiring"]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/007-mcp-integration/tasks.md (created)
tests: []
---

## Prompt

/sp.task
now you have all research and data, read them:
6 artifacts generated under specs/007-mcp-integration/:

  File: plan.md — Full implementation plan: 4 phases (Gmail MCP, Obsidian MCP, Orchestrator wiring, Housekeeping), Constitution check (all 7 principles PASS), project structure, risk analysis
  File: research.md — 8 architectural decisions: SDK API choice, OAuth2 reuse, atomic_write reuse, stdio transport, error handling, test strategy, MCPClient design, dependency pinning
  File: data-model.md — All Pydantic I/O models, shared error taxonomy (8 error codes), email state machine diagram, updated vault directory structure
  File: contracts/gmail-tools.json — Full JSON Schema for 6 Gmail tools (incl. health_check)
  File: contracts/obsidian-tools.json — Full JSON Schema for 6 Obsidian tools (incl. health_check)
  File: quickstart.md — Setup, server launch, Claude Code registration, test commands, E2E flow, troubleshooting

use context7 is required

you have constitution, spec, adr, plan, tasks, research and phr file for backup support and as resource and Reusable intelligence to start quantum level tasks generation
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows
- use skills, sub-agents, mcps, plugins, hooks

### 3. AGENT TEAM (MOBILIZED)
- Command Team: @qa-oversee, @loop-controller, @imperator, @path-warden
- Build Team: @modular-ai-architect, @ux-frontend-developer, @spec-architect
### 4. SKILLSET & MCP REGISTRY
- Skill Set A (Construction): building-mcp-servers, scaffolding-openai-agents, streaming-llm-responses, building-chat-interfaces
- Skill Set B (Safety): deployment-preflight-check, security-scan, env-validator, spec-driven-development
- Intelligence: Use skill-creator to standardize the MCP contract testing patterns. Use context7 for latest MCP SDK documentation.
- MCP Servers: context7, code-search, postgres

## Response snapshot

**Skills loaded**: `building-mcp-servers` (Python MCP guide — FastMCP patterns, Pydantic v2, tool decorators, lifespan management)

**Key revision from skill guidance**: FastMCP (`mcp.server.fastmcp.FastMCP`) recommended over low-level Server API (research.md D1 superseded). FastMCP provides: `@mcp.tool` decorator, auto-schema from Pydantic, `mcp.run()` stdio entry point, lifespan context for persistent connections.

**tasks.md generated**: 31 tasks across 7 phases

| Phase | Tasks | Scope |
|-------|-------|-------|
| 1: Setup | T001–T005 | requirements.txt, directory structure, .env, vault/Approved/ |
| 2: Foundational | T006–T010 | Gmail auth.py, Gmail models.py, Obsidian models.py, MCPClient, test __init__ |
| 3: US1 (P1) | T011–T016 | Gmail send_email + health_check, approved draft workflow, fallback protocol tests |
| 4: US2 (P2) | T017–T020 | All 5 Gmail tools, full contract suite |
| 5: US3 (P3) | T021–T024 | All 5 Obsidian tools, Obsidian server.py |
| 6: US4 (P4) | T025–T027 | _apply_decision() MCP wiring, orchestrator tests |
| 7: Polish | T028–T031 | HUMAN-TASKS.md, MCP.md registry, spec exit criteria, pytest suite |

**Key design decisions in tasks**:
- auth.py: `get_gmail_service()` singleton pattern; `reset_service_cache()` for tests; raises `AuthRequiredError` (not browser flow)
- GmailTools: `_write_audit_log()` called BEFORE Gmail API send (Constitution Principle IX)
- ObsidianTools: imports `atomic_write` + `render_yaml_frontmatter` from `watchers/utils.py` directly (FR-010)
- ObsidianTools._resolve(): path traversal protection (validates path stays inside VAULT_PATH)
- MCPClient: JSON-RPC subprocess invocation + fallback protocol with `mcp_fallback` / `mcp_escalation` JSONL logging
- FastMCP lifespan: Gmail server validates env vars + warms up OAuth on startup; Obsidian server validates VAULT_PATH exists
- All tools return `json.dumps(dict)` — no raw exceptions exposed

**MVP path**: T001–T016 (Phases 1–3, User Story 1). Delivers primary value: approved draft reply sending.

**14 parallelizable tasks** marked [P].

**Next step**: Run `/sp.implement` to begin implementation, starting with Phase 1–2 tasks (T001–T010).
