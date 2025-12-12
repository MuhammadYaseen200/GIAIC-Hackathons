# Implementation Plan: Physical AI & Humanoid Robotics Interactive Textbook

**Branch**: `001-physical-ai-textbook` | **Date**: 2025-12-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-physical-ai-textbook/spec.md`

## Summary

Build an interactive Docusaurus-based textbook for teaching Physical AI & Humanoid Robotics, featuring embedded RAG chatbot, personalized learning, Urdu translation, and agent-driven content generation. Target hackathon score: 300 points (base 100 + 200 bonus). Primary challenge: Coordinating 5 independent user stories with free-tier infrastructure constraints (1GB Qdrant, 0.5GB Neon) while demonstrating industrial-grade agentic workflows.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend), Node.js 20+
**Primary Dependencies**: Docusaurus 3.x, FastAPI 0.110+, OpenAI SDK 1.x, Better Auth 1.x, Qdrant Client 1.7+, Neon Serverless Postgres (via asyncpg), React 18+, Tailwind CSS 3.x
**Storage**: Qdrant Cloud Free Tier (1GB vectors), Neon Serverless Postgres (0.5GB relational data), GitHub/Vercel static hosting
**Testing**: Pytest (backend), Jest + React Testing Library (frontend), Playwright (E2E), Link checker (broken-link-checker npm)
**Target Platform**: Web browsers (Chrome 90+, Firefox 88+, Safari 14+), responsive mobile
**Project Type**: Hybrid (static Docusaurus site + FastAPI backend microservice)
**Performance Goals**: <3s initial page load, <10s RAG chatbot response (p95), <5s personalization/translation
**Constraints**: 1GB Qdrant limit (~250 chapters max @ 4MB each), 0.5GB Neon limit, 90s demo video, Nov 30 2025 deadline
**Scale/Scope**: 13+ chapters, 50 concurrent users, 100+ test user accounts

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Justification |
|-----------|-------------------|-------------------------|
| **I. Spec-Driven Development** | ✅ PASS | This plan derived from approved spec.md; tasks.md will be generated from this plan; no implementation starts before task approval |
| **II. Reusable Intelligence** | ✅ PASS | All content stored in `/docs` (Docusaurus); agent skills documented in `/skills`; PHRs track decisions in `history/prompts/001-physical-ai-textbook/` |
| **III. Agent-First Architecture** | ✅ PASS | 5 specialized agents defined (Writer, RAG Indexer, QA, Translator, Personalizer); skills library in `/skills`; `agents/definitions.yaml` documents roles |
| **IV. Independent Testability** | ✅ PASS | 5 user stories (P1-P5) independently deployable: P1 = static site alone, P2 = +RAG chatbot, P3-P5 = bonus features with isolated toggles |
| **V. RAG-Native Learning** | ⚠️ COMPLEXITY | Qdrant 1GB limit requires chunking strategy (512-token chunks, metadata filtering). **Justification**: Free tier mandatory per hackathon rules; chunking adds complexity but is unavoidable. Mitigation: Document chunking logic in ADR-003. |
| **VI. Personalization & Accessibility** | ✅ PASS | Better Auth for user profiles; per-chapter personalization buttons; Urdu translation via GPT-4; session-based state minimizes costs |
| **VII. Hackathon Scoring Optimization** | ✅ PASS | Phase prioritization aligns with scoring: Phase 1-2 (base 100pts), Phase 3a (+50pts RAG already in base), Phase 3b-3d (+150pts bonuses) |

**Complexity Violations Requiring Justification**:

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Qdrant 1GB chunking strategy (Principle V) | Free tier limit forces text splitting into 512-token chunks with metadata for retrieval | In-memory vector search insufficient for 13+ chapters; paid tier violates hackathon constraints |
| Dual-stack (Docusaurus + FastAPI) architecture | Static site for performance; dynamic backend for RAG/personalization/auth | Next.js monolith would mix SSR complexity with static content; Docusaurus optimized for docs sites |
| Session-based translation (not persistent) | Minimizes OpenAI API costs for repeated translations | Persistent translations would require caching infrastructure exceeding Neon 0.5GB limit |

## Project Structure

### Documentation (this feature)

```text
specs/001-physical-ai-textbook/
├── plan.md              # This file (/sp.plan command output)
├── spec.md              # Feature specification (already exists)
├── research.md          # Phase 0 output (external API docs, reference implementations)
├── data-model.md        # Phase 1 output (Neon schema, Qdrant collection design)
├── quickstart.md        # Phase 1 output (local dev setup, environment config)
├── contracts/           # Phase 1 output (FastAPI endpoint specs)
│   ├── chat-api.yaml    # OpenAPI spec for /chat endpoint
│   ├── auth-api.yaml    # OpenAPI spec for /auth/* endpoints
│   ├── personalize-api.yaml
│   └── translate-api.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Hybrid architecture: Static frontend + Dynamic backend

