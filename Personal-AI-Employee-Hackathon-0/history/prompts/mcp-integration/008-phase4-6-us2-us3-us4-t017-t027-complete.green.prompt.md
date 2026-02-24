---
id: 008
title: Phase 4-6 US2 US3 US4 T017-T027 Complete
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: m-y-j
command: /sp.implement
labels: [mcp,gmail,obsidian,orchestrator,us2,us3,us4,contract-tests,integration-tests,mcp-client,fastmcp]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: history/adr/0005-mcp-server-framework-stack.md
  pr: null
files:
  - tests/contract/test_gmail_mcp_contracts.py
  - tests/integration/test_gmail_mcp_integration.py
  - mcp_servers/obsidian/tools.py
  - mcp_servers/obsidian/server.py
  - tests/contract/test_obsidian_mcp_contracts.py
  - tests/integration/test_obsidian_mcp_integration.py
  - orchestrator/orchestrator.py
  - tests/unit/test_orchestrator_mcp.py
  - tests/integration/test_orchestrator_mcp_integration.py
  - specs/007-mcp-integration/tasks.md
tests:
  - tests/contract/test_gmail_mcp_contracts.py (14 tests — all pass)
  - tests/integration/test_gmail_mcp_integration.py (7 tests — all pass)
  - tests/contract/test_obsidian_mcp_contracts.py (16 tests — all pass)
  - tests/integration/test_obsidian_mcp_integration.py (11 tests — all pass)
  - tests/unit/test_orchestrator_mcp.py (7 tests — all pass)
  - tests/integration/test_orchestrator_mcp_integration.py (3 tests — all pass)
  - Full suite: 460/460 tests — all pass, zero regressions
---

## Prompt

/sp.implement T017–T020 (US2), T021–T024 (US3), T025–T027 (US4)
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
- **Intelligence**: Use `skill-creator` to standardize the "Return vs. Raise" error pattern for tools. Use `context7` for any Obsidian or YAML library documentation.
- **Active MCPs**: `context7`, `code-search`, `postgres`

## Response snapshot

Executed US2 (T017-T020), US3 (T021-T024), US4 (T025-T027) — 57 new tests written, all pass, 403→460 total tests green.

**T017 [US2]**: Already complete — all 4 Gmail tools (list_emails, get_email, move_email, add_label) were implemented in T011. Marked as done without redundant work.

**T018 [US2]**: Already complete — all 4 tools registered in server.py during T013. Marked as done.

**T019 [US2]**: Created `tests/contract/test_gmail_mcp_contracts.py` — 14 contract tests covering all 6 Gmail tools. Uses `make_http_error(status, reason)` helper for HttpError mocking. Patches `mcp_servers.gmail.tools.get_gmail_service` (bound location, not definition location).

**T020 [US2]**: Created `tests/integration/test_gmail_mcp_integration.py` — 7 integration tests with `mock_service` fixture; verifies audit log written by send_email.

**T021 [US3]**: Created `mcp_servers/obsidian/tools.py` — `ObsidianTools` class with 6 tools (health_check, read_note, write_note, list_notes, move_note, search_notes). `_resolve()` with path traversal protection. Reuses `atomic_write`, `render_yaml_frontmatter`, `sanitize_utf8` from `watchers/utils.py`.

**T022 [US3]**: Created `tests/contract/test_obsidian_mcp_contracts.py` — 16 contract tests: write+read roundtrip, not_found, permission_denied path traversal, list with filter, move success/not_found, search body/case-insensitive/snippet.

**T023 [US3]**: Created `mcp_servers/obsidian/server.py` — FastMCP entry point, validates VAULT_PATH at startup, registers all 5 tools + health_check.

**T024 [US3]**: Created `tests/integration/test_obsidian_mcp_integration.py` — 11 integration tests using real tmp_path filesystem; no mocking.

**T025 [US4]**: Modified `orchestrator/orchestrator.py` — added `_obsidian_mcp` MCPClient in `__init__`; refactored `_apply_decision()`: all 5 branches (draft_reply, needs_info, archive, urgent, delegate) now MCP-first with vault_ops fallback lambdas.

**T026 [US4]**: Created `tests/unit/test_orchestrator_mcp.py` — 7 unit tests using `make_orchestrator()` helper (mocked `_obsidian_mcp` + `_gmail_mcp`). Verifies each decision type routes to correct MCP tool (move_note for archive, write_note for others). Fix required: `EmailContext` needs `classification` and `date_received` fields.

**T027 [US4]**: Created `tests/integration/test_orchestrator_mcp_integration.py` — 3 E2E tests: archive→move_note, draft_reply→write_note, approved drafts sent in same cycle.

**Bug fixed**: YAML plain scalar colon issue — `subject: Re: Budget` fails PyYAML because `: ` in plain scalars is treated as mapping indicator. Fix: use `yaml.dump()` in all test fixtures (matches production `render_yaml_frontmatter` behavior).

## Outcome

- ✅ Impact: US2, US3, US4 fully implemented — Gmail MCP full contract coverage (14 contract + 7 integration tests), Obsidian MCP full coverage (16 contract + 11 integration tests), orchestrator MCP-first wiring verified (7 unit + 3 E2E tests). Phase 4 Phases 4-6 complete.
- 🧪 Tests: 57 new tests added (460 total); all pass; zero regressions from Phase 3
- 📁 Files: 8 new files created, orchestrator/orchestrator.py modified; tasks T021-T027 marked [x]
- 🔁 Next prompts: T028-T031 (Phase 7 Polish — HUMAN-TASKS.md, MCP.md, spec exit criteria, final test run)
- 🧠 Reflection: Key insight — patch where the name is BOUND (mcp_servers.gmail.tools.get_gmail_service), not where it's DEFINED (mcp_servers.gmail.auth.get_gmail_service). PyYAML colon-in-value bug is a recurring footgun in test fixtures.

## Evaluation notes (flywheel)

- Failure modes observed: (1) Wrong patch target for Gmail tools tests — fixed by patching mcp_servers.gmail.tools.get_gmail_service. (2) YAML ScannerError on `subject: Re: Budget` — fixed with yaml.dump(). (3) EmailContext missing required fields classification + date_received in T026 tests.
- Graders run and results (PASS/FAIL): pytest tests/ — 460/460 PASS
- Prompt variant (if applicable): /sp.implement with explicit T017-T027 scope + agent team mobilization
- Next experiment: Consider adding a pytest fixture factory for EmailContext to avoid missing required fields in future tests.
