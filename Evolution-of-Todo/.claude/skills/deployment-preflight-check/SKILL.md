---
name: deployment-preflight-check
description: |
  Validates deployment artifacts before pushing to Vercel or other serverless platforms.
  Use this skill when: (1) About to deploy a FastAPI/Python backend to Vercel, (2) Before
  running `vercel --prod` or `git push` to production branch, (3) After modifying
  requirements.txt, pyproject.toml, or environment variables, (4) When debugging 500 errors
  on Vercel deployments. Checks for: lock file conflicts, credential leaks, env var schema
  validation, CORS format issues, and .gitignore completeness.
---

# Deployment Pre-Flight Check

Run this checklist before every production deployment to prevent common serverless deployment failures.

## Quick Command

```bash
# From project root, run the preflight check script
python .claude/skills/deployment-preflight-check/scripts/preflight_check.py --path ./phase-2-web/backend
```

## Checklist Categories

### 1. Lock File Conflict Detection

Vercel detects `uv.lock` or `pyproject.toml` and may install from them instead of `requirements.txt`.

**Check:**
- [ ] No `uv.lock` in deployment directory (rename to `uv.lock.bak` if needed)
- [ ] No `pyproject.toml` in deployment directory OR ensure it doesn't conflict
- [ ] `requirements.txt` contains ALL dependencies with pinned versions

**Why:** Windows-compiled binaries in `uv.lock` (e.g., `pydantic_core`) crash on Linux serverless.

### 2. Credential Leak Detection

Scan for accidentally committed secrets.

**Patterns to grep:**
```bash
git grep -E "(npg_|sk-|api_key|SECRET_KEY|password\s*=)" --cached
```

**Check:**
- [ ] No database passwords in tracked files
- [ ] No API keys (OpenAI, Anthropic, etc.) in tracked files
- [ ] No JWT secrets in tracked files
- [ ] `.env`, `.env.local`, `*.local` files are gitignored

### 3. Environment Variable Schema Validation

Validate `.env.example` matches `config.py` Pydantic Settings types.

**Check for type mismatches:**

| Config Type | Env Format | Example |
|-------------|------------|---------|
| `str` | Plain string | `DATABASE_URL=postgres://...` |
| `int` | Number | `PORT=8000` |
| `bool` | true/false/1/0 | `DEBUG=false` |
| `list[str]` | JSON array | `CORS_ORIGINS=["https://example.com"]` |

**Common mistake:** `CORS_ORIGINS=https://a.com,https://b.com` fails; must be `["https://a.com","https://b.com"]`

### 4. CORS_ORIGINS Format Validation

If `config.py` defines `CORS_ORIGINS: list[str]`, verify the environment variable:

```python
# CORRECT (JSON array)
CORS_ORIGINS=["https://frontend.vercel.app","http://localhost:3000"]

# WRONG (comma-separated)
CORS_ORIGINS=https://frontend.vercel.app,http://localhost:3000
```

### 5. Gitignore Completeness

Verify these patterns exist in `.gitignore`:

```gitignore
# Environment files
.env
.env.*
*.local

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# Lock files (for Vercel compatibility)
uv.lock
uv.lock.bak

# Node
node_modules/

# IDE
.idea/
.vscode/
*.swp

# OS
.DS_Store
Thumbs.db
```

## Automated Script Usage

```bash
# Full check
python scripts/preflight_check.py --path ./backend

# Check specific category
python scripts/preflight_check.py --path ./backend --check credentials
python scripts/preflight_check.py --path ./backend --check lockfiles
python scripts/preflight_check.py --path ./backend --check env-schema
python scripts/preflight_check.py --path ./backend --check cors
python scripts/preflight_check.py --path ./backend --check gitignore
```

## Integration with Workflow

Call this skill at these points:

1. **Before `vercel --prod`**: Run full preflight check
2. **Before `git push origin main`**: Run credentials check
3. **After modifying `requirements.txt`**: Run lockfiles check
4. **After modifying `.env.example`**: Run env-schema check

## Failure Response

If any check fails:

1. **STOP** the deployment
2. **FIX** the identified issue
3. **RE-RUN** the preflight check
4. **PROCEED** only when all checks pass

## History

This skill was created after Phase 2 deployment incidents:
- `pydantic_core._pydantic_core` import error (uv.lock conflict)
- `CORS_ORIGINS` Pydantic validation error (wrong format)
- Credential exposure risk (settings.local.json)
