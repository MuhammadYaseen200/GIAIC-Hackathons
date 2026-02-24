---
id: 007
title: Phase 3 US1 T011-T016 Complete
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: m-y-j
command: /sp.implement
labels: [mcp,gmail,orchestrator,phase3,us1,tools,contract-tests,integration-tests]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: history/adr/0005-mcp-server-framework-stack.md
  pr: null
files:
  - mcp_servers/gmail/tools.py
  - mcp_servers/gmail/server.py
  - orchestrator/orchestrator.py
  - tests/contract/test_gmail_send_contract.py
  - tests/unit/test_mcp_client.py
  - tests/integration/test_approved_draft_send.py
  - specs/007-mcp-integration/tasks.md
tests:
  - tests/unit/test_mcp_client.py (8 tests — all pass)
  - tests/contract/test_gmail_send_contract.py (5 tests — all pass)
  - tests/integration/test_approved_draft_send.py (5 tests — all pass)
  - Full suite: 403 tests — all pass, zero regressions
---

## Prompt

according to our plan execute Phase 3 MVP (T011–T016, US1) — T011+T012 in parallel, then T013, T014, T015+T016.

you have constitution, spec, plan, adr, tasks, data model, quick start, research, phr, requirements and contracts file for backup support and as resource and Reusable intelligence to start implementation
- create claude agent team instance
- apply all governance and control, applied enforcement, rules, laws, loops, automations, workflows
- use context7
- use skills, sub-agents, mcps, plugins, hooks
### 3. AGENT TEAM (MOBILIZED)
- **Command Team**: @qa-oversee, @loop-controller, @imperator, @path-warden
- **Build Team**: @modular-ai-architect, @ux-frontend-developer, @spec-architect

### 4. SKILLSET & MCP REGISTRY
- **Skill Set A (AI & MCP)**: `building-mcp-servers`, `scaffolding-openai-agents`, `streaming-llm-responses`, `building-chat-interfaces`
- **Skill Set B (Safety & Quality)**: `deployment-preflight-check`, `security-scan`, `env-validator`, `spec-driven-development`
- **Intelligence**: Use `skill-creator` to standardize the `asyncio.to_thread` wrapper for synchronous Google API calls.
- **Active MCPs**: `context7`, `code-search`, `postgres`

## Response snapshot

Phase 3 MVP (T011–T016, US1) fully implemented and tested. Execution order: T011+T012 in parallel → T013 → T014 → T015+T016 in parallel.

**Files created:**
- `mcp_servers/gmail/tools.py` — `GmailTools` class with all 5 tools (send_email, list_emails, get_email, move_email, add_label) + health_check. Includes asyncio.to_thread wrapping, pre-action audit log, typed error returns per contract.
- `mcp_servers/gmail/server.py` — FastMCP entry point with lifespan (env validation + warm-up), all 5 tools + health_check registered with MCP annotations.
- `orchestrator/orchestrator.py` — minimal diff: added MCPClient import, `_gmail_mcp` + `_approved_dir` in `__init__`, `_run_poll_cycle()` override, `_scan_approved_drafts()`, `_send_approved_draft()`.
- `tests/contract/test_gmail_send_contract.py` — 5 contract tests.
- `tests/unit/test_mcp_client.py` — 8 unit tests for fallback protocol.
- `tests/integration/test_approved_draft_send.py` — 5 integration tests for US1 acceptance scenarios.

**Bugs found and fixed:**
1. Contract tests patched `mcp_servers.gmail.auth.get_gmail_service` but tools.py binds the name locally on first import → fixed by patching `mcp_servers.gmail.tools.get_gmail_service`.
2. Test fixture produced unquoted YAML `subject: Re: Budget` which PyYAML fails to parse (colon-space in plain scalar) → fixed using `yaml.dump()` in test fixtures.
3. `_scan_approved_drafts` used `read_email_context` which requires `message_id` not present in draft files → fixed to parse frontmatter directly with `yaml.safe_load`.

**Result:** 403/403 tests pass, zero regressions.

## Outcome

- ✅ Impact: US1 complete — approved draft reply sending via Gmail MCP fully implemented and tested. vault/Approved/ → send_email → vault/Done/ workflow operational.
- 🧪 Tests: 18 new tests (8 unit + 5 contract + 5 integration), all pass. 403 total, zero regressions.
- 📁 Files: 6 files created, 1 modified (orchestrator.py minimal diff)
- 🔁 Next prompts: T017-T020 (US2 — full Gmail tools + contracts), T021-T024 (US3 — Obsidian MCP), T025-T027 (US4 — orchestrator MCP refactor)
- 🧠 Reflection: Three bugs found and fixed during green phase: import binding (patch target), YAML parsing (unquoted subjects), and read_email_context API mismatch. All minimal fixes; spec intent preserved.

## Evaluation notes (flywheel)

- Failure modes observed: (1) unittest.mock.patch target: must patch where name is bound (used), not where defined; (2) PyYAML plain scalar colon ambiguity; (3) API contract mismatch between vault_ops functions and draft file structure
- Graders run and results (PASS/FAIL): pytest 403/403 PASS
- Prompt variant (if applicable): sp.implement with parallel execution T011+T012, T015+T016
- Next experiment: T017-T024 in parallel batches (US2 + US3 simultaneously)
