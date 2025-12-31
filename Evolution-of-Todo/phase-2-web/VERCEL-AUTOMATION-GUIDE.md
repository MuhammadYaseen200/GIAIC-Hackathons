# Vercel Deployment Automation Guide

**Evolution of Todo - Phase 2**

This guide documents the automated deployment system for deploying the full-stack Todo application to Vercel with a single command.

---

## Quick Start

### Prerequisites

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Authenticate with Vercel:**
   ```bash
   vercel login
   ```

3. **Prepare Neon Database:**
   - Create a PostgreSQL database at [console.neon.tech](https://console.neon.tech)
   - Copy the connection string (format: `postgresql+asyncpg://user:pass@host/db?ssl=require`)

---

## Usage

### Windows (PowerShell)

```powershell
# Navigate to phase-2-web directory
cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo\phase-2-web

# Run deployment script
.\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://user:pass@host/db?ssl=require"
```

**Advanced options:**
```powershell
# Specify custom URLs (if already deployed)
.\deploy-to-vercel.ps1 `
    -DatabaseUrl "postgresql+asyncpg://..." `
    -FrontendUrl "https://my-frontend.vercel.app" `
    -BackendUrl "https://my-backend.vercel.app"

# Only update environment variables (don't redeploy)
.\deploy-to-vercel.ps1 -DatabaseUrl "postgresql+asyncpg://..." -SkipDeploy
```

### Linux/macOS (Bash)

```bash
# Navigate to phase-2-web directory
cd ~/projects/Evolution-of-Todo/phase-2-web

# Make script executable (first time only)
chmod +x deploy-to-vercel.sh

# Run deployment script
./deploy-to-vercel.sh --database-url "postgresql+asyncpg://user:pass@host/db?ssl=require"
```

**Advanced options:**
```bash
# Specify custom URLs
./deploy-to-vercel.sh \
    --database-url "postgresql+asyncpg://..." \
    --frontend-url "https://my-frontend.vercel.app" \
    --backend-url "https://my-backend.vercel.app"

# Only update environment variables
./deploy-to-vercel.sh --database-url "postgresql+asyncpg://..." --skip-deploy
```

---

## What the Script Does

### 1. Prerequisite Validation
- Verifies Vercel CLI is installed
- Confirms Python 3.13+ is available
- Checks project directory structure
- Validates Vercel authentication

### 2. Secret Generation
- Generates cryptographically secure 256-bit JWT secret using Python's `secrets` module
- Uses `token_urlsafe()` for URL-safe base64 encoding

### 3. URL Resolution
- Auto-detects backend and frontend URLs from existing Vercel projects
- Falls back to interactive prompts if auto-detection fails
- Constructs CORS origins JSON array

### 4. Environment Configuration

**Backend Variables:**
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon PostgreSQL connection | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing secret | Auto-generated |
| `CORS_ORIGINS` | Allowed frontend domains | `["https://frontend.vercel.app"]` |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `1440` (24 hours) |

**Frontend Variables:**
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend URL (client-side) | `https://backend.vercel.app` |
| `BACKEND_URL` | Backend URL (server-side) | `https://backend.vercel.app` |

### 5. Production Deployment
- Deploys backend with `vercel --prod --yes`
- Deploys frontend with `vercel --prod --yes`
- Both services are deployed to production environment

### 6. Post-Deployment
- Generates timestamped deployment record file
- Provides database migration instructions
- Displays verification commands

---

## Environment Variable Management

### How Variables Are Set

The scripts use the Vercel CLI to programmatically set environment variables:

```bash
# Remove existing variable (idempotent)
vercel env rm VARIABLE_NAME production --yes

# Add new variable
echo "value" | vercel env add VARIABLE_NAME production
```

### Why Remove Before Add?

Vercel CLI `env add` fails if the variable already exists. The script removes it first to ensure idempotent behavior.

### Scope: Production Only

All variables are scoped to `production` environment. Preview and development deployments will NOT inherit these values.

To add variables to other environments:
```bash
vercel env add VARIABLE_NAME preview < value.txt
vercel env add VARIABLE_NAME development < value.txt
```

---

## Database Migrations

**CRITICAL:** Vercel serverless functions cannot run Alembic migrations automatically.

### Migration Workflow

1. **After first deployment:**
   ```bash
   cd backend
   export DATABASE_URL="postgresql+asyncpg://user:pass@host/db?ssl=require"
   uv run alembic upgrade head
   ```

2. **For schema changes:**
   ```bash
   # Create migration locally
   uv run alembic revision --autogenerate -m "add new column"

   # Apply to production database
   export DATABASE_URL="postgresql+asyncpg://..."
   uv run alembic upgrade head

   # Commit migration file
   git add alembic/versions/*.py
   git commit -m "feat: add database migration"
   git push

   # Redeploy backend (picks up new migration files)
   vercel --prod
   ```

### Alternative: Neon SQL Editor

1. Go to [console.neon.tech](https://console.neon.tech)
2. Open your database's SQL Editor
3. Paste migration SQL manually
4. Execute

---

## Verification Checklist

After running the deployment script:

### 1. Backend Health Check
```bash
# Should return {"status": "healthy"}
curl https://backend-xyz.vercel.app/health
```

### 2. Frontend Access
Open `https://frontend-xyz.vercel.app` in browser. Should see login page.

### 3. Registration Test
```bash
curl -X POST https://backend-xyz.vercel.app/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"SecurePass123"}'
```

Expected response:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "test@example.com"
    },
    "access_token": "eyJ..."
  }
}
```

### 4. Task CRUD Operations

Via frontend UI:
1. Register a new account
2. Create a task
3. Mark task as complete
4. Edit task title
5. Delete task

All operations should persist and reload correctly.

---

## Troubleshooting

### Error: "Vercel CLI not found"

**Cause:** Vercel CLI not installed globally

**Fix:**
```bash
npm install -g vercel

