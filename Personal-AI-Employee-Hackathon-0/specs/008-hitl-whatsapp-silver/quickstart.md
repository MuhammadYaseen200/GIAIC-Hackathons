# Quickstart: HITL + WhatsApp Silver Tier — Phase 5

**Branch**: `008-hitl-whatsapp-silver` | **Date**: 2026-03-02

---

## Prerequisites

Before running any Phase 5 code, confirm all entry criteria are met:

| Check | Command | Expected |
|-------|---------|---------|
| Phase 4 complete | `cat specs/007-mcp-integration/spec.md \| grep Status` | `Status: Complete` |
| Gmail MCP healthy | `python3 mcp_servers/gmail/server.py` (then `health_check`) | `{"status": "healthy"}` |
| Obsidian MCP healthy | `python3 mcp_servers/obsidian/server.py` (then `health_check`) | `{"status": "healthy"}` |
| Go bridge running | `curl http://localhost:8080/health` | `{"status": "ok"}` |
| Python version | `python3 --version` | `Python 3.12+` |

---

## Step 1: Install New Dependencies

```bash
# From project root
pip install httpx>=0.27

# Verify (should already be present from previous phases)
pip show mcp pydantic google-api-python-client google-auth-oauthlib pyyaml pytest pytest-asyncio
```

---

## Step 2: Update .env

Add these variables to your `.env` file at the project root:

```bash
# WhatsApp configuration
WHATSAPP_BACKEND=go_bridge
WHATSAPP_BRIDGE_URL=http://localhost:8080
OWNER_WHATSAPP_NUMBER=+XXXXXXXXXXXX   # Your WhatsApp number in E.164 format

# Calendar configuration (same credentials.json as Gmail)
CALENDAR_CREDENTIALS_PATH=/path/to/credentials.json   # same as GMAIL_CREDENTIALS_PATH
CALENDAR_TOKEN_PATH=/path/to/calendar_token.json       # NEW separate token file

# HITL configuration
HITL_BATCH_DELAY_SECONDS=120    # 2 minutes before sending batch notification
HITL_REMINDER_HOURS=24          # Send reminder after 24h of no response
HITL_TIMEOUT_HOURS=48           # Mark timed_out after 48h
HITL_MAX_CONCURRENT_DRAFTS=5   # Maximum pending drafts at one time
```

---

## Step 3: Authorize Google Calendar (HT-011)

> This step is required ONCE before running Calendar MCP live tests.
> You already added `calendar.readonly` scope to the existing OAuth consent screen.
> The same `credentials.json` works — you only need a separate `calendar_token.json`.

```bash
# Run the calendar authorization script (creates calendar_token.json)
python3 scripts/calendar_auth.py

# Expected output:
# Opening browser for Google Calendar authorization...
# Authorization successful!
# Token saved to: /path/to/calendar_token.json
```

> Note: `scripts/calendar_auth.py` is created in Phase 5 Task T11 (Calendar MCP server setup).
> If it doesn't exist yet, run the following one-time authorization manually:
```python
# One-time manual auth (paste in Python REPL):
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    ["https://www.googleapis.com/auth/calendar.readonly"]
)
creds = flow.run_local_server(port=0)
import json
from pathlib import Path
Path("calendar_token.json").write_text(json.dumps({
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": creds.scopes,
}))
print("calendar_token.json created!")
```

---

## Step 4: Setup Vault Directories

```bash
# Create vault/Rejected/ (does not exist yet)
mkdir -p vault/Rejected
touch vault/Rejected/.gitkeep

# Verify all Phase 5 directories exist
ls vault/
# Expected: Needs_Action  Pending_Approval  Approved  Rejected  Done  Drafts  Logs
```

---

## Step 5: Run Unit Tests First

```bash
# Privacy Gate unit tests (fast, no network, no vault)
pytest tests/unit/test_privacy_gate.py -v

# HITL Manager unit tests (mocked MCPClient)
pytest tests/unit/test_hitl_manager.py -v

# WhatsApp watcher unit tests (mocked bridge)
pytest tests/unit/test_whatsapp_watcher.py -v

# Run all unit tests at once
pytest tests/unit/ -v
```

---

## Step 6: Run Contract Tests

```bash
# WhatsApp MCP schema validation
pytest tests/contract/test_whatsapp_mcp_contracts.py -v

# Calendar MCP schema validation
pytest tests/contract/test_calendar_mcp_contracts.py -v

# Run all contract tests
pytest tests/contract/ -v
```

---

## Step 7: Run Integration Tests

