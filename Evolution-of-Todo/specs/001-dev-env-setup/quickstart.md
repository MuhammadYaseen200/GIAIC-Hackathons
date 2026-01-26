# Development Environment Setup - Quickstart Guide

**Feature**: 001-dev-env-setup
**Version**: 1.0.0
**Last Updated**: 2026-01-26

## Overview

Automation scripts to ensure your development environment is clean, properly configured, and ready for Phase 3/4 work. Implements 5 operational areas with fail-fast validation.

## Prerequisites

- **Git Bash** or **WSL** (Windows) / **Bash** (Unix/Mac)
- **PowerShell 5.1+** (Windows, optional for some operations)
- **Python 3.13+**
- **Node.js 18+**
- **pnpm** (Node package manager)
- **uv** (Python package manager)

## Quick Start

### Full Environment Reset (Recommended Daily Workflow)

Run all 5 operations in one command:

```bash
./scripts/dev-env-setup.sh
```

**Execution Order** (automatic):
1. ✅ **AC-005**: Environment Validation (fail-fast if broken)
2. ✅ **AC-001**: Governance File Synchronization
3. ✅ **AC-002**: Cache & Dependency Cleanup (quick mode)
4. ✅ **AC-003**: Server Lifecycle Management (kill old, start new)
5. ✅ **AC-004**: Browser Debugging Tools Validation

**Expected Time**: Under 5 minutes

**Output Example**:
```
🔍 [1/5] Running environment validation...
✅ Environment validation passed

🔍 [2/5] Checking governance file synchronization...
✅ ai-control/CLAUDE.md references @AGENTS.md
✅ AGENTS.md contains Spec-Kit workflow
✅ Constitution v2.0.0 referenced
✅ Agent teams consistent

🔍 [3/5] Cleaning caches (quick mode)...
✓ Removed phase-3-chatbot/frontend/.next/
✓ Removed phase-3-chatbot/backend/__pycache__/
✅ Caches cleaned (lock files preserved)

🔍 [4/5] Restarting development servers...
ℹ No servers running on port 3000 (skipped)
ℹ No servers running on port 8000 (skipped)
✅ Frontend server started on port 3000
✅ Backend server started on port 8000
✅ Health checks passed

🔍 [5/5] Validating browser debugging tools...
✅ Playwright MCP configured and responding
⚠ ChromeDevTools MCP not found (optional)
⚠ Puppeteer MCP not found (optional)

═══════════════════════════════════════
✅ Environment setup complete!
   5/5 operations successful
   Ready for development
═══════════════════════════════════════
```

---

## Individual Operations

### 1. Environment Validation Only

**When to Use**: Before starting any development work

```bash
./scripts/verify-env.sh
```

**What it Checks**:
- ✅ Required environment variables exist (DATABASE_URL, OPENROUTER_API_KEY, etc.)
- ✅ Environment variable formats are valid (URLs, ports, hostnames)
- ✅ Python version is 3.13+
- ✅ Node.js version is 18+
- ✅ Required CLI tools installed (pnpm, uv, git)
- ✅ Database connectivity (Neon PostgreSQL)

**Exit Codes**:
- `0` = All checks passed
- `2` = Validation failed (see error messages for fixes)

**Example Failure**:
```
❌ Environment validation failed

Issues found:
  1. Missing environment variable: DATABASE_URL
     Fix: Copy .env.example to .env in backend/ directory

  2. Python version 3.11 does not meet requirement (3.13+)
     Fix: Install Python 3.13 from python.org

  3. Command not found: pnpm
     Fix: npm install -g pnpm

Blocking all operations until fixed (fail-fast)
```

---

### 2. Governance File Synchronization Check

**When to Use**: After pulling changes, before starting work

```bash
./scripts/sync-governance.sh
```

**What it Checks**:
- ✅ `ai-control/CLAUDE.md` references `@AGENTS.md` on line 3
- ✅ `AGENTS.md` at root contains Spec-Kit workflow documentation
- ✅ Both files reference constitution v2.0.0
- ✅ Agent team definitions (Command/Build/Support) are consistent

**Example Output**:
```
Checking governance file synchronization...
✅ ai-control/CLAUDE.md → @AGENTS.md reference found
✅ AGENTS.md → Spec-Kit workflow documented
✅ Constitution v2.0.0 referenced in both files
✅ Agent team definitions consistent

Governance files synchronized
```

---

### 3. Cache Cleanup

**When to Use**: When experiencing build issues, stale code, or "works on my machine" problems

#### Quick Mode (Default - Caches Only)

```bash
./scripts/clean-caches.sh
```

**What it Removes**:
- Frontend: `.next/`, `node_modules/.cache/`
- Backend: `__pycache__/`, `.pytest_cache/`, `.uv/`

**What it Preserves**:
- ✅ `pnpm-lock.yaml` (for dependency recreation)
- ✅ `uv.lock` (for dependency recreation)
- ✅ `node_modules/` (installed packages)
- ✅ `.venv/` (Python virtual environment)

**Time**: ~5 seconds

#### Full Mode (Caches + Dependencies)

```bash
./scripts/clean-caches.sh --full
```

