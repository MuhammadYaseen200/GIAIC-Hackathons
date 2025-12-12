---
id: 3
title: Create implementation plan with ADRs
stage: plan
date: 2025-12-12
surface: agent
model: claude-sonnet-4-5
feature: 001-physical-ai-textbook
branch: 001-physical-ai-textbook
user: system
command: /sp.plan
labels: ["planning", "architecture", "adr", "technical-design"]
links:
  spec: specs/001-physical-ai-textbook/spec.md
  ticket: null
  adr: history/adr/001-deployment-strategy.md, history/adr/002-better-auth-integration.md, history/adr/003-rag-chunking-strategy.md
  pr: null
files:
 - specs/001-physical-ai-textbook/plan.md
 - history/adr/001-deployment-strategy.md
 - history/adr/002-better-auth-integration.md
 - history/adr/003-rag-chunking-strategy.md
tests:
 - Constitution Check validation (PASSED with 1 complexity justification)
---

## Prompt

/sp.plan

Create: Development roadmap, technical architecture diagram, chapter generation workflow, and RAG integration strategy.
Decisions needing documentation:
- Cloud (AWS/Azure) vs. Local (Jetson) simulation tradeoffs.
- RAG backend stack choice (FastAPI vs. Next.js API routes).
- Better-Auth integration method (client-side vs. server-side).

Testing strategy:
- Automated link checking for Docusaurus.
- RAG accuracy tests (ground truth Q&A pairs).
- User journey validation for personalization features (toggle checks).

Technical details:
- Phase 1: Infrastructure & "Reusable Intelligence" Setup (Skills).
- Phase 2: Content Generation (Modules 1-4) via Subagents.
- Phase 3: Intelligence Layer (RAG & Personalization).
- Follow "Spec-Driven Development" (Spec → Plan → Code).

## Response snapshot

Created comprehensive implementation plan with 7-phase roadmap, technical architecture, data models, API contracts, and 3 ADRs documenting significant architectural decisions:

**Constitution Check Results:**
- ✅ PASS on 6/7 principles (SDD, Reusable Intelligence, Agent-First, Independent Testability, Personalization, Hackathon Scoring)
- ⚠️ COMPLEXITY on Principle V (RAG-Native): Qdrant 1GB chunking strategy required (justified as unavoidable free-tier constraint)
- Complexity tracking table documents 3 violations with mitigations

**Technical Architecture:**
- **Hybrid deployment**: GitHub Pages (Docusaurus static site) + Railway (FastAPI backend microservice)
- **Rationale**: Docusaurus purpose-built for docs (search, navigation, mobile), FastAPI optimal for Python RAG stack (Qdrant, OpenAI)
- **Decision documented in ADR-001** with CORS configuration examples

**Data Models:**
- **Neon Postgres schema**: Users (profile data), ChatSessions, Messages tables - total 2.2MB for 100 users + 500 sessions (well within 0.5GB limit)
- **Qdrant collection design**: 1536-dim vectors (text-embedding-3-small), cosine similarity, metadata (chapter_id, module, week_number, chunk_index, heading)
- **Storage estimate**: 13 chapters = 65 chunks @ 8.5KB = 553KB (0.05% of 1GB, leaves room for 2400+ future chapters)

**API Contracts (4 OpenAPI specs):**
1. `contracts/chat-api.yaml`: POST /chat with question, session_id, chapter_context, selected_text (up to 2000 chars)
2. `contracts/auth-api.yaml`: POST /auth/signup (email, password, profile), POST /auth/signin
3. `contracts/personalize-api.yaml`: POST /personalize with chapter_id, user_profile (requires bearer token)
4. `contracts/translate-api.yaml`: POST /translate with chapter_id, original_content (requires bearer token)

**3 Architectural Decision Records:**

**ADR-001: Deployment Strategy (GitHub Pages + Railway vs. Vercel Monolith)**
- **Decision**: Hybrid deployment (GitHub Pages for frontend, Railway for backend)
- **Rationale**: Docusaurus optimized for docs, FastAPI better for Python RAG ecosystem, static CDN performance <1s page load
- **Tradeoff**: CORS complexity (5 lines FastAPI middleware) vs. losing Docusaurus features in Next.js

