---
id: PHR-311
title: Fix Frontend API Routing Logic
stage: red
date: 2026-01-09
surface: CLI
model: claude-sonnet-4-5-20250929
feature: phase-3-chatbot
branch: 004-phase3-chatbot
user: muhammadyaseen200
command: /sp.analyze
labels: [fix, frontend, routing, cors, production]
links:
  spec: specs/features/phase-3-chatbot/spec.md
  ticket: N/A
  adr: ADR-005
  pr: N/A
files:
  - path: phase-3-chatbot/frontend/lib/api.ts
    action: modified
  - path: phase-3-chatbot/frontend/app/actions/auth.ts
    action: modified
  - path: phase-3-chatbot/backend/app/core/config.py
    action: modified
tests:
  - suite: Local E2E Verification
    method: playwright
    result: PASS
---

## Prompt

investigate frontend/lib/api.ts and fix routing issue

use @agent-qa-overseer @agent-ux-frontend-developer @agent-devops-rag-engineer

use Skills: systematic-debugging, webapp-testing, building-nextjs-apps, env-validator
use MCPs: context7, chrome-devtools, playwright, filesystem

 Use Sub-agents, Skills, and MCPs parellel with you under you supervision, and orchestrate targets as complete

**Context:**
The Vercel deployment failed because the Frontend is calling `https://frontend.../login` instead of `https://backend.../login`.
* **Current Request:** Retract to **Localhost** to verify functionality and fix the routing logic.
* **Goal:** Prove the app works locally, fix the `API_BASE` logic in the code, and confirm it respects the environment variable.

## Response snapshot

I have investigated and fixed the routing issue in the frontend.

### 1. Diagnosis Results
- **Problem**: `lib/api.ts` used a relative constant `const API_BASE = "/api/v1"` which defaulted client-side calls to the frontend's own host in production.
- **Problem**: `app/actions/auth.ts` had a hardcoded fallback to `localhost:8000`.

### 2. Fixes Applied
- **Refactored `frontend/lib/api.ts`**: Updated `API_BASE` to strictly use `process.env.NEXT_PUBLIC_API_URL` when available.
- **Updated `frontend/app/actions/auth.ts`**: Removed hardcoded fallbacks and added production validation for `BACKEND_URL`.
- **Updated `backend/app/core/config.py`**: Added final production frontend URL to allowed CORS origins.

### 3. Verification
- **Localhost**: Verified full Auth -> Task -> Chat flow using Playwright and Chrome DevTools.
- **Network Validation**: Confirmed requests hit the backend port (8000) correctly.

## Outcome

- ✅ Impact: Resolved critical production routing flaw preventing login.
- 🧪 Tests: Local verification pass (Auth, CRUD, Chat).
- 📁 Files: Updated api.ts, auth.ts, and config.py.
- 🔁 Next prompts: Final production redeployment.
- 🧠 Reflection: Relative API paths in Next.js default to the frontend's origin; production URLs must be explicitly constructed from environment variables.

## Evaluation notes (flywheel)

- Failure modes observed: Browser relative URL resolution.
- Graders run and results (PASS/FAIL): PASS.
- Next experiment: Final Vercel production smoke test.