# --- Frontend (Docusaurus Static Site) ---
docs/                    # Docusaurus content root
├── intro.md             # Landing page
├── module1-ros2/        # Module 1: ROS 2 Nervous System
│   ├── week3-nodes.md
│   ├── week4-topics-services.md
│   └── week5-urdf.md
├── module2-digital-twin/  # Module 2: Gazebo & Unity
│   ├── week6-gazebo.md
│   └── week7-unity.md
├── module3-isaac/       # Module 3: NVIDIA Isaac
│   ├── week8-isaac-sim.md
│   ├── week9-isaac-ros.md
│   └── week10-nav2.md
└── module4-vla/         # Module 4: Vision-Language-Action
    ├── week11-humanoid-kinematics.md
    ├── week12-manipulation.md
    └── week13-conversational.md

docusaurus.config.js     # Docusaurus configuration
sidebars.js              # Sidebar navigation structure

src/                     # Docusaurus React components
├── components/
│   ├── ChatbotWidget.tsx       # Embedded RAG chatbot UI
│   ├── PersonalizeButton.tsx   # Per-chapter personalization toggle
│   ├── TranslateButton.tsx     # Per-chapter Urdu translation toggle
│   └── AuthModal.tsx           # Better Auth login/signup modal
├── pages/
│   └── index.tsx        # Custom homepage
└── css/
    └── custom.css       # Tailwind + custom styles

# --- Backend (FastAPI Microservice) ---
backend/
├── src/
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Environment variables (.env loader)
│   ├── auth/
│   │   ├── routes.py    # Better Auth integration endpoints
│   │   ├── models.py    # User, Session SQLAlchemy models
│   │   └── middleware.py
│   ├── chat/
│   │   ├── routes.py    # /chat endpoint
│   │   ├── rag_engine.py   # Qdrant query + OpenAI completion
│   │   └── models.py    # ChatSession, Message models
│   ├── personalize/
│   │   ├── routes.py    # /personalize endpoint
│   │   └── prompt_builder.py  # GPT-4 prompts for skill levels
│   ├── translate/
│   │   ├── routes.py    # /translate endpoint
│   │   └── urdu_translator.py # GPT-4 translation logic
│   └── db/
│       ├── neon_client.py   # Neon Postgres async connection
│       └── migrations/      # Alembic migration scripts
└── tests/
    ├── test_chat.py
    ├── test_personalize.py
    └── integration/
        └── test_user_journey.py

# --- Agent Skills & Reusable Intelligence ---
skills/                  # Documented agent capabilities
├── generate-chapter.md  # Skill: Generate new chapter from outline
├── create-rag-embedding.md  # Skill: Ingest chapter into Qdrant
├── review-content.md    # Skill: QA check for technical accuracy
├── personalize-content.md   # Skill: Adjust content for skill level
└── translate-to-urdu.md     # Skill: Translate preserving code blocks

agents/
└── definitions.yaml     # Agent roles and skill mappings