# Verify installation
vercel --version
```

### Error: "Not logged into Vercel"

**Cause:** No active Vercel authentication

**Fix:**
```bash
vercel login

# Follow browser authentication flow
```

### Error: "Failed to generate secret key"

**Cause:** Python not available or `secrets` module missing

**Fix:**
```bash
# Verify Python installation
python --version  # or python3 --version

# Should be 3.13 or higher
```

### Error: "Could not auto-detect backend URL"

**Cause:** No prior Vercel deployment exists

**Fix:**
1. Deploy manually first:
   ```bash
   cd backend
   vercel --prod
   ```

2. Note the deployed URL

3. Re-run script with `--backend-url`:
   ```bash
   ./deploy-to-vercel.sh \
       --database-url "postgresql+asyncpg://..." \
       --backend-url "https://backend-xyz.vercel.app"
   ```

### Error: "Backend returns 500 Internal Server Error"

**Cause:** Environment variables not applied or database unreachable

**Fix:**
1. Check Vercel dashboard environment variables:
   - Go to project settings → Environment Variables
   - Verify all backend variables are present

2. Verify database URL format:
   ```
   postgresql+asyncpg://user:pass@host:port/dbname?ssl=require
   ```

3. Test database connectivity:
   ```bash
   # Install psql client
   sudo apt install postgresql-client  # Linux
   brew install libpq  # macOS

   # Test connection
   psql "postgresql://user:pass@host:port/dbname?sslmode=require"
   ```

4. Redeploy backend:
   ```bash
   cd backend
   vercel --prod
   ```

### Error: "CORS policy blocked"

**Cause:** Frontend URL not in backend `CORS_ORIGINS`

**Fix:**
1. Verify frontend URL is correct:
   ```bash
   curl https://backend-xyz.vercel.app/health
   # Check CORS headers in response
   ```

2. Update `CORS_ORIGINS` in Vercel dashboard:
   ```json
   ["https://frontend-abc.vercel.app", "https://frontend-xyz.vercel.app"]
   ```

3. Redeploy backend:
   ```bash
   cd backend
   vercel --prod
   ```

### Error: "relation 'users' does not exist"

**Cause:** Database migrations not run

**Fix:**
```bash
cd backend
export DATABASE_URL="postgresql+asyncpg://user:pass@host/db?ssl=require"
uv run alembic upgrade head
```

### Error: "Invalid JWT token"

**Cause:** Mismatched `SECRET_KEY` between deployments

**Fix:**
1. Generate new secret:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Update in Vercel dashboard backend environment variables

3. Redeploy backend:
   ```bash
   cd backend
   vercel --prod
   ```

4. Clear browser cookies and re-login

---

## Security Best Practices

### 1. Never Commit Secrets
- `.env` files are gitignored
- Deployment records (`vercel-deployment-*.txt`) contain masked secrets
- Always use environment variables for sensitive data

### 2. Rotate Credentials Regularly
```bash
# Generate new JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Update in Vercel
echo "NEW_SECRET" | vercel env add SECRET_KEY production

# Redeploy
cd backend && vercel --prod
```

### 3. Restrict CORS Origins
Only allow specific frontend domains:
```json
["https://frontend-prod.vercel.app"]
```

Never use wildcards in production:
```json
["*"]  // INSECURE - DO NOT USE
```

### 4. Monitor Vercel Logs
- Check deployment logs for errors: [vercel.com/dashboard](https://vercel.com/dashboard)
- Enable error tracking (Sentry, LogRocket) for production

### 5. Database Connection Pooling
Neon automatically handles connection pooling. Use pooler endpoints:
```
postgresql+asyncpg://user:pass@ep-xyz-pooler.region.aws.neon.tech/db
```

Not direct endpoints:
```
postgresql+asyncpg://user:pass@ep-xyz.region.aws.neon.tech/db
```

---

## Advanced Workflows

### Multi-Environment Deployments

Deploy to preview environment:
```bash
# Set preview environment variables
cd backend
echo "DEV_DATABASE_URL" | vercel env add DATABASE_URL preview

