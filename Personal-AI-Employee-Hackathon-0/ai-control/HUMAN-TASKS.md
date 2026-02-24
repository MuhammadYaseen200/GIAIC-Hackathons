# H0 Human-Dependent Tasks

> **Agent Control Authority**: This file is managed by **[`AGENTS.md`](AGENTS.md)**.
> Agents may READ this file to understand what humans must do. Agents MUST NOT mark tasks as DONE — only the human who completed the action may update the status. Escalation protocol follows Loop 3 (HITL) in [`LOOP.md`](LOOP.md).
> Related: [`AGENTS.md`](AGENTS.md) (agent registry) | [`LOOP.md`](LOOP.md) (human-in-the-loop)

## Purpose
This file tracks all tasks that REQUIRE human intervention because Claude Code cannot perform them autonomously. These tasks involve authentication, provisioning, installation, or physical access that is beyond AI agent capability.

**Status Legend**: PENDING | IN_PROGRESS | DONE | BLOCKED | DEFERRED

---

## Critical Priority (Blocks Phase 1-2)

### HT-001: Create Obsidian Vault and Folder Structure
- **Status**: PENDING
- **Blocks**: Phase 1 (Obsidian Vault)
- **Why Human**: Obsidian is a desktop application. Claude cannot launch GUI apps or create vaults through the Obsidian interface.
- **Instructions**:
  1. Open Obsidian desktop application
  2. Create new vault pointing to: `<project-root>/vault/`
  3. Create the following folder structure inside the vault:
     ```
     vault/
     ├── Inbox/
     ├── Needs_Action/
     ├── Plans/
     ├── Pending_Approval/
     ├── Approved/
     ├── Done/
     ├── Logs/
     ├── CEO_Briefings/
     ├── Templates/
     ├── Company_Handbook.md
     └── Dashboard.md
     ```
  4. Enable "Files & Links" → "Detect all file extensions" in Obsidian settings
  5. Install "Dataview" community plugin (needed for Dashboard.md queries)
- **Verification**: Run `ls -la vault/` and confirm all folders exist
- **Claude Can Then**: Create markdown templates, populate Dashboard.md, write watcher output files