# --- Infrastructure ---
.env.example             # Template for API keys (never commit .env)
docker-compose.yml       # Local dev: FastAPI + Postgres (Neon in prod)
requirements.txt         # Python dependencies
package.json             # Node dependencies (Docusaurus)
playwright.config.ts     # E2E test configuration
```

**Structure Decision**: Hybrid architecture chosen to balance static site performance (Docusaurus) with dynamic features (FastAPI backend). Docusaurus handles content serving, search, and navigation. FastAPI microservice handles RAG, authentication, personalization, and translation. This separation enables independent deployment (GitHub Pages for frontend, Vercel/Railway for backend) and aligns with JAMstack best practices.

## Phase 0: Research & Preparation

**Goal**: Gather external references, validate free-tier limits, establish development environment.

### Research Deliverables (research.md)

1. **Docusaurus Configuration**:
   - Official docs: https://docusaurus.io/docs
   - Custom React components integration
   - Search plugin configuration (local search vs Algolia)
   - GitHub Pages deployment guide

2. **RAG Stack References**:
   - Qdrant Python client documentation
   - OpenAI Agents SDK examples (if using ChatKit SDK instead of raw API)
   - LangChain RAG patterns (optional, evaluate if needed)
   - Chunking strategies for technical documentation

3. **Better Auth Integration**:
   - Better Auth documentation: https://www.better-auth.com/
   - Email/password authentication setup
   - React integration patterns
   - Session management with FastAPI backend

4. **Free Tier Validation**:
   - Qdrant Cloud Free Tier: 1GB storage, confirm API rate limits
   - Neon Serverless Postgres: 0.5GB storage, connection pooling limits
   - OpenAI API pricing for GPT-4 (estimate costs for personalization/translation)

5. **Reference Implementations**:
   - Existing RAG chatbot embedded in documentation sites
   - Better Auth + FastAPI examples
   - Multi-language content sites (for translation patterns)

### Environment Setup Checklist

- [ ] Node.js 20+ and Python 3.11+ installed
- [ ] Qdrant Cloud account created, API key obtained
- [ ] Neon Serverless Postgres database created, connection string obtained
- [ ] OpenAI API key obtained, billing limits set
- [ ] Better Auth account setup (if required for hosted service)
- [ ] GitHub repository initialized with branch `001-physical-ai-textbook`
- [ ] Local dev environment: `npm install` and `pip install -r requirements.txt`

## Phase 1: Design Artifacts

### Data Model (data-model.md)

#### Neon Serverless Postgres Schema

```sql
-- Users table (Better Auth managed, extended for profiles)
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    software_level VARCHAR(20) CHECK (software_level IN ('beginner', 'intermediate', 'advanced')),
    hardware_level VARCHAR(20) CHECK (hardware_level IN ('none', 'some', 'extensive')),
    robotics_background BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Chat sessions
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,  -- Nullable for anonymous
    chapter_context VARCHAR(100),  -- e.g., "module1-week3-ros2-nodes"
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages
CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(10) CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    retrieved_chunks JSONB,  -- Array of Qdrant chunk IDs with scores
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_users_email ON users(email);
```

**Storage Estimate**: 100 users @ 500 bytes = 50KB, 500 chat sessions @ 200 bytes = 100KB, 2000 messages @ 1KB = 2MB. **Total: ~2.2MB** (well within 0.5GB limit).

#### Qdrant Collection Design

```python
# Collection: "textbook_chunks"
# Vector dimensions: 1536 (OpenAI text-embedding-3-small)
# Distance metric: Cosine similarity

