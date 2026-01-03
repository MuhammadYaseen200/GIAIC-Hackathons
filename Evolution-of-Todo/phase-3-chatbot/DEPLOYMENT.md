# Phase 2 Vercel Deployment Guide

## Automated Deployment (RECOMMENDED)

**NEW:** Use the automated deployment scripts for one-command setup.

### Quick Start

```bash
# Windows (PowerShell)
.\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://user:pass@host/db?ssl=require"

# Linux/macOS (Bash)
./deploy-to-vercel.sh --database-url "postgresql+asyncpg://user:pass@host/db?ssl=require"
```

**What it does:**
- Generates secure JWT secret automatically
- Sets all environment variables via Vercel CLI
- Deploys both backend and frontend to production
- Creates timestamped deployment record

**Documentation:**
- Quick Start: `QUICK-START.md`
- Full Guide: `VERCEL-AUTOMATION-GUIDE.md`
- Example Output: `deployment-example-output.txt`

---

## Manual Deployment (Alternative)

If you prefer manual setup, follow the instructions below.

## Deployment Status

| Service | URL | Status |
|---------|-----|--------|
| **Frontend** | https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app | ✅ Deployed |
| **Backend** | https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app | ✅ Deployed (Protected) |

---

## Environment Variables Required

### Backend Project Settings

Go to: https://vercel.com/muhammadyaseen200s-projects/backend/settings/environment-variables

Add the following variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `DATABASE_URL` | `postgresql+asyncpg://neondb_owner:<YOUR_PASSWORD>@ep-weathered-resonance-adok3vmj-pooler.c-2.us-east-1.aws.neon.tech/neondb?ssl=require` | Your Neon DB connection string |
| `SECRET_KEY` | `[Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"]` | JWT signing secret |
| `CORS_ORIGINS` | `["https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app"]` | Frontend URL |

### Frontend Project Settings

Go to: https://vercel.com/muhammadyaseen200s-projects/frontend/settings/environment-variables

Add the following variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_API_URL` | `https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app` | Backend URL |
| `BACKEND_URL` | `https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app` | Backend URL (server-side) |

---

## Deployment Steps

### 1. Set Environment Variables

1. Navigate to Vercel Dashboard
2. Select **backend** project
3. Go to Settings → Environment Variables
4. Add all backend variables listed above
5. Select **frontend** project
6. Add all frontend variables listed above

### 2. Redeploy Both Services

```bash
# Redeploy backend (to load new environment variables)
cd phase-2-web/backend
npx vercel --prod

# Redeploy frontend (to load new backend URL)
cd phase-2-web/frontend
npx vercel --prod
```

### 3. Run Database Migrations

**IMPORTANT:** Alembic migrations cannot run automatically in Vercel serverless.

**Option A: Run migrations locally against Neon DB:**
```bash
cd phase-2-web/backend

# Set DATABASE_URL to Neon
export DATABASE_URL="postgresql+asyncpg://neondb_owner:<YOUR_PASSWORD>@ep-weathered-resonance-adok3vmj-pooler.c-2.us-east-1.aws.neon.tech/neondb?ssl=require"

# Run migrations
uv run alembic upgrade head
```

**Option B: Use Neon SQL Editor:**
- Go to https://console.neon.tech
- Open SQL Editor
- Run migration SQL manually

### 4. Test Production Deployment

```bash
# Test backend health
curl https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app/health

# Test registration
curl -X POST https://backend-r16dl2hxm-muhammadyaseen200s-projects.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Visit frontend
open https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app
```

---

## Troubleshooting

### Backend Returns 500 Error

**Cause:** Environment variables not set or incorrect DATABASE_URL format

**Fix:**
1. Check Vercel dashboard environment variables
2. Ensure `DATABASE_URL` uses `postgresql+asyncpg://` (not `postgresql://`)
3. Redeploy: `npx vercel --prod`

### Frontend Cannot Connect to Backend

**Cause:** CORS_ORIGINS doesn't include frontend URL

**Fix:**
1. Update backend `CORS_ORIGINS` to include: `https://frontend-k77768se5-muhammadyaseen200s-projects.vercel.app`
2. Redeploy backend: `npx vercel --prod`

### Database Tables Don't Exist

**Cause:** Migrations not run on Neon DB

**Fix:**
```bash
# Local migration against Neon
export DATABASE_URL="postgresql+asyncpg://neondb_owner:<YOUR_PASSWORD>@..."
uv run alembic upgrade head
```

---

## Security Notes

- ✅ `.env` is gitignored (not committed)
- ✅ Neon password rotated (stored ONLY in Vercel environment variables)
- ✅ No credentials in git-tracked files
- ⚠️ Backend deployment protection enabled (requires Vercel auth)

---

**Last Updated:** 2025-12-31