**ADR-002: Better Auth Integration (Server-Side JWT vs. Client-Side Session)**
- **Decision**: Server-side JWT tokens (FastAPI generates/validates)
- **Rationale**: Stateless (no sessions table saves Neon storage), standard FastAPI pattern, user profile in JWT claims
- **Implementation**: Better Auth React components for UI only, FastAPI handles authentication logic
- **Security**: httpOnly cookies to prevent XSS, 24-hour expiration

**ADR-003: RAG Chunking Strategy (Token Size & Overlap)**
- **Decision**: 512-token chunks with 50-token overlap
- **Rationale**: Industry standard, balances context and precision, only 0.05% of 1GB used for 13 chapters
- **Storage calculation**: 65 chunks × 8.5KB = 553KB (leaves 999.4MB headroom)
- **Alternative rejected**: 1024-token chunks reduce precision, 256-token chunks fragment context

**7-Phase Implementation Roadmap:**
1. **Phase 0**: Research & environment setup (Qdrant/Neon/OpenAI accounts, free-tier validation)
2. **Phase 2.1**: Infrastructure & skills library setup (agent skills, Docusaurus, FastAPI, Better Auth, CI/CD)
3. **Phase 2.2**: Content generation via subagents (13+ chapters, Writer → RAG Indexer → QA agent workflow)
4. **Phase 2.3**: RAG chatbot integration (ChatbotWidget.tsx, /chat endpoint, ground-truth Q&A tests)
5. **Phase 2.4**: Authentication & user profiles (+50pts bonus, AuthModal.tsx, /auth/signup, JWT implementation)
6. **Phase 2.5**: Content personalization (+50pts bonus, PersonalizeButton.tsx, GPT-4 skill-level prompts, caching)
7. **Phase 2.6**: Urdu translation (+50pts bonus, TranslateButton.tsx, GPT-4 translation, code preservation)
8. **Phase 2.7**: Agent workflows demonstration (+50pts in Phase 2.2, 5+ skills, agents/definitions.yaml, demo video)

**Testing Strategy:**
- **Link checking**: broken-link-checker npm package, CI/CD integration
- **RAG accuracy**: 10 ground-truth Q&A pairs, >90% keyword match threshold
- **User journey E2E**: Playwright tests for personalization toggle (beginner vs. advanced content verification)
- **Load testing**: k6 with 50 concurrent users, <10s chatbot response target

**Project Structure:**
- Frontend: `docs/` (Docusaurus content), `src/components/` (ChatbotWidget, PersonalizeButton, TranslateButton, AuthModal)
- Backend: `backend/src/` (FastAPI routes for chat, auth, personalize, translate), `backend/tests/` (pytest)
- Agent infrastructure: `skills/` (5+ documented skills), `agents/definitions.yaml`
- Deployment: GitHub Actions CI/CD, GitHub Pages + Railway/Render/Vercel

## Outcome

- ✅ Impact: Complete technical plan ready for task generation, 3 ADRs document critical decisions, Constitution Check passed with justified complexity
- 🧪 Tests: Testing strategy defined (link checking, RAG accuracy, E2E user journeys, load testing)
- 📁 Files: Created `plan.md` (580+ lines), `adr/001-deployment-strategy.md`, `adr/002-better-auth-integration.md`, `adr/003-rag-chunking-strategy.md`
- 🔁 Next prompts: Run `/sp.tasks` to generate detailed task breakdown from plan, then `/sp.implement` to begin Phase 2.1
- 🧠 Reflection: Hybrid architecture (Docusaurus + FastAPI) aligns with constitution's separation of concerns (Principle III). 512-token chunking optimizes storage efficiency while maintaining retrieval accuracy. JWT authentication avoids Neon database sessions, preserving storage for chat history.

## Evaluation notes (flywheel)

- Failure modes observed: None - plan comprehensively addresses all 5 user stories with technical depth
- Graders run and results (PASS/FAIL): PASS - Constitution Check validated, ADRs document all significant decisions (deployment, auth, chunking), data models fit within free-tier limits (0.5GB Neon, 1GB Qdrant)
- Prompt variant (if applicable): plan-v1-hybrid-architecture-with-adrs
- Next experiment (smallest change to try): During `/sp.tasks`, validate task organization aligns with 7-phase roadmap and user story priorities (P1 base functionality first, P3-P5 bonus features sequential)