collection_config = {
    "vectors": {
        "size": 1536,
        "distance": "Cosine"
    },
    "payload_schema": {
        "chapter_id": "keyword",      # e.g., "module1-week3-ros2-nodes"
        "module": "keyword",           # "ROS2", "DigitalTwin", "Isaac", "VLA"
        "week_number": "integer",      # 1-13
        "chunk_index": "integer",      # Position within chapter
        "text": "text",                # Original text content
        "heading": "text",             # Nearest heading for context
        "token_count": "integer"       # For debugging chunk sizes
    }
}
```

**Chunking Strategy**:
- **Chunk size**: 512 tokens (~2KB per chunk)
- **Overlap**: 50 tokens to preserve context across boundaries
- **Average chapter**: 1500 words = ~2000 tokens = 4 chunks
- **13 chapters**: 52 chunks × ~4KB (text + vector) = **208KB** (well within 1GB limit, leaves room for 200+ more chapters)

**Retrieval Strategy**:
1. User asks question → Embed query with OpenAI text-embedding-3-small
2. Qdrant search top 5 chunks with cosine similarity > 0.7
3. Filter by chapter_id if "Ask about selection" mode
4. Pass retrieved chunks + user question to GPT-4
5. Cite chapter_id and heading in response

### API Contracts (contracts/)

#### contracts/chat-api.yaml

```yaml
openapi: 3.1.0
info:
  title: RAG Chatbot API
  version: 1.0.0

paths:
  /chat:
    post:
      summary: Submit question to RAG chatbot
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [question, session_id]
              properties:
                question:
                  type: string
                  maxLength: 500
                  example: "How do ROS 2 topics differ from services?"
                session_id:
                  type: string
                  format: uuid
                  example: "123e4567-e89b-12d3-a456-426614174000"
                chapter_context:
                  type: string
                  nullable: true
                  example: "module1-week3-ros2-nodes"
                selected_text:
                  type: string
                  nullable: true
                  maxLength: 2000
                  description: "Text snippet for 'Ask about selection' mode"
      responses:
        '200':
          description: Chatbot response
          content:
            application/json:
              schema:
                type: object
                properties:
                  answer:
                    type: string
                  citations:
                    type: array
                    items:
                      type: object
                      properties:
                        chapter_id: {type: string}
                        heading: {type: string}
                        relevance_score: {type: number}
                  response_time_ms:
                    type: integer
        '429':
          description: Rate limit exceeded
        '503':
          description: Qdrant or OpenAI unavailable
```

#### contracts/auth-api.yaml

```yaml
openapi: 3.1.0
info:
  title: Authentication API
  version: 1.0.0

paths:
  /auth/signup:
    post:
      summary: Create new user account
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password, software_level, hardware_level, robotics_background]
              properties:
                email: {type: string, format: email}
                password: {type: string, minLength: 8}
                software_level: {type: string, enum: [beginner, intermediate, advanced]}
                hardware_level: {type: string, enum: [none, some, extensive]}
                robotics_background: {type: boolean}
      responses:
        '201':
          description: User created
          content:
            application/json:
              schema:
                type: object
                properties:
                  user_id: {type: string, format: uuid}
                  access_token: {type: string}

  /auth/signin:
    post:
      summary: Authenticate existing user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email: {type: string}
                password: {type: string}
      responses:
        '200':
          description: Authentication successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token: {type: string}
                  user_profile:
                    type: object
                    properties:
                      software_level: {type: string}
                      hardware_level: {type: string}
        '401':
          description: Invalid credentials
```

#### contracts/personalize-api.yaml

```yaml
openapi: 3.1.0
info:
  title: Content Personalization API
  version: 1.0.0

paths:
  /personalize:
    post:
      summary: Generate personalized chapter content
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [chapter_id, user_profile]
              properties:
                chapter_id: {type: string}
                user_profile:
                  type: object
                  properties:
                    software_level: {type: string}
                    hardware_level: {type: string}
                original_content: {type: string}
      responses:
        '200':
          description: Personalized content
          content:
            application/json:
              schema:
                type: object
                properties:
                  personalized_markdown: {type: string}
                  adjustments_applied:
                    type: array
                    items: {type: string}
                    example: ["Simplified jargon", "Expanded step-by-step", "Linked prerequisites"]
        '401':
          description: Unauthorized (login required)
