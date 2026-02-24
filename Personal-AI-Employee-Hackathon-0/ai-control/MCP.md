# H0 MCP Server Registry

> **Agent Control Authority**: This file is managed by **[`AGENTS.md`](AGENTS.md)**.
> All MCP tool calls MUST be made by agents registered in `AGENTS.md`. Direct API calls from agent code bypassing this registry are FORBIDDEN (Constitution Principle IV).
> Related: [`LOOP.md`](LOOP.md) (enforcement loops) | [`SKILLS.md`](SKILLS.md) (skill registry) | [`SWARM.md`](SWARM.md) (swarm coordination)

## Purpose
This file is the authoritative registry of all Model Context Protocol (MCP) servers available to the H0 project. Per Constitution Principle IV, ALL external interactions MUST be routed through MCP servers. Direct API calls from agent code are FORBIDDEN.

## Registry Rules

1. Every MCP server MUST be registered here before use
2. Each entry MUST define: purpose, status, fallback behavior, and owning agent
3. Status MUST be kept current (checked at session start)
4. Broken MCPs MUST have a remediation plan or CLI fallback documented

## Connected MCP Servers (Operational)

| # | Server | Purpose | Tools Provided | Fallback | Phase Required |
|---|--------|---------|---------------|----------|---------------|
| 1 | **filesystem** | Read/write project files | read_file, write_file, edit_file, list_directory, search_files, directory_tree, move_file, create_directory, get_file_info | Native Claude Code file tools | Phase 0+ |
| 2 | **git** | Git operations (MCP) | git_status, git_diff, git_commit, git_add, git_log, git_branch, git_checkout, git_show, git_create_branch, git_reset | `git` CLI via Bash | Phase 0+ |
| 3 | **postgres** | PostgreSQL database queries | query (read-only) | SQLite local fallback | Phase 6 (Gold) |
| 4 | **docker** | Container management | run_command | Docker CLI via Bash | Phase 7 |
| 5 | **hopx-sandbox** | Isolated code execution | execute_code (isolated/persistent/rich/background), create_sandbox, file_read, file_write, run_command | Local Python execution | Phase 2+ |
| 6 | **playwright** | Browser automation + testing | (browser tools) | Playwright CLI | Phase 4+ |
| 7 | **scriptflow** | Script management + execution | script_add, script_list, script_run, script_edit, script_rm, script_get | Bash scripts directly | Phase 0+ |
| 8 | **github** | GitHub repo, PR, issue management | (GitHub API tools) | `gh` CLI via Bash | Phase 0+ |
| 9 | **context7** | Library documentation lookup | (context tools) | WebSearch + WebFetch | Phase 2+ |
| 10 | **ragie** | RAG document management | (RAG tools) | Manual document search | Phase 6 |
| 11 | **nx-mcp** | Monorepo build orchestration | (Nx tools) | Nx CLI via Bash | Optional |
| 12 | **chrome-devtools** | Browser debugging | (DevTools tools) | Playwright inspector | Phase 4+ |
| 13 | **code-search** | Code indexing and search | (search tools) | Grep/Glob tools | Phase 0+ |

## Broken MCP Servers (Need Fixing)

| # | Server | Issue | Remediation | CLI Fallback | Priority |
|---|--------|-------|-------------|-------------|----------|
| 1 | **Neon** | Auth/connection failure | Human MUST provide valid connection string in .env | `psql` CLI or postgres MCP with manual connection | HIGH (Gold tier) |
| 2 | **gemini-cli** | Auth not configured | Human MUST set up Gemini API key | WebSearch for research tasks | LOW |
| 3 | **n8n-local** | Local instance not responding | Human MUST start n8n Docker container | Manual workflow execution | MEDIUM |
| 4 | **codex-cli** | Not installed/configured | Human MUST install codex CLI tool | Claude Code native coding | LOW |
| 5 | **mcp-hfspace** | Connection failed | Human MUST configure HuggingFace token | WebFetch to HF API | LOW |
| 6 | **MCP_DOCKER** | Duplicate/redundant | Remove or consolidate with docker MCP | docker MCP (working) | LOW |
| 7 | **mcp_server_mysql** | Redundant MySQL config | Remove (using postgres for H0) | postgres MCP | LOW |
| 8 | **peppeteer** | Misconfigured (typo in name?) | Fix config or remove (playwright covers this) | playwright MCP | LOW |

## Project-Custom MCP Servers (Built — Phase 4)

| # | Server | Purpose | Tools | Path | Health Check | Phase |
|---|--------|---------|-------|------|-------------|-------|
| 1 | **gmail_mcp** | Gmail email send/read/act | `send_email`, `list_emails`, `get_email`, `move_email`, `add_label`, `health_check` | `mcp_servers/gmail/server.py` | `python3 -c "import asyncio; from mcp_servers.gmail.tools import GmailTools; from pathlib import Path; asyncio.run(GmailTools(Path('./vault')).health_check())"` | Phase 4 |
| 2 | **obsidian_mcp** | Vault read/write/search | `read_note`, `write_note`, `list_notes`, `move_note`, `search_notes`, `health_check` | `mcp_servers/obsidian/server.py` | `python3 -c "import asyncio; from mcp_servers.obsidian.tools import ObsidianTools; from pathlib import Path; asyncio.run(ObsidianTools(Path('./vault')).health_check())"` | Phase 4 |

**Registration**: See `ai-control/HUMAN-TASKS.md` HT-005 for exact `~/.claude.json` config blocks.

## Needed MCP Servers (To Add — Future Phases)

| # | Server | Purpose | Phase Required | Human Action Required | Priority |
|---|--------|---------|---------------|----------------------|----------|
| 1 | **WhatsApp MCP** | Message monitoring and sending | Phase 5 (Silver) | Authenticate WhatsApp Web session, configure MCP | HIGH |
| 2 | **Calendar MCP** | Schedule management | Phase 5 (Silver) | Set up Google Calendar API credentials | MEDIUM |
| 3 | **Odoo MCP** | ERP/accounting integration | Phase 6 (Gold) | Install Odoo Community, create API user, configure MCP | MEDIUM |

## MCP Fallback Protocol

Per Constitution Principle X (Graceful Degradation):

```
1. Attempt MCP tool call
2. If MCP fails -> log error to /Logs/
3. Check fallback method in this registry
4. Execute fallback
5. If fallback fails -> escalate to human
6. NEVER silently skip the operation
```

## MCP Development Standards

When creating new custom MCP servers (in `mcp-servers/` directory):

1. MUST have a spec in `specs/<mcp-name>/spec.md` before coding
2. MUST expose typed tool definitions with input validation
3. MUST be stateless (state lives in Obsidian vault)
4. MUST have contract tests (input -> expected output)
5. MUST define fallback behavior
6. MUST be registered in this file
7. MUST handle errors gracefully (no crashes)

## Status Check Protocol

At the start of every session:
1. Run health check on all "Connected" MCPs
2. Update status column if any changed
3. Log any newly broken MCPs
4. Verify critical MCPs for current phase are operational

---
*Governed by: .specify/memory/constitution.md (Principle IV: MCP-First External Actions)*
*See also: AGENTS.md (which agents use which MCPs)*
*Version: 1.0.0 | Date: 2026-02-16*
