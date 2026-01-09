# Vercel Deployment Preflight Checklist

## Overview
This checklist ensures proper deployment configuration for the Evolution of Todo full-stack application on Vercel, featuring a Next.js frontend and FastAPI backend.

## Architecture Summary
- **Frontend**: Next.js 15+ application deployed to Vercel
- **Backend**: FastAPI application deployed to Vercel as serverless functions
- **Database**: Neon Serverless PostgreSQL
- **Authentication**: JWT tokens stored in httpOnly cookies
- **API Routing**: Next.js rewrites proxy frontend `/api` requests to backend

## Required Environment Variables

### Backend Environment Variables (Production)
These must be set in the Vercel backend project settings:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `DATABASE_URL` | ✅ | Neon PostgreSQL connection string with ssl=require | `postgresql+asyncpg://user:pass@ep-xyz.region.aws.neon.tech/db?ssl=require` |
| `SECRET_KEY` | ✅ | JWT signing secret (32+ char random string) | `generated_with_python_secrets_module` |
| `ALGORITHM` | ✅ | JWT algorithm | `HS256` (default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ | Token expiration time | `1440` (24 hours) |
| `CORS_ORIGINS` | ✅ | JSON array of allowed frontend origins | `["https://frontend-xyz.vercel.app"]` |

### Frontend Environment Variables (Production)
These must be set in the Vercel frontend project settings:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | ✅ | Backend URL for client-side API calls | `https://backend-xyz.vercel.app` |
| `BACKEND_URL` | ✅ | Backend URL for server-side API calls | `https://backend-xyz.vercel.app` |

## Vercel Project Setup

### 1. Backend Project Configuration
- [ ] Create Vercel project for backend
- [ ] Set framework preset to "Other" (since it's FastAPI, not a standard Python framework)
- [ ] Set root directory to `phase-2-web/backend`
- [ ] Set build command to `pip install -r requirements.txt`
- [ ] Set output directory to leave blank (serverless functions)
- [ ] Set dev command to `uv run uvicorn app.main:app --reload`

### 2. Frontend Project Configuration
- [ ] Create Vercel project for frontend
- [ ] Set framework preset to "Next.js"
- [ ] Set root directory to `phase-2-web/frontend`
- [ ] Leave build command as default (auto-detected)
- [ ] Leave output directory as default
- [ ] Leave dev command as default

### 3. Environment Variables Setup
- [ ] Add backend environment variables to backend Vercel project
- [ ] Add frontend environment variables to frontend Vercel project
- [ ] Verify CORS_ORIGINS includes the frontend deployment URL
- [ ] Verify NEXT_PUBLIC_API_URL and BACKEND_URL point to backend deployment URL

## Route Configuration Analysis

### Backend Routes (vercel.json)
The backend `vercel.json` properly configures routing:
- `/api/(.*)` → routes API requests to FastAPI
- `/health` → health check endpoint
- `/docs` → Swagger docs
- `/openapi.json` → OpenAPI spec
- `/(.*)` → fallback route for any other backend requests

### Frontend Routes (next.config.ts)
The frontend `next.config.ts` properly configures rewrites:
- `/api/:path*` → rewrites to backend API
- Maintains frontend routes for UI pages

## Deployment Sequence

### 1. Deploy Backend First
- [ ] Deploy backend to Vercel first to get production URL
- [ ] Note the backend deployment URL (e.g., `https://backend-xyz.vercel.app`)

### 2. Configure Frontend Environment
- [ ] Set `NEXT_PUBLIC_API_URL` to backend URL
- [ ] Set `BACKEND_URL` to backend URL

### 3. Deploy Frontend
- [ ] Deploy frontend after backend environment variables are configured

### 4. Update Backend CORS
- [ ] Add frontend URL to backend's `CORS_ORIGINS` variable
- [ ] Redeploy backend to apply CORS changes

## Security Considerations

### JWT Configuration
- [ ] Use strong `SECRET_KEY` (minimum 32 random characters)
- [ ] Set appropriate `ACCESS_TOKEN_EXPIRE_MINUTES` (recommended 1440 for 24 hours)
- [ ] Never commit secrets to version control

### CORS Configuration
- [ ] `CORS_ORIGINS` should only include trusted domains
- [ ] Do not use wildcard `["*"]` in production
- [ ] Include both frontend deployment URL and localhost for development

### Database Security
- [ ] Use Neon connection pooling endpoint if available
- [ ] Ensure `ssl=require` parameter is present in `DATABASE_URL`
- [ ] Enable Neon's branch protection for production data

## Verification Steps

### 1. Backend Health Check
- [ ] Visit `https://backend-[hash].vercel.app/health`
- [ ] Should return `{"status": "healthy"}`

### 2. Backend API Endpoints
- [ ] Visit `https://backend-[hash].vercel.app/docs`
- [ ] Should show Swagger documentation

### 3. Frontend Access
- [ ] Visit frontend deployment URL
- [ ] Should load the application without errors

### 4. API Proxy Functionality
- [ ] Register a new user through the frontend
- [ ] Verify the request reaches the backend successfully
- [ ] Verify JWT tokens are handled properly with httpOnly cookies

### 5. Database Connectivity
- [ ] Create a test task
- [ ] Verify it persists in the Neon database
- [ ] Verify data isolation between users

## Common Issues & Solutions

### Issue: CORS Errors
**Symptoms**: Browser shows CORS errors when calling backend APIs
**Solution**: Verify `CORS_ORIGINS` includes the frontend URL and redeploy backend

### Issue: Database Connection Failures
**Symptoms**: 500 errors from backend with database connection errors
**Solution**: Verify `DATABASE_URL` format and SSL parameter

### Issue: Authentication Failures
**Symptoms**: Login/register works but subsequent requests fail
**Solution**: Verify `SECRET_KEY` is consistent and properly formatted

### Issue: API Requests Not Routing
**Symptoms**: Frontend `/api` requests return 404
**Solution**: Verify next.config.ts rewrite configuration and backend deployment

## Rollback Plan

### In Case of Deployment Failure
1. Keep previous deployment URLs available
2. Use Vercel dashboard to rollback to previous version
3. Verify database integrity after rollback
4. Update environment variables as needed

## Post-Deployment Tasks

### 1. Database Migrations
- [ ] Run initial database migrations via Alembic
- [ ] Execute: `uv run alembic upgrade head` with production DATABASE_URL

### 2. Monitoring Setup
- [ ] Set up error monitoring (Sentry, etc.)
- [ ] Configure performance monitoring
- [ ] Set up health check monitoring

### 3. Custom Domain Configuration (Optional)
- [ ] Add custom domains to both projects in Vercel dashboard
- [ ] Update environment variables to reflect custom domains
- [ ] Update CORS configuration accordingly

---

**Last Updated**: January 8, 2026
**Version**: 1.0
**Author**: DevOps & RAG Engineer