```

#### contracts/translate-api.yaml

```yaml
openapi: 3.1.0
info:
  title: Urdu Translation API
  version: 1.0.0

paths:
  /translate:
    post:
      summary: Translate chapter content to Urdu
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [chapter_id, original_content]
              properties:
                chapter_id: {type: string}
                original_content: {type: string, maxLength: 50000}
      responses:
        '200':
          description: Translated content
          content:
            application/json:
              schema:
                type: object
                properties:
                  translated_markdown: {type: string}
                  preserved_elements:
                    type: object
                    properties:
                      code_blocks: {type: integer}
                      technical_terms: {type: array, items: {type: string}}
        '401':
          description: Unauthorized (login required)
```

### Quickstart (quickstart.md)

```markdown
# Developer Quickstart: Physical AI Textbook

## Prerequisites
- Node.js 20+, Python 3.11+
- Git, Docker (optional for local Postgres)

## Environment Setup

1. Clone repository and checkout feature branch:
   ```bash
   git clone <repo-url>
   cd Humanoid-Robots-Book
   git checkout 001-physical-ai-textbook
   ```

2. Install dependencies:
   ```bash
   # Frontend
   npm install

   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables (copy `.env.example` to `.env`):
   ```env
   # OpenAI
   OPENAI_API_KEY=sk-...

   # Qdrant Cloud
   QDRANT_URL=https://your-cluster.qdrant.io
   QDRANT_API_KEY=...

   # Neon Serverless Postgres
   DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

   # Better Auth
   AUTH_SECRET=<generate-random-secret>
   AUTH_URL=http://localhost:3000
   ```

4. Initialize database:
   ```bash
   cd backend
   alembic upgrade head  # Run migrations
   ```

5. Ingest initial content into Qdrant:
   ```bash
   python scripts/ingest_chapters.py --docs-dir ../docs
   ```

6. Run development servers:
   ```bash
   # Terminal 1: Docusaurus frontend
   npm start  # http://localhost:3000

   # Terminal 2: FastAPI backend
   cd backend
   uvicorn src.main:app --reload --port 8000  # http://localhost:8000
   ```

## Running Tests

```bash
# Backend unit tests
cd backend
pytest tests/

# Frontend component tests
npm test

# E2E tests (requires both servers running)
npx playwright test
```

## Building for Production

```bash
# Frontend static build
npm run build  # Output: build/

# Deploy to GitHub Pages
npm run deploy  # Pushes to gh-pages branch

# Backend deployment (example: Railway)
# See deployment/railway.md for instructions
```
```

## Phase 2: Implementation Roadmap

### Phase 2.1: Infrastructure & Reusable Intelligence Setup

**Goal**: Establish agent skills library, repository structure, and development environment.

**Tasks** (will be detailed in tasks.md):
- Create `/skills` directory with 5+ documented skills
- Create `agents/definitions.yaml` with agent role mappings
- Setup Docusaurus project with custom React components
- Setup FastAPI backend with project structure
- Configure Better Auth integration (server-side approach per ADR-002)
- Initialize Neon database with schema from data-model.md
- Create Qdrant collection with vector config
- Setup CI/CD pipeline (GitHub Actions for tests + deployment)

**Success Criteria**: Repository structure matches plan.md, all dependencies installed, local dev environment functional, initial PHR documenting setup decisions.

### Phase 2.2: Content Generation (Modules 1-4) via Subagents

**Goal**: Generate 13+ chapters of technical content using Writer Agent and document in `history/prompts/`.

**Subagent Workflow**:
1. **Writer Agent** (uses `generate-chapter.md` skill):
   - Input: Chapter outline (e.g., "Week 3: ROS 2 Nodes and Topics")
   - Output: Markdown file with 1500+ words, code examples, diagrams
   - Stores in `docs/module1-ros2/week3-nodes.md`