# Deploy to preview
vercel
```

### Custom Domain Setup

1. Add custom domain in Vercel dashboard:
   - Go to project → Settings → Domains
   - Add `api.yourdomain.com` (backend)
   - Add `app.yourdomain.com` (frontend)

2. Update environment variables:
   ```bash
   # Backend CORS
   echo '["https://app.yourdomain.com"]' | vercel env add CORS_ORIGINS production

   # Frontend API URL
   echo "https://api.yourdomain.com" | vercel env add NEXT_PUBLIC_API_URL production
   ```

3. Redeploy both services

### Automated CI/CD with GitHub Actions

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Vercel Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel

      - name: Deploy Backend
        working-directory: ./phase-2-web/backend
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_BACKEND_PROJECT_ID }}
        run: |
          vercel pull --yes --environment=production --token=$VERCEL_TOKEN
          vercel build --prod --token=$VERCEL_TOKEN
          vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN

      - name: Deploy Frontend
        working-directory: ./phase-2-web/frontend
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
          VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
          VERCEL_PROJECT_ID: ${{ secrets.VERCEL_FRONTEND_PROJECT_ID }}
        run: |
          vercel pull --yes --environment=production --token=$VERCEL_TOKEN
          vercel build --prod --token=$VERCEL_TOKEN
          vercel deploy --prebuilt --prod --token=$VERCEL_TOKEN
```

Required GitHub Secrets:
- `VERCEL_TOKEN`: Get from [vercel.com/account/tokens](https://vercel.com/account/tokens)
- `VERCEL_ORG_ID`: Run `vercel whoami` to find team/user ID
- `VERCEL_BACKEND_PROJECT_ID`: Found in `.vercel/project.json` after first deploy
- `VERCEL_FRONTEND_PROJECT_ID`: Found in `.vercel/project.json` after first deploy

---

## Deployment Records

Each script execution generates a timestamped record file:

**Filename:** `vercel-deployment-YYYYMMDD-HHMMSS.txt`

**Contents:**
- Deployment timestamp
- Deployer username
- Frontend/backend URLs
- Environment variable summary (secrets masked)
- Post-deployment action checklist

**Example:**
```
vercel-deployment-20251231-143022.txt
```

**Location:** `phase-2-web/vercel-deployment-*.txt`

These files should be gitignored but can be saved to a secure password manager or secrets vault.

---

## Cost Optimization

### Vercel Pricing Tiers

- **Hobby (Free):**
  - 100 GB bandwidth/month
  - 100 deployments/day
  - Serverless function execution: 100 GB-hours
  - Suitable for development and low-traffic demos

- **Pro ($20/month):**
  - 1 TB bandwidth
  - Unlimited deployments
  - Advanced analytics
  - Required for production workloads

### Neon Pricing Tiers

- **Free:**
  - 10 databases
  - 0.5 GB storage
  - Autosuspends after inactivity
  - Suitable for demos

- **Pro ($19/month):**
  - Unlimited databases
  - 10 GB storage
  - No autosuspend
  - Required for production

### Optimization Tips

1. **Enable Vercel Edge Caching:**
   ```typescript
   // frontend/app/api/tasks/route.ts
   export const revalidate = 60 // Cache for 60 seconds
   ```

2. **Use Neon Connection Pooling:**
   ```python
   # backend/app/core/database.py
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=5,  # Limit concurrent connections
       max_overflow=10
   )
   ```

3. **Monitor Usage:**
   - Vercel: [vercel.com/dashboard/usage](https://vercel.com/dashboard/usage)
   - Neon: [console.neon.tech/usage](https://console.neon.tech/usage)

---

## References

### Official Documentation
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Neon PostgreSQL Documentation](https://neon.tech/docs/introduction)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Next.js Vercel Deployment](https://nextjs.org/docs/deployment)

### Related Files
- `phase-2-web/backend/.env.example` - Backend environment variables template
- `phase-2-web/frontend/.env.local` - Frontend environment variables
- `phase-2-web/DEPLOYMENT.md` - Manual deployment instructions
- `phase-2-web/vercel-env-setup.txt` - Generated environment variables

### Project Context
- `CLAUDE.md` - Project constitution and phase specifications
- `specs/overview.md` - Architecture overview
- `history/adr/ADR-004-jwt-authentication.md` - JWT auth architecture
- `history/adr/ADR-006-alembic-migrations.md` - Database migration strategy

---

**Version:** 1.0.0
**Last Updated:** 2025-12-31
**Maintainer:** DevOps & RAG Engineer
**License:** MIT