```bash
# WhatsApp watcher → vault integration (uses tmp vault, mocked bridge)
pytest tests/integration/test_whatsapp_watcher_integration.py -v

# HITL full cycle integration (mocked Gmail MCP + WhatsApp MCP)
pytest tests/integration/test_hitl_integration.py -v

# Calendar MCP integration (mocked Google API)
pytest tests/integration/test_calendar_mcp_integration.py -v

# Run all integration tests
pytest tests/integration/ -v
```

---

## Step 8: Run Full Test Suite

```bash
# All tests (unit + contract + integration)
pytest tests/ -v

# With coverage report
pytest tests/ --cov=mcp_servers --cov=watchers --cov=orchestrator --cov-report=term-missing
```

Expected: All tests pass. Coverage ≥ 80% for watchers/, mcp_servers/whatsapp/, mcp_servers/calendar/, orchestrator/hitl_manager.py.

---

## Step 9: Smoke Test — WhatsApp MCP

```bash
# Verify Go bridge is running first
curl -s http://localhost:8080/health

# Test health_check tool manually
python3 - <<'EOF'
import asyncio
from orchestrator.mcp_client import MCPClient
from pathlib import Path

async def test():
    client = MCPClient("whatsapp", ["python3", "mcp_servers/whatsapp/server.py"], Path("vault"))
    result = await client.call_tool("health_check", {})
    print(result)

asyncio.run(test())
EOF
```

Expected output: `{'status': 'healthy', 'backend': 'go_bridge', 'connected_number': '+XXXXXXXXXXXX', ...}`

---

## Step 10: Smoke Test — Calendar MCP

```bash
# Test list_events for next 7 days
python3 - <<'EOF'
import asyncio
from orchestrator.mcp_client import MCPClient
from datetime import datetime, timezone, timedelta
from pathlib import Path

async def test():
    client = MCPClient("calendar", ["python3", "mcp_servers/calendar/server.py"], Path("vault"))
    now = datetime.now(timezone.utc)
    result = await client.call_tool("list_events", {
        "time_min": now.isoformat(),
        "time_max": (now + timedelta(days=7)).isoformat(),
        "max_results": 5
    })
    print(f"Found {len(result['events'])} events")
    for e in result['events']:
        print(f"  - {e['summary']} @ {e['start']}")

asyncio.run(test())
EOF
```

---

## Troubleshooting

### Go bridge not responding

```bash
# Check if bridge process is running
ps aux | grep whatsapp
# Or check port
ss -tlnp | grep 8080

# Restart Go bridge (from its directory)
# Note: Go bridge was set up during HT-004 — refer to bridge documentation
```

### Calendar token expired

```bash
# Delete old token and re-authorize
rm calendar_token.json
python3 scripts/calendar_auth.py
```

### Privacy Gate false positive (legitimate content redacted)

This is expected behavior. The Privacy Gate errs on the side of privacy.
- Owner sees `[REDACTED]` in vault note
- Owner can check their own WhatsApp for original message
- To view: open WhatsApp app on phone, find the conversation

### HITL draft not found (approve command fails)

```bash
# List current pending drafts
ls vault/Pending_Approval/

# Check draft frontmatter
head -20 vault/Pending_Approval/<draft_id>.md
```

### WhatsApp message not appearing in vault

```bash
# Check watcher logs
tail -f vault/Logs/whatsapp_watcher.log

# Check if bridge is receiving messages
curl http://localhost:8080/messages
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WHATSAPP_BACKEND` | Yes | `go_bridge` | Backend: `go_bridge` or `pywa` |
| `WHATSAPP_BRIDGE_URL` | Yes (go_bridge) | `http://localhost:8080` | Go bridge REST URL |
| `OWNER_WHATSAPP_NUMBER` | Yes | — | Your WhatsApp number (E.164) |
| `CALENDAR_CREDENTIALS_PATH` | Yes | — | Path to Google credentials.json |
| `CALENDAR_TOKEN_PATH` | Yes | — | Path to calendar_token.json |
| `HITL_BATCH_DELAY_SECONDS` | No | `120` | Seconds to wait before sending batch |
| `HITL_REMINDER_HOURS` | No | `24` | Hours before sending reminder |
| `HITL_TIMEOUT_HOURS` | No | `48` | Hours before marking timed_out |
| `HITL_MAX_CONCURRENT_DRAFTS` | No | `5` | Max pending drafts at once |
| `VAULT_PATH` | Yes | — | Absolute path to vault directory |

---

*Quickstart complete. Proceed to `/sp.tasks` to generate the task list.*