2. **RAG Indexer Agent** (uses `create-rag-embedding.md` skill):
   - Input: Generated markdown file
   - Output: Chunks text, generates embeddings, uploads to Qdrant
   - Records chunk IDs in Qdrant collection metadata

3. **QA Agent** (uses `review-content.md` skill):
   - Input: Generated chapter
   - Output: Technical accuracy review, broken link check
   - Suggests corrections if needed

**Content Structure** (13 chapters minimum):
- Module 1: ROS 2 Nervous System (3 chapters, weeks 3-5)
- Module 2: Digital Twin (2 chapters, weeks 6-7)
- Module 3: NVIDIA Isaac (3 chapters, weeks 8-10)
- Module 4: Vision-Language-Action (3 chapters, weeks 11-13)
- Intro: Physical AI Overview (2 chapters, weeks 1-2)

**Success Criteria**: 13+ chapters deployed, each 1500+ words with code examples, Qdrant contains 50+ chunks, all chapters navigable in Docusaurus, PHRs document content generation decisions.

### Phase 2.3: RAG Chatbot Integration (Base 100pts)

**Goal**: Embed functional RAG chatbot widget on every chapter page.

**Tasks**:
- Implement `ChatbotWidget.tsx` React component
- Implement FastAPI `/chat` endpoint with Qdrant retrieval logic
- Implement "Ask about selection" text highlighting feature
- Connect chatbot to Neon for chat history storage
- Test with 10 ground-truth Q&A pairs (>90% accuracy)
- Handle out-of-scope questions gracefully

**Success Criteria**: Chatbot answers 90% of test questions within 10 seconds, retrieves context from 3+ chapters, "Ask about selection" mode functional, chat history persisted for logged-in users.

### Phase 2.4: Authentication & User Profiles (+50pts bonus)

**Goal**: Implement Better Auth signup/signin with background questionnaire.

**Tasks**:
- Implement `AuthModal.tsx` React component
- Implement FastAPI `/auth/signup` and `/auth/signin` endpoints
- Collect software_level, hardware_level, robotics_background during signup
- Store user profiles in Neon database
- Implement JWT-based session management (per ADR-002)
- Allow anonymous users to read content without signup

**Success Criteria**: Signup flow completes in <2 minutes, user profiles stored in database, authentication required for personalization/translation features, anonymous browsing functional.

### Phase 2.5: Content Personalization (+50pts bonus)

**Goal**: Per-chapter personalization based on user skill level.

**Tasks**:
- Implement `PersonalizeButton.tsx` React component
- Implement FastAPI `/personalize` endpoint with GPT-4 integration
- Build prompt templates for beginner/intermediate/advanced levels
- Implement session-based caching (1-hour TTL) to reduce API costs
- Test with 2 user profiles (beginner vs. advanced) to verify distinct outputs

**Success Criteria**: Beginner content 30% longer with simplified vocabulary, advanced content condensed with source references, personalization per-chapter (not global), caching reduces API calls by 80% for repeated requests.

### Phase 2.6: Urdu Translation (+50pts bonus)

**Goal**: One-click Urdu translation preserving code blocks and technical terms.

**Tasks**:
- Implement `TranslateButton.tsx` React component
- Implement FastAPI `/translate` endpoint with GPT-4 translation
- Build translation prompt preserving code blocks, math notation, acronyms
- Implement session-based state (translation resets on page reload)
- Test with 5 randomly selected chapters to verify 95% coverage

**Success Criteria**: Translation completes in <3 seconds, 95% of natural language translated, code blocks preserved, technical terms kept in English with Urdu explanations, session-based state functional.

### Phase 2.7: Agent Workflows Demonstration (+50pts already included in Phase 2.2)

**Goal**: Document agent skills and demonstrate autonomous content generation.

**Tasks**:
- Finalize 5+ agent skills in `/skills` directory
- Complete `agents/definitions.yaml` with role descriptions
- Create 10+ PHRs documenting major decisions
- Record demo video segment (20 seconds) showing agent generating new chapter
- Verify judges can inspect `/skills`, `agents/definitions.yaml`, and `history/prompts/`

