# Quickstart: MCP Integration — Phase 4

**Branch**: `007-mcp-integration` | **Date**: 2026-02-24

---

## Prerequisites

1. Phase 3 complete (RalphWiggumOrchestrator, 385/385 tests passing)
2. Gmail OAuth token exists at `GMAIL_TOKEN_PATH` (set by HT-002)
3. `.env` configured with `VAULT_PATH`, `GMAIL_CREDENTIALS_PATH`, `GMAIL_TOKEN_PATH`
4. `mcp` SDK installed: `pip install -r requirements.txt`

---

## 1. Install Updated Dependencies

```bash
# From project root
pip install -r requirements.txt

# Verify mcp SDK:
python3 -c "import mcp; print('mcp SDK:', mcp.__version__)"
```

---

## 2. Run Gmail MCP Server (manual test)

```bash
# Start Gmail MCP in stdio mode (used by Claude Code)
python3 mcp-servers/gmail/server.py
```

The server waits on stdin for JSON-RPC messages. To test via Claude Code, see HT-005.

**Health check** (Claude Code agent tool call):
```
> Use tool: gmail → health_check {}
```
Expected: `{"status": "ok", "authenticated_as": "your@gmail.com"}`

---

## 3. Run Obsidian MCP Server (manual test)

```bash
# Set vault path (or use .env)
export VAULT_PATH=/path/to/vault

# Start Obsidian MCP in stdio mode
python3 mcp-servers/obsidian/server.py
```

**Health check**:
```
> Use tool: obsidian → health_check {}
```
Expected: `{"status": "ok", "vault_path": "/path/to/vault", "note_count": <n>}`

---

## 4. Register Both Servers in Claude Code (HT-005)

Add to `~/.claude.json` under `"mcpServers"`:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-servers/gmail/server.py"],
      "env": {
        "GMAIL_CREDENTIALS_PATH": "/path/to/credentials.json",
        "GMAIL_TOKEN_PATH": "/path/to/token.json",
        "VAULT_PATH": "/path/to/vault"
      }
    },
    "obsidian": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp-servers/obsidian/server.py"],
      "env": {
        "VAULT_PATH": "/path/to/vault"
      }
    }
  }
}
```

Restart Claude Code after adding. Verify with:
```
> Use tool: gmail → health_check {}
> Use tool: obsidian → health_check {}
```

---

## 5. Run All Tests

```bash
# Unit + contract + integration tests
pytest tests/ -v

# Contract tests only (no live API, no vault needed):
pytest tests/contract/ -v

# Integration tests (mocked OAuth, temp vault):
pytest tests/integration/ -v
```

Expected: All existing 385 tests pass + new Phase 4 tests added.

---

## 6. End-to-End Approval Flow Test

```bash
# 1. Create a test draft in vault/Approved/
cat > vault/Approved/test-reply.md << 'EOF'
---
status: pending_approval
to: test@example.com
subject: Test reply from AI
original_message_id: fake-id-001
---

This is a test reply body.
EOF

# 2. Run orchestrator (with mocked MCP in test mode)
python3 -m orchestrator.cli --dry-run

# 3. Check vault/Logs/ for pre-send audit entry
cat vault/Logs/gmail_mcp_$(date +%Y-%m-%d).jsonl
```

In dry-run mode, `send_email` is mocked and logs the call parameters without sending.

---

## 7. Key .env Variables for Phase 4

```bash
# Phase 4: MCP Servers
GMAIL_MCP_SERVER=mcp-servers/gmail/server.py
OBSIDIAN_MCP_SERVER=mcp-servers/obsidian/server.py
VAULT_PATH=./vault                      # vault root (relative to project root)

# Already set from Phase 2 (HT-002):
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `auth_required` error on Gmail MCP startup | `token.json` missing or expired | Run `python3 scripts/gmail_auth.py` to re-authenticate |
| `permission_denied` on Obsidian MCP | Path outside `VAULT_PATH` | Ensure all note paths are relative to vault root |
| MCP server not appearing in Claude Code | Config in wrong file or server not registered | Check `~/.claude.json` → `mcpServers` section; restart Claude Code |
| Existing tests fail after Phase 4 changes | Orchestrator refactor broke fallback | `vault_ops.py` unchanged; check that `MCPClient` fallback calls `vault_ops` correctly |
| `ImportError: mcp` | `mcp` not installed | Run `pip install mcp>=1.0.0` |
