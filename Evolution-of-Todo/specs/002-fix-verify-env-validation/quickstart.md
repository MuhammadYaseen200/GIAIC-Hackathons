# Quickstart Guide: Phase-Aware Environment Validation

**Feature**: 002-fix-verify-env-validation
**Date**: 2026-01-27

---

## Overview

The `verify-env.py` script automatically detects your project phase and validates only the appropriate environment variables. No configuration required - just run it!

---

## Installation

**No installation required!** The script uses Python standard library only.

**Optional**: Install `python-dotenv` for automatic `.env` file loading:
```bash
pip install python-dotenv
```

If not installed, the script will show a warning but continue working (you'll need to export vars manually).

---

## Basic Usage

### Run Validation (Auto-Detect Phase)

```bash
cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo
./scripts/verify-env.py
```

**What happens**:
1. Script checks for `phase-3-chatbot/`, `phase-2-web/`, `phase-1-console/` directories
2. Uses highest phase found (or generic mode if none)
3. Validates environment variables for that phase
4. Exits with code 0 (success) or 2 (failure)

### Run with Manual Phase Override

```bash
./scripts/verify-env.py --phase 3
```

Forces Phase 3 validation regardless of detected directories. Useful for testing or non-standard setups.

---

## Phase-Specific Usage

### Phase 3: AI Chatbot

**Required Variables**:
- `DATABASE_URL` (SQLite or PostgreSQL)
- `OPENROUTER_API_KEY`
- `SECRET_KEY`

**Setup `.env` file**:
```bash
# Create/edit .env in project root
cat > .env <<'EOF'
DATABASE_URL=sqlite+aiosqlite:///./todo_app.db
OPENROUTER_API_KEY=sk-or-v1-your-key-here
SECRET_KEY=your-secret-key-here
EOF
```

**Run Validation**:
```bash
./scripts/verify-env.py
```

**Expected Output**:
```
Detected Phase: 3 | Using Phase 3 Chatbot profile
Description: AI chatbot with OpenRouter, SQLite/PostgreSQL, and custom JWT

============================================================
ENVIRONMENT VALIDATION
============================================================

[1/5] Checking environment variables...
   ✓ Environment variables

[2/5] Checking runtime versions...
   ✓ Python 3.13.9
   ✓ Node.js 24.11.1

...

============================================================

✅ All validations passed
============================================================
```

---

### Phase 2: Full-Stack Web

**Required Variables**:
- `DATABASE_URL` (PostgreSQL only)
- `SECRET_KEY`
- `NEXTAUTH_SECRET`

**Setup `.env` file**:
```bash
cat > .env <<'EOF'
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/todo_db
SECRET_KEY=your-secret-key-here
NEXTAUTH_SECRET=your-nextauth-secret-here
EOF
```

**Run Validation**:
```bash
git checkout <phase-2-branch>
./scripts/verify-env.py
```

**Expected Output**:
```
Detected Phase: 2 | Using Phase 2 Web profile
Description: Full-stack web application with PostgreSQL and NextAuth

============================================================
ENVIRONMENT VALIDATION
============================================================

[1/5] Checking environment variables...
   ✓ Environment variables

...

============================================================

✅ All validations passed
============================================================
```

---

### Generic Mode: Other Projects

If you copy `verify-env.py` to a different project (no phase directories), it runs in generic mode.

**Required Variables**:
- `DATABASE_URL` (any format)

**Setup `.env` file**:
```bash
cat > .env <<'EOF'
DATABASE_URL=sqlite:///./myapp.db
EOF
```

**Run Validation**:
```bash
./verify-env.py
```

**Expected Output**:
```
Generic validation mode (no phase detected)
Validating DATABASE_URL only

============================================================
ENVIRONMENT VALIDATION
============================================================

[1/5] Checking environment variables...
   ✓ Environment variables

[2/5] Checking runtime versions...
   ✓ Python 3.13.x
   ✓ Node.js 24.x.x

[3/5] Checking CLI tools...
   ✓ pnpm
   ✓ uv
   ✓ git

[4/5] Checking database connectivity...
   ✓ Database reachable

[5/5] Checking project structure...

============================================================

✅ All validations passed
============================================================
```

---

## Troubleshooting

### Error: "Missing required environment variable: DATABASE_URL"

**Problem**: DATABASE_URL not set in .env or environment.

**Solution**:
```bash
# Option 1: Add to .env file
echo "DATABASE_URL=sqlite+aiosqlite:///./todo_app.db" >> .env

# Option 2: Export manually
export DATABASE_URL="sqlite+aiosqlite:///./todo_app.db"

# Then re-run validation
./scripts/verify-env.py
```

---

### Error: "DATABASE_URL must use one of these database formats: postgresql, postgres. Found: sqlite"

**Problem**: Phase 2 expects PostgreSQL, but you have SQLite.

**Solution**:
```bash
# Option 1: Switch to Phase 3 (which allows SQLite)
git checkout 004-phase3-chatbot
./scripts/verify-env.py

# Option 2: Change DATABASE_URL to PostgreSQL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
./scripts/verify-env.py
```

---

### Warning: "python-dotenv not found - .env file will not be auto-loaded"

**Problem**: python-dotenv package not installed.

**Solution Option 1** (Install python-dotenv):
```bash
pip install python-dotenv
./scripts/verify-env.py
```

**Solution Option 2** (Export variables manually):
```bash
# Read .env and export vars
export $(grep -v '^#' .env | xargs)

# Then run validation
./scripts/verify-env.py
```

---

### Error: "Detected Phase: 3 but I want Phase 2 validation"

**Problem**: Multiple phase directories present, validator using highest phase.

**Solution**: Use `--phase` flag to override:
```bash
./scripts/verify-env.py --phase 2
```

---

## Testing Validation

### Test Phase 3 Validation

```bash
# Ensure you're on Phase 3 branch
git checkout 004-phase3-chatbot

# Create .env with Phase 3 requirements
cat > .env <<'EOF'
DATABASE_URL=sqlite+aiosqlite:///./todo_app.db
OPENROUTER_API_KEY=sk-or-v1-test-key
SECRET_KEY=test-secret-key-32-characters-long
EOF

# Run validation
./scripts/verify-env.py

# Expected: Exit code 0, "Detected Phase: 3", "VALIDATION PASSED"
echo $?  # Should print: 0
```

---

### Test Phase 2 Validation

```bash
# Switch to Phase 2 branch
git checkout <phase-2-branch-name>

# Create .env with Phase 2 requirements
cat > .env <<'EOF'
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/todo_db
SECRET_KEY=test-secret-key-32-characters-long
NEXTAUTH_SECRET=test-nextauth-secret-32-characters-long
EOF

# Run validation
./scripts/verify-env.py

# Expected: Exit code 0, "Detected Phase: 2", "VALIDATION PASSED"
echo $?  # Should print: 0
```

---

### Test Generic Mode

```bash
# Create clean test directory
mkdir /tmp/test-generic-validation
cd /tmp/test-generic-validation

# Copy validator
cp E:/M.Y/.../Evolution-of-Todo/scripts/verify-env.py .

# Create .env with only DATABASE_URL
echo "DATABASE_URL=sqlite:///./test.db" > .env

# Run validation
./verify-env.py

# Expected: "Generic validation mode", "VALIDATION PASSED"
echo $?  # Should print: 0
```

---

### Test Manual Override

```bash
# From Phase 3 branch (phase-3-chatbot/ exists)
git checkout 004-phase3-chatbot

# Force Phase 2 validation with --phase flag
./scripts/verify-env.py --phase 2

# Expected: Use Phase 2 profile (requires PostgreSQL + NEXTAUTH_SECRET)
# Will fail if .env has SQLite (which is expected behavior)
```

---

## Integration with dev-env-setup.sh

The `dev-env-setup.sh` orchestrator script calls `verify-env.py` as step 1/5.

**Usage**:
```bash
./scripts/dev-env-setup.sh
```

**Flow**:
```
Step 1/5: Running environment validation...
  → Calls verify-env.py
  → If exit code 2 (validation failure) → STOP (fail-fast)
  → If exit code 0 (success) → Continue to step 2/5

Step 2/5: Checking governance file synchronization...
Step 3/5: Cleaning build caches...
Step 4/5: Restarting development servers...
Step 5/5: Validating browser tools...
```

**Unblocking Automation**:
If `dev-env-setup.sh` was failing at step 1/5, fixing `.env` file will unblock the entire workflow:

```bash
# Fix .env (add missing variables)
vi .env

# Re-run automation
./scripts/dev-env-setup.sh

# Expected: Step 1/5 passes, automation proceeds
```

---

## Exit Codes Reference

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | ✅ All validations passed | Continue with development |
| 1 | ❌ Script execution error (Python exception) | Check Python version, dependencies |
| 2 | ❌ Validation failures (missing/invalid vars) | Fix `.env` file, re-run |
| 3 | ❌ Reserved for future (Directory Safety Rule) | - |

**Usage in Scripts**:
```bash
./scripts/verify-env.py
if [ $? -eq 0 ]; then
    echo "Environment validated successfully"
else
    echo "Validation failed, fix .env file"
    exit 1
fi
```

---

## Advanced Usage

### Generate Secret Keys

```bash
# Generate SECRET_KEY (32 hex characters)
openssl rand -hex 32

# Generate NEXTAUTH_SECRET (32 hex characters)
openssl rand -hex 32

# Add to .env
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
echo "NEXTAUTH_SECRET=$(openssl rand -hex 32)" >> .env
```

---

### Check Which Phase is Detected

```bash
# Run validation with verbose output
./scripts/verify-env.py 2>&1 | grep "Detected Phase"

# Output examples:
# "Detected Phase: 3 | Using Phase 3 profile"
# "Generic validation mode (no phase detected)"
```

---

### Copy Validator to Other Projects

```bash
# Copy verify-env.py to another project
cp scripts/verify-env.py /path/to/other-project/

# It will automatically use generic mode (DATABASE_URL only)
cd /path/to/other-project/
./verify-env.py

# To add custom validation, edit VALIDATION_PROFILES dict in the script
```

---

## Summary

| Scenario | Command | Expected Behavior |
|----------|---------|-------------------|
| Phase 3 validation | `./scripts/verify-env.py` | Detects Phase 3, validates SQLite + OpenRouter |
| Phase 2 validation | `git checkout phase-2-web && ./scripts/verify-env.py` | Detects Phase 2, validates PostgreSQL + NextAuth |
| Generic validation | Copy script to clean dir, run | Validates DATABASE_URL only |
| Manual override | `./scripts/verify-env.py --phase 2` | Forces Phase 2 validation |
| Automation | `./scripts/dev-env-setup.sh` | Runs validator as step 1/5, fails-fast if errors |

**Key Benefit**: Zero configuration required - validator auto-detects phase and validates appropriately! ✅
