# Vercel Deployment Preparation Guide for Evolution of Todo

## Current Status
- ✅ Vercel CLI installed (version 50.0.1)
- ✅ Project structure verified (frontend + backend in phase-3-chatbot/)
- ✅ Vercel configuration fixed (root vercel.json now correctly references api/index.py)
- ✅ Backend API compatible with Vercel serverless functions
- ✅ Frontend configured with proper API proxy rewrites

## Deployment Architecture
```
Root Domain (e.g., https://evolution-of-todo.vercel.app/)
├── /api/* → Backend FastAPI service
│   ├── /api/v1/auth/*
│   ├── /api/v1/tasks/*
│   ├── /health
│   ├── /docs
│   └── /openapi.json
└── /* → Frontend Next.js application
    ├── /
    ├── /login
    ├── /register
    └── /dashboard
```

## Required Environment Variables

### Backend Environment Variables (for Vercel)
```bash
# Database Configuration (Production - Neon PostgreSQL recommended)
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.us-east-2.aws.neon.tech/dbname?sslmode=require

# JWT Security
SECRET_KEY=generate-with-python-secrets-token-urlsafe-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS Configuration (Frontend URL)
CORS_ORIGINS=["https://your-frontend-domain.vercel.app"]
```

### Frontend Environment Variables (for Vercel)
```bash
# Backend API URL
NEXT_PUBLIC_API_URL=https://your-backend-domain.vercel.app
BACKEND_URL=https://your-backend-domain.vercel.app
```

## Pre-Deployment Checklist

### 1. Vercel Account Setup
- [ ] Vercel CLI installed (`vercel --version`)
- [ ] Logged into Vercel account (`vercel login`)
- [ ] Team/organization access confirmed if deploying to team project

### 2. Database Setup
- [ ] Neon PostgreSQL database created
- [ ] Database connection string ready (asyncpg format)
- [ ] SSL certificate properly configured for production

### 3. Security Configuration
- [ ] JWT SECRET_KEY generated securely (256-bit random string)
- [ ] CORS origins properly configured for production domain
- [ ] No sensitive data in version control

### 4. Code Verification
- [ ] Backend: `api/index.py` properly imports `app.main:app`
- [ ] Frontend: `next.config.ts` correctly proxies API requests
- [ ] All dependencies listed in `requirements.txt` and `package.json`
- [ ] No local-specific configurations in code

### 5. Testing Verification
- [ ] Local development works: `cd phase-3-chatbot/backend && uv run uvicorn app.main:app --reload`
- [ ] Local frontend works: `cd phase-3-chatbot/frontend && npm run dev`
- [ ] API endpoints accessible via frontend proxy
- [ ] Authentication flow works end-to-end

## Deployment Commands

### Individual Service Deployment
```bash
# Deploy backend only
cd phase-3-chatbot/backend && vercel --prod

# Deploy frontend only
cd phase-3-chatbot/frontend && vercel --prod

# Link projects if deploying separately
cd phase-3-chatbot/backend && vercel link
cd phase-3-chatbot/frontend && vercel link
```

### Monorepo Deployment (Recommended)
```bash
# Deploy both services from root
cd /path/to/Evolution-of-Todo && vercel --prod
```

### Setting Environment Variables via CLI
```bash
# Backend environment variables
cd phase-3-chatbot/backend
vercel env add DATABASE_URL production
vercel env add SECRET_KEY production
vercel env add CORS_ORIGINS production

# Frontend environment variables
cd phase-3-chatbot/frontend
vercel env add NEXT_PUBLIC_API_URL production
```

## Post-Deployment Steps

### 1. Database Migrations
After backend deployment, run database migrations manually:
```bash
# SSH into deployed backend or run locally with production DATABASE_URL
cd phase-3-chatbot/backend
export DATABASE_URL="your-production-database-url"
uv run alembic upgrade head
```

### 2. Health Checks
- [ ] Backend health endpoint: `https://your-backend-domain.vercel.app/health`
- [ ] Frontend loads: `https://your-frontend-domain.vercel.app/`
- [ ] API documentation: `https://your-backend-domain.vercel.app/docs`
- [ ] Cross-origin requests work between frontend and backend

### 3. Functional Testing
- [ ] User registration works
- [ ] User login works
- [ ] Task CRUD operations work
- [ ] Authentication tokens properly handled

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `api/index.py` correctly imports the FastAPI app
2. **CORS Issues**: Verify CORS_ORIGINS includes your frontend domain
3. **Database Connection**: Check DATABASE_URL format and SSL settings
4. **Environment Variables**: Confirm all required vars are set in Vercel dashboard

### Debugging Tips
- Check Vercel deployment logs in dashboard
- Verify `api/index.py` exports the app as `app`
- Test API endpoints directly via browser
- Enable detailed logging during initial deployment

## Rollback Plan
- Keep previous deployment URLs for quick rollback
- Maintain local development environment as fallback
- Document deployment hashes/tags for version control