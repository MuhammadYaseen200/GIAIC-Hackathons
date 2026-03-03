---
id: 012
title: MCP Import Fix HT Done Commit
stage: misc
date: 2026-02-25
surface: agent
model: claude-sonnet-4-6
feature: mcp-integration
branch: 007-mcp-integration
user: m-y-j
command: /sp.git.commit_pr
labels: [hotfix,mcp-servers,import-fix,ht-004,ht-005,whatsapp,commit]
links:
  spec: specs/007-mcp-integration/spec.md
  ticket: null
  adr: null
  pr: https://github.com/MuhammadYaseen200/GIAIC-Hackathons/pull/new/007-mcp-integration
files:
  - mcp_servers/gmail/server.py
  - mcp_servers/obsidian/server.py
  - ai-control/HUMAN-TASKS.md
  - history/prompts/mcp-integration/011-phase4-commit-push-pr-deployed.misc.prompt.md
tests:
  - Manual: both servers start clean (exit 124 = healthy MCP stdio wait)
  - Verified: /mcp shows all 7 MCPs connected after Claude Code restart
---

## Prompt

/sp.git.commit_pr — commit hotfix for MCP server import crash + human task completions

## Response

Committed `7d88521` — `fix(mcp-servers): resolve relative import crash + mark HT-004/HT-005 done`

### Root cause fixed

Both `mcp_servers/gmail/server.py` and `mcp_servers/obsidian/server.py` used relative
imports (`from .models import`, `from .tools import`) which fail when Python runs the
file as a script (Claude Code's MCP subprocess launcher does exactly this).
`sys.path.insert(0, project_root)` was already present, so converting to absolute
imports (`from mcp_servers.gmail.models import`) is the correct minimal fix.

### Human tasks completed this session

- **HT-004**: WhatsApp Web authenticated — Go bridge built (fixed 5 context API breaking
  changes in main.go), whatsmeow updated to Feb 2026, paired as `XXXXXXXXXXXX:4@s.whatsapp.net`,
  bridge running on `:8080`, auto-start added to `~/.bashrc`
- **HT-005**: `gmail_mcp` + `obsidian_mcp` registered in `~/.claude.json` via Python
  json module (file updated atomically to avoid live-write race condition with Claude Code)

### MCP status after restart

All 7 MCPs confirmed connected via `/mcp`:
- `obsidian_mcp` ✅ (was failing — now fixed)
- `gmail_mcp` ✅
- `whatsapp` ✅
- `google-workspace` ✅
- `obsidian` ✅
- `google-search` ✅
- `claude.ai Gmail/Calendar` ✅

### Commit

`7d88521` pushed to `origin/007-mcp-integration`.
PR creation blocked by PAT scope (read-only token).
Manual PR URL: https://github.com/MuhammadYaseen200/GIAIC-Hackathons/pull/new/007-mcp-integration

## Outcome

- ✅ Both MCP servers now start correctly as Claude Code subprocesses
- ✅ HT-004 + HT-005 documented as DONE
- ✅ Phase 4 fully live — all MCP tools operational
- ⏸ Phase 5 deferred — weekly usage at 98%, resets Sunday 3:00 PM
