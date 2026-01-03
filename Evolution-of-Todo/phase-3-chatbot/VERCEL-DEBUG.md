# Vercel Deployment Debugging Guide

## Recent Fix: Error 500 FUNCTION_INVOCATION_FAILED

### Problem Diagnosis

**Symptom**: Backend deployment returned 500 errors with `FUNCTION_INVOCATION_FAILED`.

**Root Causes Identified**:
1. **Missing psycopg2-binary**: Neon DB requires psycopg2 for connection pooling
2. **Limited error logging**: Original api/index.py had no error handling
3. **Route configuration**: Needed explicit routes for /api/*, /health, /docs

### Solutions Implemented

#### 1. Updated requirements.txt

Added `psycopg2-binary>=2.9.9` to support Neon DB's connection pooler:

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
sqlmodel>=0.0.22
asyncpg>=0.30.0
aiosqlite>=0.19.0
psycopg2-binary>=2.9.9  # ← ADDED
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.0,<4.1.0
python-multipart>=0.0.17
alembic>=1.14.0
pydantic-settings>=2.6.0
httpx>=0.28.0
email-validator>=2.0.0
```

#### 2. Hardened api/index.py

Added comprehensive error handling and logging:

```python
import sys
import traceback

try:
    from app.main import app
    handler = app

    # Debug logging
    print("✅ FastAPI app imported successfully", file=sys.stderr)
    print(f"✅ Available routes: {[route.path for route in app.routes]}", file=sys.stderr)

except ImportError as e:
    print("❌ IMPORT ERROR in api/index.py:", file=sys.stderr)
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise

except Exception as e:
    print("❌ UNEXPECTED ERROR in api/index.py:", file=sys.stderr)
    print(f"❌ Error type: {type(e).__name__}", file=sys.stderr)
    print(f"❌ Error: {str(e)}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    raise
```

**Benefits**:
- Errors now appear in Vercel function logs
- Clear distinction between import errors and runtime errors
- Stack traces help identify exact failure points

#### 3. Improved vercel.json Routing

Added explicit routes for all FastAPI endpoints:

```json
{
  "routes": [
    {"src": "/api/(.*)", "dest": "api/index.py"},
    {"src": "/health", "dest": "api/index.py"},
    {"src": "/docs", "dest": "api/index.py"},
    {"src": "/openapi.json", "dest": "api/index.py"},
    {"src": "/(.*)", "dest": "api/index.py"}
  ]
}
```

**Why This Matters**:
- Ensures all API routes are properly forwarded
- Health check endpoint accessible at `/health`
- Swagger docs available at `/docs`
- Catch-all route for any other paths

---

## Debugging Workflow

### Step 1: Check Vercel Function Logs

```bash
vercel logs https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app
```

Look for:
- ✅ "FastAPI app imported successfully" → Good!
- ❌ "IMPORT ERROR" → Module missing in requirements.txt
- ❌ "UNEXPECTED ERROR" → Configuration or environment issue

### Step 2: Test Health Endpoint

```bash
curl https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app/health
```

**Expected Response**:
```json
{"status": "ok"}
```

**Error Responses**:
- 500: Function crash (check logs)
- 404: Routing issue (check vercel.json)
- 502: Timeout or resource limit

### Step 3: Verify Environment Variables

Go to: https://vercel.com/muhammadyaseen200s-projects/backend/settings/environment-variables

**Required Variables**:
- `DATABASE_URL`: Neon DB connection string with `?ssl=require`
- `SECRET_KEY`: JWT signing secret (32+ chars)
- `CORS_ORIGINS`: Frontend URLs (JSON array or comma-separated)

**Common Mistakes**:
- Using `sslmode=require` instead of `ssl=require` (asyncpg incompatible)
- Missing `SECRET_KEY` → JWT generation fails
- Wrong `CORS_ORIGINS` → Frontend blocked by CORS

### Step 4: Test Database Connection

```bash
curl -X POST https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

**Success**: Returns user object with `id` and `email`
**Failure**: Check logs for database connection errors

---

## Common Errors and Fixes

### Error: "No module named 'asyncpg'"

**Cause**: Missing Python package in requirements.txt

**Fix**:
```bash
# Ensure requirements.txt includes:
asyncpg>=0.30.0
```

---

### Error: "No module named 'psycopg2'"

**Cause**: Neon DB needs psycopg2 for connection pooling

**Fix**:
```bash
# Add to requirements.txt:
psycopg2-binary>=2.9.9
```

---

### Error: "DATABASE_URL not set"

**Cause**: Environment variable missing in Vercel

**Fix**:
1. Go to Vercel dashboard → Settings → Environment Variables
2. Add `DATABASE_URL` with Neon connection string
3. Redeploy: `npx vercel --prod`

---

### Error: "ssl_: CERTIFICATE_VERIFY_FAILED"

**Cause**: SSL verification issue with Neon DB

**Fix**:
```bash
# Use ssl=require (not sslmode=require)
DATABASE_URL=postgresql+asyncpg://user:pass@host/db?ssl=require
```

---

### Error: "CORS policy blocked"

**Cause**: Frontend URL not in CORS_ORIGINS

**Fix**:
```bash
# Add frontend URL to environment variables
CORS_ORIGINS=["https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app"]
```

---

## Deployment Checklist

Before deploying:

- [ ] requirements.txt includes all dependencies
- [ ] api/index.py has error handling
- [ ] vercel.json routes configured
- [ ] Environment variables set in Vercel dashboard
- [ ] DATABASE_URL uses `ssl=require` format
- [ ] SECRET_KEY generated (32+ chars)
- [ ] CORS_ORIGINS includes frontend URL

After deploying:

- [ ] Check function logs for import errors
- [ ] Test `/health` endpoint returns 200
- [ ] Test registration endpoint works
- [ ] Verify CORS allows frontend requests
- [ ] Confirm database tables exist (run migrations if needed)

---

## Quick Redeploy

```bash
cd phase-2-web/backend
npx vercel --prod
```

**When to redeploy**:
- After changing requirements.txt
- After updating api/index.py
- After modifying vercel.json
- After setting environment variables

---

**Last Updated**: 2025-12-31 | **Status**: Production Ready ✅
