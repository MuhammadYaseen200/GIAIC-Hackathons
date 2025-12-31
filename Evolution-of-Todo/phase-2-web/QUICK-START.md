# Vercel Deployment Quick Start

**One-command deployment for Evolution-of-Todo Phase 2**

---

## Prerequisites (One-Time Setup)

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Get Neon Database URL
# Go to: https://console.neon.tech
# Create database → Copy connection string
```

---

## Deploy to Production

### Windows (PowerShell)

```powershell
cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo\phase-2-web

.\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://user:pass@host/db?ssl=require"
```

### Linux/macOS (Bash)

```bash
cd ~/projects/Evolution-of-Todo/phase-2-web

chmod +x deploy-to-vercel.sh  # First time only

./deploy-to-vercel.sh --database-url "postgresql+asyncpg://user:pass@host/db?ssl=require"
```

---

## What Happens

1. Generates secure JWT secret
2. Sets backend environment variables (DATABASE_URL, SECRET_KEY, CORS_ORIGINS)
3. Sets frontend environment variables (NEXT_PUBLIC_API_URL, BACKEND_URL)
4. Deploys backend to Vercel
5. Deploys frontend to Vercel
6. Saves deployment record

---

## Post-Deployment (REQUIRED)

### Run Database Migrations

```bash
cd backend
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db?ssl=require"
uv run alembic upgrade head
```

### Test Deployment

```bash
# Test backend health
curl https://backend-xyz.vercel.app/health

# Open frontend
open https://frontend-xyz.vercel.app
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Vercel CLI not found" | `npm install -g vercel` |
| "Not logged into Vercel" | `vercel login` |
| Backend 500 error | Run database migrations |
| CORS error | Check backend `CORS_ORIGINS` includes frontend URL |

---

## Full Documentation

See `VERCEL-AUTOMATION-GUIDE.md` for:
- Advanced options
- Security best practices
- CI/CD integration
- Cost optimization
- Troubleshooting guide

---

**Need Help?** Check deployment record: `vercel-deployment-*.txt`