**Success Criteria**: 5+ skills documented with input/output specs, `agents/definitions.yaml` defines Writer/QA/RAG Indexer/Translator/Personalizer agents, 10+ PHRs with complete YAML front matter, demo video shows autonomous agent workflow.

## Phase 3: Testing Strategy

### 3.1 Automated Testing

**Link Checking (Docusaurus)**:
```bash
# npm package: broken-link-checker
npm install --save-dev broken-link-checker
npx blc http://localhost:3000 --recursive --ordered --exclude="github.com"
```
- Run during CI/CD pipeline
- Flag broken external links but don't block deployment
- Generate report in `tests/link-check-report.json`

**RAG Accuracy Tests (Ground Truth Q&A)**:
```python
# tests/test_rag_accuracy.py
import pytest

GROUND_TRUTH = [
    {
        "question": "How do ROS 2 topics differ from services?",
        "expected_keywords": ["publish-subscribe", "many-to-many", "asynchronous", "request-response"],
        "chapter": "module1-week3-ros2-nodes"
    },
    # ... 10 total ground truth pairs
]

@pytest.mark.asyncio
async def test_rag_accuracy():
    correct = 0
    for qa in GROUND_TRUTH:
        response = await chatbot.ask(qa["question"], chapter=qa["chapter"])
        if all(kw in response.lower() for kw in qa["expected_keywords"]):
            correct += 1
    accuracy = correct / len(GROUND_TRUTH)
    assert accuracy >= 0.90, f"RAG accuracy {accuracy:.1%} below 90% threshold"
```

**User Journey Validation (Personalization Toggle)**:
```typescript
// tests/e2e/personalization.spec.ts
import { test, expect } from '@playwright/test';

test('beginner personalization simplifies content', async ({ page }) => {
  // Create beginner user account
  await page.goto('/auth/signup');
  await page.fill('input[name="email"]', 'beginner@test.com');
  await page.fill('input[name="password"]', 'testpass123');
  await page.selectOption('select[name="software_level"]', 'beginner');
  await page.click('button[type="submit"]');

  // Navigate to chapter and personalize
  await page.goto('/docs/module1-ros2/week3-nodes');
  await page.click('button[aria-label="Personalize Content"]');
  await page.waitForSelector('.personalized-content');

  // Verify content is simplified
  const content = await page.textContent('.personalized-content');
  expect(content).toContain('step-by-step'); // Indicator of beginner content
  expect(content.split(' ').length).toBeGreaterThan(1500 * 1.3); // 30% longer
});
```

### 3.2 Manual Testing Checklist

- [ ] All 13+ chapters load correctly in Docusaurus
- [ ] Chatbot widget appears on every chapter page
- [ ] "Ask about selection" mode works with highlighted text
- [ ] Signup flow collects background information
- [ ] Personalization button only visible when logged in
- [ ] Beginner vs. advanced personalization produces distinct outputs
- [ ] Urdu translation button only visible when logged in
- [ ] Translation preserves code blocks and technical terms
- [ ] Translation resets on page reload (session-based)
- [ ] Anonymous users can browse content and use chatbot
- [ ] Mobile responsive layout works on iPhone/Android

### 3.3 Performance Testing

**Load Test (50 Concurrent Users)**:
```bash
# Using Locust or k6
k6 run --vus 50 --duration 60s tests/load/chatbot-load.js
```
- Target: <10s response time (p95) for chatbot queries
- Verify Qdrant and Neon handle concurrent connections
- Monitor OpenAI API rate limits

**Page Load Performance**:
- Target: <3s initial page load (Lighthouse audit)
- Optimize Docusaurus bundle size
- Lazy-load chatbot widget to improve First Contentful Paint

## Phase 4: Deployment

### 4.1 Frontend Deployment (GitHub Pages)

