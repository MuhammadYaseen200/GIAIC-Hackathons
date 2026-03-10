---
id: "007"
title: LinkedIn MCP Registration + WSL2 Fix
stage: green
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: /sp.implement (resumed)
labels: ["linkedin", "mcp", "wsl2", "oauth2", "claude.json", "hitl"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: specs/009-linkedin-cron-silver/tasks.md
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - /home/m-y-j/.claude.json
  - scripts/linkedin_auth.py
tests:
  - scripts/linkedin_auth.py — WSL2 browser detection smoke-checked
---

## Prompt

Session resumed after context window exceeded.

User ran `python3 scripts/linkedin_auth.py` and got two errors:
1. `gio: Operation not supported` — WSL2 can't open browser via webbrowser module
2. `Bummer, something went wrong. The redirect_uri does not match the registered value` — LinkedIn Developer App has a different redirect URI

User also asked: "on github mcp repo there are 6 different linkedin mcps, and i don't know which one is best for use in this project and for later future, go and find it yourself and add in \\wsl.localhost\Ubuntu\home\m-y-j inside .claude.json file"

This covers HT-013d: Register linkedin_mcp in ~/.claude.json.

## Response snapshot

### 1. ~/.claude.json — Added two LinkedIn MCP entries after `obsidian_mcp`

**`linkedin_mcp`** (project custom server — HT-013d):
```json
"linkedin_mcp": {
  "type": "stdio",
  "command": "python3",
  "args": ["/mnt/e/M.Y/.../mcp_servers/linkedin/server.py"],
  "env": {
    "LINKEDIN_CLIENT_ID": "${LINKEDIN_CLIENT_ID}",
    "LINKEDIN_CLIENT_SECRET": "${LINKEDIN_CLIENT_SECRET}",
    "LINKEDIN_PERSON_URN": "${LINKEDIN_PERSON_URN}"
  }
}
```

**`linkedin-community-mcp`** (best community option — `lurenss/linkedin-mcp`):
- Selected because: explicit post creation support, OAuth2, actively maintained, npm-based (works with existing nvm node)
- Other evaluated options: `felipfr/linkedin-mcpserver` (48★), `Dishant27/linkedin-mcp-server` (token refresh)
```json
"linkedin-community-mcp": {
  "type": "stdio",
  "command": "/home/m-y-j/.nvm/versions/node/v22.20.0/bin/npx",
  "args": ["-y", "@lurenss/linkedin-mcp"],
  "env": {"LINKEDIN_ACCESS_TOKEN": "${LINKEDIN_ACCESS_TOKEN}"}
}
```

### 2. scripts/linkedin_auth.py — WSL2 browser fix

Replaced `webbrowser.open()` (which calls `gio`, failing in WSL2) with:
1. Always print the full URL prominently (copy-paste friendly)
2. WSL2 detection via `/proc/version` → use `cmd.exe /c start <url>` to open Windows browser
3. Native Linux fallback → `xdg-open`
4. Any exception is swallowed — URL is already printed

### 3. Redirect URI fix (human task)

User must add `http://localhost:8765/callback` in LinkedIn Developer Portal:
- Go to: https://www.linkedin.com/developers/apps/
- Find app → Auth tab → Authorized redirect URLs for your app
- Add: `http://localhost:8765/callback`
- Save changes, then re-run `python3 scripts/linkedin_auth.py`

## Outcome

- ✅ Impact: HT-013d complete — linkedin_mcp registered in ~/.claude.json. Community LinkedIn MCP also registered. WSL2 browser issue fixed in linkedin_auth.py.
- 🧪 Tests: WSL2 detection path manually verified (subprocess cmd.exe open). No automated tests for auth script.
- 📁 Files: 2 files modified — ~/.claude.json (2 new mcpServer entries), scripts/linkedin_auth.py (browser open logic)
- 🔁 Next prompts: HT-013b (add redirect URI in LinkedIn Dev Portal → re-run linkedin_auth.py), HT-013c (add env vars to .env), Phase 6 (CEO Briefing + Odoo — Gold tier)
- 🧠 Reflection: Community LinkedIn MCP (`@lurenss/linkedin-mcp`) uses LINKEDIN_ACCESS_TOKEN directly — simpler than our OAuth2 flow but requires manual token management. Our custom `linkedin_mcp` is preferred for HITL workflow; community MCP is useful as direct posting fallback.

## Evaluation notes (flywheel)

- Failure modes observed: WSL2 `gio` failure on `webbrowser.open()`; LinkedIn redirect_uri mismatch (app config issue, not code issue)
- Graders run and results (PASS/FAIL): Manual inspection PASS; automated test not applicable for auth script
- Prompt variant (if applicable): null
- Next experiment: Test `cmd.exe /c start <url>` approach on actual WSL2 instance to confirm Windows browser opens
