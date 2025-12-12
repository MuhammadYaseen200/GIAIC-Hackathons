# ADR-001: Deployment Strategy - GitHub Pages + Railway vs. Vercel Monolith

**Status**: Accepted
**Date**: 2025-12-12
**Context**: Feature 001-physical-ai-textbook
**Deciders**: System (Claude Sonnet 4.5), pending human approval

## Context and Problem Statement

The textbook requires both static content serving (Docusaurus) and dynamic backend features (RAG chatbot, authentication, personalization, translation). We need to decide between:

1. **Hybrid deployment**: GitHub Pages (frontend) + Railway/Render (backend)
2. **Monolith deployment**: Vercel with Next.js API routes handling both concerns

This decision impacts development velocity, operational complexity, cost, and alignment with JAMstack best practices.

## Decision Drivers

- **Performance**: Static site delivery must be fast (<3s page load)
- **Cost**: Must stay within free tiers (GitHub Pages free, Railway free tier sufficient)
- **Development simplicity**: Minimize context-switching between frontend and backend
- **Scalability**: Support 50 concurrent users without degradation
- **Hackathon timeline**: Nov 30, 2025 deadline requires rapid iteration

## Considered Options

### Option A: Hybrid Deployment (GitHub Pages + Railway)

**Architecture**:
- **Frontend**: Docusaurus static site on GitHub Pages
- **Backend**: FastAPI microservice on Railway (or Render/Vercel Serverless as fallback)
- **Communication**: Frontend calls backend API via fetch() for chatbot, auth, personalization, translation

**Pros**:
- ✅ **Static site performance**: Docusaurus served via CDN, ~1s page load
- ✅ **Separation of concerns**: Frontend (content) and backend (intelligence) cleanly separated
- ✅ **Technology fit**: Docusaurus optimized for documentation sites (built-in search, versioning, navigation)
- ✅ **Free tier alignment**: GitHub Pages unlimited static hosting, Railway free tier sufficient for FastAPI
- ✅ **Independent scaling**: Can scale backend without redeploying frontend

**Cons**:
- ❌ **CORS complexity**: Need to configure cross-origin requests (mitigated by Railway CORS middleware)
- ❌ **Dual deployment**: Must deploy frontend and backend separately (mitigated by GitHub Actions CI/CD)
- ❌ **Environment management**: Two `.env` files (frontend for API URL, backend for secrets)

### Option B: Vercel Monolith (Next.js API Routes)

**Architecture**:
- **Framework**: Next.js with App Router (combines SSG for content + API routes for backend)
- **Deployment**: Single Vercel deployment
- **Communication**: API routes handled by serverless functions in same codebase

**Pros**:
- ✅ **Single deployment**: One `vercel deploy` command
- ✅ **No CORS issues**: API routes on same domain
- ✅ **Unified codebase**: TypeScript for both frontend and backend

**Cons**:
- ❌ **SSR overhead**: Next.js more complex than Docusaurus for pure static content
- ❌ **API route limitations**: Vercel serverless functions have 10s timeout (tight for GPT-4 personalization)
- ❌ **Python incompatibility**: Would require Node.js backend (FastAPI chosen for RAG ecosystem compatibility)
- ❌ **Docusaurus features lost**: Built-in search, sidebar generation, versioning not native to Next.js
- ❌ **Learning curve**: Team more familiar with Docusaurus for docs sites

## Decision Outcome

**Chosen option**: **Option A - Hybrid Deployment (GitHub Pages + Railway)**

**Rationale**:
1. **Docusaurus is purpose-built for documentation**: Built-in features (search, navigation, versioning, mobile responsiveness) align perfectly with textbook requirements. Next.js would require rebuilding these features.
2. **FastAPI chosen for RAG stack**: Python ecosystem (Qdrant client, OpenAI SDK, LangChain if needed) is more mature for RAG than Node.js alternatives. Switching to Next.js API routes would require rewriting in TypeScript.
3. **Static performance critical**: Textbook content must load instantly for good user experience. Docusaurus CDN delivery achieves <1s page load. Next.js SSR adds unnecessary complexity.
4. **CORS complexity is manageable**: FastAPI CORS middleware configuration is 5 lines of code. This is a non-issue compared to losing Docusaurus benefits.
5. **Alignment with constitution Principle III (Agent-First Architecture)**: Separating concerns enables specialized agents (Writer Agent for content, RAG Agent for backend) to work independently without conflicts.

### Consequences

**Positive**:
- Frontend and backend can be developed in parallel by different agents
- Static content serves from CDN (GitHub Pages) at optimal speed
- Backend can be swapped (Railway → Render → Vercel Serverless) without frontend changes
- Docusaurus plugin ecosystem available (Algolia search, mermaid diagrams, code highlighting)

**Negative**:
- Need to configure CORS headers in FastAPI
- Two deployment pipelines in CI/CD (acceptable complexity)
- API URL must be environment variable in frontend (handled via Docusaurus config)

### Implementation Notes

**Frontend deployment** (GitHub Pages):
```bash
# In docusaurus.config.js
module.exports = {
  url: 'https://<username>.github.io',
  baseUrl: '/Humanoid-Robots-Book/',
  organizationName: '<username>',
  projectName: 'Humanoid-Robots-Book',
};

# Deploy
npm run deploy  # Builds and pushes to gh-pages branch
```

**Backend deployment** (Railway):
```yaml
# railway.toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"

[env]
ALLOWED_ORIGINS = "https://<username>.github.io"  # For CORS
```

**CORS configuration** (FastAPI):
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://<username>.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Links

- **Feature spec**: specs/001-physical-ai-textbook/spec.md
- **Implementation plan**: specs/001-physical-ai-textbook/plan.md
- **Related ADRs**: ADR-002 (Better Auth integration), ADR-003 (RAG chunking strategy)