```bash
# In package.json
{
  "scripts": {
    "deploy": "docusaurus deploy"
  },
  "homepage": "https://<username>.github.io/Humanoid-Robots-Book/"
}

# Deploy command
npm run deploy  # Builds and pushes to gh-pages branch
```

**Alternative**: Vercel deployment if GitHub Pages has SSL issues.

### 4.2 Backend Deployment (Railway / Render / Vercel Serverless)

**Recommended**: Railway (free tier supports FastAPI + Neon integration)

```yaml
# railway.toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
startCommand = "uvicorn src.main:app --host 0.0.0.0 --port $PORT"

[env]
OPENAI_API_KEY = "<from-railway-env-vars>"
QDRANT_URL = "<from-railway-env-vars>"
DATABASE_URL = "<neon-connection-string>"
```

### 4.3 Demo Video Production (<90 seconds)

**Segment Breakdown**:
1. **0-15s**: Landing page tour, navigate to Module 1
2. **15-30s**: RAG chatbot demo (ask question, show context retrieval)
3. **30-45s**: Personalization demo (toggle beginner/advanced, show difference)
4. **45-60s**: Urdu translation demo (translate chapter, revert)
5. **60-75s**: Agent workflow demo (show `/skills` directory, PHRs, run content generation command)
6. **75-90s**: GitHub repo overview, highlight scoring features (base + bonuses)

**Tools**: OBS Studio for screen recording, DaVinci Resolve for editing, NotebookLM for voiceover (optional).

## Dependencies & Execution Order

### Critical Path

1. **Phase 2.1** (Infrastructure) → Blocks all other phases
2. **Phase 2.2** (Content Generation) → Required for RAG testing in 2.3
3. **Phase 2.4** (Authentication) → Required for 2.5 and 2.6 (personalization/translation need auth)
4. **Phase 2.3, 2.5, 2.6, 2.7** → Can proceed in parallel after dependencies met

### Parallel Opportunities

- Phase 2.3 (RAG) and Phase 2.4 (Auth) can be developed in parallel after Phase 2.1
- Phase 2.5 (Personalization) and Phase 2.6 (Translation) can be developed in parallel after Phase 2.4
- Testing (Phase 3) can begin incrementally as each phase completes

### Risk Mitigation

**Risk**: Qdrant 1GB limit exceeded during content generation
**Mitigation**: Monitor storage after each chapter ingestion, implement chunk pruning if approaching limit

**Risk**: OpenAI API rate limits during peak personalization/translation usage
**Mitigation**: Implement exponential backoff, cache responses for 1 hour, provide fallback error message

**Risk**: Demo video exceeds 90 seconds
**Mitigation**: Script segments precisely, rehearse before recording, edit aggressively

## Complexity Tracking

| Complexity Area | Justification | Mitigation Strategy |
|-----------------|---------------|---------------------|
| Dual-stack architecture (Docusaurus + FastAPI) | Static site performance + dynamic features require separate concerns | Well-documented API contracts, clear separation in `/docs` vs `/backend` |
| Qdrant chunking strategy (512-token chunks) | Free tier 1GB limit forces text splitting | Document chunking logic in ADR-003, test with 13+ chapters to validate fit |
| Session-based translation (not persistent) | Minimizes OpenAI API costs | User education via UI ("Translation resets on page reload"), consider localStorage caching in future |
| Agent skills documentation overhead | Hackathon bonus feature requires 5+ skills | Template-based skill documentation, focus on 5 highest-value skills first |

## Next Steps

1. Run `/sp.adr` to document the 3 significant decisions:
   - ADR-001: Deployment strategy (GitHub Pages + Railway vs. Vercel monolith)
   - ADR-002: Better Auth integration (server-side JWT vs. client-side session)
   - ADR-003: RAG chunking strategy (512-token chunks with 50-token overlap)

2. Run `/sp.tasks` to generate detailed task breakdown from this plan

3. Obtain human approval before proceeding to implementation

4. Run `/sp.implement` to begin Phase 2.1 (Infrastructure setup)