**Additional Removals**:
- Frontend: `node_modules/` (requires `pnpm install` after)
- Backend: `.venv/` (requires `uv sync` after)

**Time**: ~2-3 minutes (including reinstall)

**Use Case**: When dependency conflicts or corruption suspected

---

### 4. Server Lifecycle Management

**When to Use**: Port conflicts, zombie processes, or need to restart with fresh code

```bash
./scripts/restart-servers.sh
```

**What it Does**:
1. **Kill Phase** (idempotent - skips if no servers):
   - Finds processes on port 3000 (frontend)
   - Finds processes on port 8000 (backend)
   - Terminates them gracefully

2. **Start Phase**:
   - Starts Next.js dev server (`pnpm dev` in `phase-3-chatbot/frontend/`)
   - Starts FastAPI server (`uv run uvicorn` in `phase-3-chatbot/backend/`)

3. **Verification Phase**:
   - Waits for frontend health check (HTTP 200 on `localhost:3000`)
   - Waits for backend health check (HTTP 200 on `localhost:8000/health`)

**Example Output**:
```
Restarting development servers...

Kill Phase:
  ✓ Killed process on port 3000 (PID 12345)
  ℹ No process on port 8000 (already clean)

Start Phase:
  Starting frontend server (port 3000)...
  Starting backend server (port 8000)...

Verification:
  ✅ Frontend responding (localhost:3000)
  ✅ Backend responding (localhost:8000/health)

Servers ready for development
```

---

### 5. Browser Debugging Tools Validation

**When to Use**: Before running E2E tests or debugging UI issues

```bash
./scripts/validate-browser-mcps.sh
```

**What it Checks**:
- ✅ **Playwright MCP** (REQUIRED): Configured in MCP registry
- ⚠ **ChromeDevTools MCP** (OPTIONAL): Edge case debugging
- ⚠ **Puppeteer MCP** (OPTIONAL): Screenshot evidence generation

**Example Output**:
```
Validating browser debugging tools...

Required:
  ✅ Playwright MCP found and responding
  ✅ Can navigate to localhost:3000
  ✅ Screenshot capture working

Optional:
  ⚠ ChromeDevTools MCP not configured (optional - install if needed for edge cases)
  ⚠ Puppeteer MCP not configured (optional - install if needed for screenshots)

Browser tools ready (1/3 configured, 1 required)
```

---

## Troubleshooting

### "Port already in use" Error

**Symptom**: Server startup fails with port conflict

**Solution**:
```bash
./scripts/restart-servers.sh
```

This will kill old servers and start fresh ones.

---

### "Environment validation failed" Error

**Symptom**: `verify-env.sh` exits with code 2

**Solution**: Fix each reported issue before proceeding (fail-fast behavior)

Common fixes:
1. **Missing .env file**:
   ```bash
   cp phase-3-chatbot/backend/.env.example phase-3-chatbot/backend/.env
   cp phase-3-chatbot/frontend/.env.example phase-3-chatbot/frontend/.env
   # Edit .env files with actual values
   ```

2. **Wrong Python version**:
   ```bash
   # Install Python 3.13+ from python.org or pyenv
   python --version  # Verify
   ```

3. **Missing CLI tools**:
   ```bash
   npm install -g pnpm  # Install pnpm
   # Install uv from https://astral.sh/uv
   ```

---

### "Cache removal failed" Error

**Symptom**: Permission denied when deleting cache directories

**Solution**:
```bash
# Windows (Git Bash as Administrator)
# Or close all editors/IDEs that may have locks on files
```

---

### "Playwright MCP not found" Error

**Symptom**: Browser tool validation fails for required Playwright MCP

**Solution**:
1. Open Claude Code MCP settings
2. Add/enable Playwright MCP
3. Restart Claude Code
4. Re-run validation:
   ```bash
   ./scripts/validate-browser-mcps.sh
   ```

---

## Exit Codes Reference

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Operations completed successfully |
| 1 | General Error | Check error message, fix issue, retry |
| 2 | Validation Failed | Fix environment issues (fail-fast - required before proceeding) |

---

## Integration with Phase 3 Resume

After completing this setup, your environment will be ready to resume Phase 3 work:

```bash
# 1. Run full environment setup
./scripts/dev-env-setup.sh

# 2. Verify setup succeeded
echo $?  # Should output: 0

# 3. Proceed to Phase 3 blocker fixes
# - Fix HTTP 500 session creation error
# - Run E2E tests
# - Complete missing specs/ADRs
```

---

## Maintenance

**Daily Workflow**:
```bash
# Start of day
./scripts/dev-env-setup.sh

# Development work...

# End of day (optional cleanup)
./scripts/clean-caches.sh  # Quick cleanup
```

**Weekly Workflow**:
```bash
# Full cleanup and reinstall
./scripts/clean-caches.sh --full
cd phase-3-chatbot/frontend && pnpm install
cd ../backend && uv sync
```

---

## Support

- **Issues**: Report via GitHub Issues
- **Documentation**: See `specs/001-dev-env-setup/plan.md`
- **Constitution**: `.specify/memory/constitution.md`

---

**Version**: 1.0.0 | **Last Updated**: 2026-01-26