### HT-002: Set Up Gmail API OAuth2 Credentials
- **Status**: PENDING
- **Blocks**: Phase 2 (First Watcher - Bronze)
- **Why Human**: Google Cloud Console requires browser login, project creation, and OAuth consent screen setup. These are interactive GUI flows with CAPTCHA and 2FA.
- **Instructions**:
  1. Go to https://console.cloud.google.com/
  2. Create new project: "H0-Personal-AI-Employee"
  3. Enable Gmail API: APIs & Services → Library → Gmail API → Enable
  4. Configure OAuth consent screen:
     - User type: External (or Internal if using Workspace)
     - App name: "H0 AI Employee"
     - Scopes: `gmail.readonly`, `gmail.send`, `gmail.modify`
  5. Create OAuth 2.0 credentials:
     - Application type: Desktop application
     - Download `credentials.json`
  6. Place `credentials.json` in project root (it's in .gitignore)
  7. Add to `.env`:
     ```
     GMAIL_CREDENTIALS_PATH=./credentials.json
     GMAIL_TOKEN_PATH=./token.json
     ```
  8. Run the initial auth flow (Claude will provide the script):
     ```bash
     python scripts/gmail_auth.py
     ```
     This will open a browser for you to log in and authorize.
- **Verification**: `token.json` exists and contains valid refresh_token
- **Claude Can Then**: Build gmail_watcher.py, Gmail MCP server, email processing pipeline

### HT-003: Fix Broken MCP Servers
- **Status**: PENDING
- **Blocks**: Various phases depending on MCP
- **Why Human**: MCP configuration requires editing Claude Code settings files and potentially installing system-level packages.
- **Instructions**:

  **Priority 1 — git MCP** (blocks Phase 0+):
  - Check MCP config for git server entry
  - Verify the git MCP server binary/script path is correct
  - Restart Claude Code after config change
  - Fallback: `git` CLI works, so this is non-critical

  **Priority 2 — Neon MCP** (blocks Phase 6 Gold):
  - Sign up at https://neon.tech/ (free tier available)
  - Create a new project: "h0-ai-employee"
  - Copy the connection string
  - Add to `.env`: `DATABASE_URL=postgresql://...`
  - Update MCP config with Neon connection details
  - Verify: `psql $DATABASE_URL -c "SELECT 1"`

  **Priority 3 — n8n-local** (blocks Phase 5 Silver):
  - Install n8n: `npm install -g n8n` or use Docker: `docker run -p 5678:5678 n8nio/n8n`
  - Start n8n service
  - Update MCP config with n8n URL (default: http://localhost:5678)

  **Low Priority — gemini-cli, codex-cli, mcp-hfspace**:
  - These have functional alternatives (WebSearch, Claude Code, WebFetch)
  - Fix when bandwidth allows
  - gemini-cli: Set `GEMINI_API_KEY` in `.env`
  - codex-cli: `npm install -g @openai/codex`

- **Verification**: Run `/health` check on each MCP after fixing
- **Claude Can Then**: Use MCP tools instead of CLI fallbacks

---

## High Priority (Blocks Phase 5 Silver)

### HT-004: Authenticate WhatsApp Web Session
- **Status**: PENDING
- **Blocks**: Phase 5 (HITL Approval + WhatsApp)
- **Why Human**: WhatsApp Web requires scanning a QR code with your phone. This is a physical authentication step.
- **Instructions**:
  1. Claude will create the WhatsApp MCP server scaffolding
  2. When prompted, open the authentication URL in your browser
  3. Scan the QR code with WhatsApp on your phone
  4. Session file will be saved locally (never committed to git)
  5. Add session path to `.env`:
     ```
     WHATSAPP_SESSION_PATH=./whatsapp-session/
     ```
- **Verification**: WhatsApp watcher can read recent messages
- **Claude Can Then**: Build whatsapp_watcher.py, process incoming messages

### HT-005: Add New MCP Server Configurations
- **Status**: PENDING (Gmail MCP + Obsidian MCP built — registration required)
- **Blocks**: Phase 4 live execution (servers are BUILT; just need Claude Code registration)
- **Why Human**: MCP server configuration requires editing `~/.claude.json` (Claude Code's global settings) and restarting the CLI. Claude Code cannot edit its own config file.

- **Instructions**:

  **Step 1 — Open `~/.claude.json`** (create if it doesn't exist):
  ```bash
  code ~/.claude.json   # or: nano ~/.claude.json
  ```

  **Step 2 — Add the Gmail MCP server block**:

  Add under `"mcpServers"` (create the key if missing):
  ```json
  "gmail_mcp": {
    "command": "python3",
    "args": [
      "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/gmail/server.py"
    ],
    "env": {
      "GMAIL_CREDENTIALS_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/credentials.json",
      "GMAIL_TOKEN_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/token.json",
      "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
    }
  }
  ```

  **Step 3 — Add the Obsidian MCP server block**:
  ```json
  "obsidian_mcp": {
    "command": "python3",
    "args": [
      "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/obsidian/server.py"
    ],
    "env": {
      "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
    }
  }
  ```

  **Full `~/.claude.json` example** (if starting fresh):
  ```json
  {
    "mcpServers": {
      "gmail_mcp": {
        "command": "python3",
        "args": [
          "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/gmail/server.py"
        ],
        "env": {
          "GMAIL_CREDENTIALS_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/credentials.json",
          "GMAIL_TOKEN_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/token.json",
          "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
        }
      },
      "obsidian_mcp": {
        "command": "python3",
        "args": [
          "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/mcp_servers/obsidian/server.py"
        ],
        "env": {
          "VAULT_PATH": "/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/vault"
        }
      }
    }
  }
  ```

  **Step 4 — Restart Claude Code** (required for MCP changes to take effect):
  - Close and reopen your Claude Code terminal session

  **Step 5 — Verify health_check for each MCP**:
  ```bash
  # Test Gmail MCP health_check manually:
  cd /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0
  VAULT_PATH=./vault GMAIL_CREDENTIALS_PATH=./credentials.json GMAIL_TOKEN_PATH=./token.json \
    python3 -c "
  import asyncio, sys
  sys.path.insert(0, '.')
  from mcp_servers.gmail.tools import GmailTools
  from pathlib import Path
  async def test():
      t = GmailTools(Path('./vault'))
      r = await t.health_check()
      print(r)
  asyncio.run(test())
  "

  # Test Obsidian MCP health_check manually:
  VAULT_PATH=./vault python3 -c "
  import asyncio, sys
  sys.path.insert(0, '.')
  from mcp_servers.obsidian.tools import ObsidianTools
  from pathlib import Path
  async def test():
      t = ObsidianTools(Path('./vault'))
      r = await t.health_check()
      print(r)
  asyncio.run(test())
  "
  ```
  - Gmail: expect `{"status": "ok", "email": "<your-email>@gmail.com", "messages_total": <N>}`
  - Obsidian: expect `{"status": "ok", "vault_path": "...", "note_count": <N>}`

- **Verification**: After Claude Code restart, both `gmail_mcp` and `obsidian_mcp` appear as available MCP servers in the session
- **Claude Can Then**: Use `gmail_mcp` and `obsidian_mcp` tools natively in any Claude Code session for this project; orchestrator can send approved draft replies live

---

## Medium Priority (Blocks Phase 6 Gold)

### HT-006: Provision Neon PostgreSQL Database
- **Status**: PENDING
- **Blocks**: Phase 6 (Gold tier)
- **Why Human**: Neon requires account creation with email verification and credit card for paid tier (free tier works for development).
- **Instructions**:
  1. Go to https://neon.tech/
  2. Sign up with GitHub or email
  3. Create project: "h0-ai-employee"
  4. Select region closest to you
  5. Copy connection string
  6. Add to `.env`:
     ```
     DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/h0_db?sslmode=require
     NEON_PROJECT_ID=<project-id>
     ```
  7. Create initial database: `h0_db`
- **Verification**: `psql $DATABASE_URL -c "SELECT version();"` succeeds
- **Claude Can Then**: Run Alembic migrations, create tables, persist watcher data

### HT-007: Install Odoo Community Edition
- **Status**: DEFERRED (Gold tier — start when Bronze/Silver complete)
- **Blocks**: Phase 6 (Gold tier)
- **Why Human**: Odoo requires system-level package installation, database setup, and initial configuration wizard in browser.
- **Instructions**:
  1. Option A - Docker (recommended):
     ```bash
     docker run -d -p 8069:8069 --name odoo -t odoo:17.0
     ```
  2. Option B - Local install:
     - Follow https://www.odoo.com/documentation/17.0/administration/install.html
  3. Complete the initial setup wizard in browser (http://localhost:8069)
  4. Create admin user
  5. Add to `.env`:
     ```
     ODOO_URL=http://localhost:8069
     ODOO_DB=odoo
     ODOO_USER=admin
     ODOO_PASSWORD=<your-password>
     ```
- **Verification**: `curl http://localhost:8069/web/login` returns 200
- **Claude Can Then**: Build Odoo MCP server, integrate accounting data

---

## Low Priority (Blocks Phase 7 Platinum)

### HT-008: Provision Oracle Cloud VM
- **Status**: DEFERRED (Platinum tier)
- **Blocks**: Phase 7 (Always-On Cloud)
- **Why Human**: Oracle Cloud requires account creation with credit card, VM provisioning through web console, SSH key setup.
- **Instructions**:
  1. Go to https://cloud.oracle.com/
  2. Create free tier account
  3. Create compute instance:
     - Shape: VM.Standard.A1.Flex (free tier: 4 OCPU, 24GB RAM)
     - OS: Ubuntu 22.04
     - Add your SSH public key
  4. Note the public IP address
  5. Configure security list: open ports 22 (SSH), 443 (HTTPS)
  6. Add to `.env`:
     ```
     ORACLE_VM_IP=<public-ip>
     ORACLE_VM_USER=ubuntu
     ORACLE_SSH_KEY_PATH=~/.ssh/oracle_h0
     ```
  7. SSH in and install Docker:
     ```bash
     ssh -i ~/.ssh/oracle_h0 ubuntu@<public-ip>
     sudo apt update && sudo apt install -y docker.io docker-compose
     ```
- **Verification**: `ssh -i ~/.ssh/oracle_h0 ubuntu@<ip> "docker --version"` succeeds
- **Claude Can Then**: Deploy watchers, orchestrator, and MCP servers to cloud

### HT-010: Verify LLM Provider Connectivity
- **Status**: PENDING
- **Blocks**: Phase 3 (LLM Reasoning Loop) — must confirm before relying on live orchestrator
- **Why Human**: Requires your actual API key and network access to the provider endpoint. Claude cannot call external APIs directly without your credentials.
- **Instructions**:
  1. Ensure HT-009 is complete (ANTHROPIC_API_KEY set in .env, LLM_PROVIDER=anthropic)
  2. From the project root, run:
     ```bash
     python scripts/verify_llm_provider.py
     ```
  3. Expected output (exit 0):
     ```
     Provider : anthropic
     Model    : claude-sonnet-4-...
     Response : Hello
     Tokens   : <N> input / <N> output
     OK  LLM provider connectivity verified
     ```
  4. If exit 1: check your ANTHROPIC_API_KEY in .env, verify network access to api.anthropic.com
- **Verification**: Script exits 0 and prints "OK  LLM provider connectivity verified"
- **Claude Can Then**: Run the full orchestrator against your vault/Needs_Action/ emails

---

## Completed Tasks

| ID | Task | Completed | Notes |
|----|------|-----------|-------|
| HT-001 | Create Obsidian Vault and Folder Structure | 2026-02-17 | vault/ initialized with all required dirs |
| HT-002 | Set Up Gmail API OAuth2 Credentials | 2026-02-20 | token.json created, 52 emails processed live |
| HT-009 | Configure LLM Provider API Key(s) | 2026-02-22 | ANTHROPIC_API_KEY set in .env, anthropic SDK installed, LLM_PROVIDER=anthropic |
| HT-010 | Verify LLM Provider Connectivity | 2026-02-23 (PENDING) | Run `python scripts/verify_llm_provider.py` from project root to confirm provider responds correctly. Requires HT-009 complete. Exit 0 = pass. |

---

## Quick Reference: What Claude CAN Do vs. What Human MUST Do

| Claude CAN | Human MUST |
|------------|-----------|
| Write watcher Python code | Authenticate Gmail OAuth |
| Create MCP server scaffolding | Scan WhatsApp QR code |
| Generate Obsidian templates | Create Obsidian vault in GUI |
| Write database migrations | Provision Neon account |
| Create Docker configs | Install Odoo locally |
| Write deployment scripts | Provision Oracle Cloud VM |
| Configure `.env` template | Fill in actual secret values |
| Build test suites | Run manual browser-based auth |
| Create spec/plan/tasks | Approve sensitive actions |

---
*Governed by: .specify/memory/constitution.md (Principle III: Human-in-the-Loop)*
*Updated: 2026-02-16 | Next review: After each phase completion*
