# Implementation Plan: RAG Chatbot (Physical AI Tutor)

**Feature Branch**: `002-rag-chatbot`
**Created**: 2025-12-13
**Status**: Planning Complete

---

## Executive Summary

This plan outlines the implementation of a RAG (Retrieval-Augmented Generation) chatbot embedded in the Docusaurus textbook site. The chatbot retrieves relevant content from 13 textbook chapters using Qdrant vector search and generates contextual responses using Google Gemini 1.5 Flash.

**Key Components**:
1. **Backend** (@Backend-Engineer): FastAPI service with Qdrant + Google Gemini integration
2. **Frontend** (@Frontend-Architect): React ChatWidget with Select-to-Ask feature
3. **Data Ingestion**: Python script to chunk/embed textbook chapters

**Technology Stack**: Google Gemini SDK, Qdrant Cloud, Neon Postgres, FastAPI, React 18, Docusaurus 3.x

**Deployment**: Railway (backend) + GitHub Pages (frontend)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Pages (Frontend)                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Docusaurus Static Site                                     │ │
│  │  ├─ Root.tsx (swizzled)                                    │ │
│  │  └─ ChatWidget Component                                   │ │
│  │      ├─ Message History (React state)                      │ │
│  │      ├─ Select-to-Ask (Selection API)                      │ │
│  │      └─ Citation Links                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/chat
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Railway (Backend)                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ FastAPI Application                                        │ │
│  │  ├─ /api/chat (rate-limited)                               │ │
│  │  ├─ /health                                                │ │
│  │  └─ Middleware (CORS, error handling)                      │ │
│  └────┬─────────────────────────┬───────────────────┬─────────┘ │
└───────┼─────────────────────────┼───────────────────┼───────────┘
        │                         │                   │
        ▼                         ▼                   ▼
┌──────────────┐       ┌──────────────────┐   ┌──────────────────┐
│ Neon Postgres│       │  Qdrant Cloud    │   │ Google Gemini API│
│ (Chat Logs)  │       │ (Vector Search)  │   │ (Embeddings +    │
│ - sessions   │       │ - 65 chunks      │   │  Gemini 1.5      │
│ - messages   │       │ - 768-dim        │   │  Flash)          │
│ - query_logs │       │   vectors        │   │                  │
└──────────────┘       └──────────────────┘   └──────────────────┘
```

### 1.2 Data Flow

1. **User Question** → Frontend captures input + optional selected text
2. **Embedding Generation** → Backend calls Google Gemini text-embedding-004
3. **Vector Search** → Qdrant returns top-5 chunks (similarity ≥ 0.7)
4. **Response Generation** → Gemini 1.5 Flash generates answer with context
5. **Citation Extraction** → Extract metadata from retrieved chunks
6. **Logging** → Save to Neon Postgres (chat_messages + query_logs)
7. **Response** → Return JSON with answer, citations, token count

---

## 2. Technology Decisions

### 2.1 Backend Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | FastAPI 0.110+ | Async-first, auto-docs, type safety |
| **Database** | Neon Serverless Postgres | Free 0.5GB tier, auto-scaling |
| **Vector DB** | Qdrant Cloud | Free 1GB tier, Python async client |
| **LLM** | Google Gemini 1.5 Flash | Fast, cost-effective, 1M token context |
| **Embeddings** | text-embedding-004 | 768-dim, optimized for retrieval |
| **ORM** | SQLAlchemy 2.0+ | Async support, type-safe queries |
| **Rate Limiting** | slowapi | FastAPI integration, in-memory |

**Key Decisions**:
- **No LangChain/LlamaIndex**: Avoids unnecessary abstraction overhead
- **Google Gemini SDK directly**: Official library, langchain-google-genai wrapper
- **Async everywhere**: All I/O operations use `async/await`

### 2.2 Frontend Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Framework** | React 18 | Docusaurus dependency, hooks support |
| **Static Site** | Docusaurus 3.x | Already installed, MDX support |
| **Styling** | Tailwind CSS | Utility-first, Docusaurus compatible |
| **State** | React Hooks | useState, useEffect for chat history |
| **Selection** | Browser Selection API | Native, no external library needed |

**Key Decisions**:
- **Swizzle Root** (not Layout): More stable, won't break on Docusaurus upgrades
- **Client-side state**: No server-side session persistence (MVP simplification)
- **Markdown rendering**: Use `react-markdown` for assistant responses

### 2.3 Data Architecture

**Chunking Strategy**:
- **Size**: 512 tokens (≈ 2048 characters)
- **Overlap**: 50 tokens (prevents semantic breaks at boundaries)
- **Total chunks**: ~65 for 13 chapters
- **Tokenizer**: tiktoken (official OpenAI library)

**Database Schema**:
- `chat_sessions`: Session metadata (UUID, start time, chapter context)
- `chat_messages`: User + assistant messages with citations (JSONB)
- `query_logs`: Analytics (question, answer, tokens, latency)

**Vector Storage**:
- **Collection**: `textbook_chunks`
- **Distance**: COSINE similarity
- **Metadata**: chapter_id, module_id, title, section, file_path

---

## 3. Implementation Phases

### Phase 0: Research & Planning ✅ COMPLETE

**Deliverables**:
- ✅ `research.md`: Technology decisions documented
- ✅ All unknowns resolved (OpenAI SDK, chunking strategy, deployment)

### Phase 1: Design & Contracts ✅ COMPLETE

**Deliverables**:
- ✅ `data-model.md`: Entity schemas, validation rules, relationships
- ✅ `contracts/openapi.yaml`: API specification with examples
- ✅ `quickstart.md`: Developer setup guide

### Phase 2: Implementation (Next Step)

Run `/sp.tasks` to generate atomic implementation tasks from this plan.

**Expected task categories**:
1. **Backend Setup** (@Backend-Engineer):
   - Database schema migration
   - FastAPI app initialization
   - OpenAI + Qdrant client configuration
   - `/api/chat` endpoint implementation
   - Rate limiting middleware
   - Error handling

2. **Data Ingestion** (@Backend-Engineer):
   - `ingest_docs.py` script
   - Markdown parsing
   - Tiktoken chunking
   - Embedding generation
   - Qdrant upload

3. **Frontend Setup** (@Frontend-Architect):
   - Swizzle Docusaurus Root
   - ChatWidget component
   - Message history state
   - Select-to-Ask hook
   - Citation rendering
   - Tailwind styling

4. **Integration & Testing**:
   - End-to-end flow testing
   - Rate limit verification
   - Citation link validation
   - Performance benchmarking

---

## 4. Agent Assignments

### 4.1 @Backend-Engineer (Skill: `fastapi-coder.md`)

**Responsibilities**:
- Implement FastAPI `/api/chat` endpoint with async handlers
- Integrate Qdrant vector search (top-5, threshold 0.7)
- Integrate OpenAI SDK (embeddings + chat completions)
- Implement Neon Postgres logging (SQLAlchemy async)
- Add rate limiting (slowapi, 10 req/min per session)
- Write `ingest_docs.py` script for chunk upload
- Create database migration (`002_rag_chatbot_schema.sql`)

**Acceptance Criteria**:
- `/api/chat` returns responses in <3s (95th percentile)
- All database queries use async patterns
- Rate limiting blocks 11th request in same minute
- Ingestion script processes all 13 chapters without errors

**Key Files**:
- `backend/src/chat/routes.py` (main endpoint)
- `backend/src/chat/service.py` (business logic)
- `backend/src/db/models.py` (SQLAlchemy models)
- `backend/scripts/ingest_docs.py` (ingestion)
- `backend/db/migrations/002_rag_chatbot_schema.sql`

### 4.2 @Frontend-Architect (Skill: `react-component.md`)

**Responsibilities**:
- Swizzle Docusaurus Root component
- Create `<ChatWidget />` React component with hooks
- Implement Select-to-Ask (browser Selection API)
- Add markdown rendering for assistant responses
- Style with Tailwind CSS (floating button, chat panel)
- Add accessibility (ARIA labels, keyboard navigation)
- Handle error states (network failures, rate limits)

**Acceptance Criteria**:
- Chat widget appears on all Docusaurus pages
- Selected text automatically included in query context
- Citation links navigate to correct chapter sections
- Widget is accessible (screen readers, keyboard-only)
- Error messages displayed for failed requests

**Key Files**:
- `src/theme/Root.tsx` (swizzled wrapper)
- `src/components/ChatWidget/index.tsx` (main component)
- `src/components/ChatWidget/useSelectedText.tsx` (selection hook)
- `src/components/ChatWidget/styles.css` (Tailwind + custom CSS)

---

## 5. API Contract

### 5.1 Endpoint: POST /api/chat

**Request**:
```json
{
  "message": "How do I create a ROS 2 subscriber?",
  "history": []
}
```

**Response**:
```json
{
  "response": "To create a ROS 2 subscriber, inherit from `rclpy.node.Node` and use `create_subscription()`:\n\n```python\nclass MySubscriber(Node):\n    def __init__(self):\n        super().__init__('my_subscriber')\n        self.subscription = self.create_subscription(...)\n```",
  "sources": [
    {
      "title": "Chapter 2: Publisher-Subscriber Communication",
      "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
      "chapter_id": "module-1-ros2-basics/chapter-2"
    }
  ]
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input (missing fields, question too long)
- `429 Too Many Requests`: Rate limit exceeded (10/min)
- `500 Internal Server Error`: Gemini/Qdrant/Database failure
- `503 Service Unavailable`: Service temporarily down

See `contracts/openapi.yaml` for full specification.

---

## 6. Non-Functional Requirements

### 6.1 Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Response Time | <3s (95th percentile) | SC-001 |
| Concurrent Users | 100 without degradation | SC-007 |
| Ingestion Time | <10 minutes for 13 chapters | SC-008 |
| Vector Search | Top-5 in <500ms | Qdrant benchmark |

**Strategies**:
- Async I/O for all network calls
- Connection pooling (SQLAlchemy, Qdrant)
- Caching embeddings (no re-computation during queries)

### 6.2 Reliability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Accuracy | 90%+ relevant answers | SC-002 |
| Citation Accuracy | 100% valid links | SC-003 |
| Retrieval Success | 85%+ relevant chunks | SC-004 |
| Context Memory | 95%+ follow-up success | SC-006 |

**Strategies**:
- Similarity threshold (0.7) filters irrelevant chunks
- Citation validation during ingestion
- Session-based conversation history

### 6.3 Security

| Requirement | Implementation |
|-------------|----------------|
| Input Validation | Pydantic models (1-500 char questions) |
| Rate Limiting | 10 requests/min per session (slowapi) |
| CORS | Whitelist GitHub Pages + localhost only |
| SQL Injection | SQLAlchemy ORM (no raw SQL) |
| XSS Protection | React escapes all user content |
| API Key Security | Environment variables, never committed |

**Out of Scope for MVP**:
- User authentication (chatbot is public)
- Persistent session storage (client-side only)
- DDoS protection (rely on Railway/Cloudflare)

### 6.4 Cost Constraints

| Service | Monthly Budget | Usage Estimate |
|---------|----------------|----------------|
| Google Gemini Embeddings | $0.00 | Free tier for embeddings |
| Google Gemini 1.5 Flash | $0.00 | Free tier for chat (up to rate limits) |
| Qdrant Cloud | $0.00 | Free 1GB tier (293KB used) |
| Neon Postgres | $0.00 | Free 0.5GB tier |
| Railway | $0.00 | Free 500 hours/month |
| **Total** | **$0.00/month** | ✅ Within free tier budget |

---

## 7. Risk Analysis

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Google Gemini API rate limits** | Medium | High | Implement exponential backoff, display user-friendly errors |
| **Qdrant free tier exceeded** | Low | Medium | Monitor storage usage, optimize chunk size if needed |
| **CORS issues on GitHub Pages** | Medium | Low | Test CORS config early, add explicit origin whitelist |
| **Slow response times** | Medium | High | Optimize chunking, use async patterns, cache embeddings |
| **Inaccurate responses** | Medium | Medium | Set similarity threshold (0.7), validate with test queries |

### 7.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Qdrant service downtime** | Low | High | Implement graceful error handling, display fallback message |
| **Neon database unavailable** | Low | Medium | Chat still works (no logging), warn user |
| **Google Gemini service outage** | Low | High | Retry with exponential backoff, queue requests |
| **GitHub Pages deployment failure** | Low | Low | Use Railway preview environments for testing |

---

## 8. Success Metrics (from spec.md)

### 8.1 Functional Metrics

- ✅ **SC-001**: Response time <3 seconds (95th percentile)
- ✅ **SC-002**: 90%+ factually accurate answers
- ✅ **SC-003**: 100% correct citation links
- ✅ **SC-004**: 85%+ relevant chunk retrieval
- ✅ **SC-005**: 80%+ user satisfaction ("helpful" rating)
- ✅ **SC-006**: 95%+ successful follow-up questions
- ✅ **SC-007**: 100 concurrent users without degradation
- ✅ **SC-008**: Ingestion <10 minutes for all chapters
- ✅ **SC-009**: 95%+ out-of-scope detection accuracy
- ✅ **SC-010**: Zero XSS/injection vulnerabilities

### 8.2 Testing Strategy

**Unit Tests**:
- Pydantic model validation
- Chunking algorithm correctness
- Citation extraction logic

**Integration Tests**:
- `/api/chat` endpoint (mock Gemini/Qdrant)
- Database CRUD operations
- Rate limiting behavior

**End-to-End Tests**:
- Full chat flow (question → response → citation click)
- Select-to-Ask feature
- Error scenarios (network failure, rate limit)

**Load Tests**:
- 100 concurrent users (locust framework)
- Response time distribution analysis

---

## 9. Deployment Strategy

### 9.1 Backend Deployment (Railway)

**Steps**:
1. Connect GitHub repo to Railway
2. Set environment variables (GOOGLE_API_KEY, QDRANT_URL, DATABASE_URL)
3. Configure build command: `pip install -r requirements.txt`
4. Configure start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
5. Deploy from `002-rag-chatbot` branch
6. Run migrations: `railway run psql $DATABASE_URL -f db/migrations/002_rag_chatbot_schema.sql`
7. Run ingestion: `railway run python scripts/ingest_docs.py --docs-dir ../docs`

**Verification**:
```bash
curl https://your-app.railway.app/health
```

### 9.2 Frontend Deployment (GitHub Pages)

**Steps**:
1. Update `docusaurus.config.js` with production URL
2. Update ChatWidget API endpoint to Railway URL
3. Build: `npm run build`
4. Deploy: `GIT_USER=your-username npm run deploy`

**Verification**:
```bash
curl https://your-username.github.io/Humanoid-Robots-Book/
```

---

## 10. Rollback Plan

### 10.1 Database Rollback

```sql
-- Rollback script: 002_rag_chatbot_rollback.sql
DROP INDEX IF EXISTS idx_messages_citations;
DROP INDEX IF EXISTS idx_sessions_started;
DROP INDEX IF EXISTS idx_query_logs_timestamp;
DROP INDEX IF EXISTS idx_query_logs_session;
DROP INDEX IF EXISTS idx_messages_session_time;
DROP TABLE IF EXISTS query_logs;
DROP TABLE IF EXISTS chat_messages;
DROP TABLE IF EXISTS chat_sessions;
```

### 10.2 Qdrant Rollback

```python
# Delete collection
await client.delete_collection("textbook_chunks")
```

### 10.3 Frontend Rollback

```bash
# Revert to previous Docusaurus version
git checkout main
npm run deploy
```

---

## 11. Documentation Deliverables

All planning documents created:

1. ✅ **research.md**: Technology decisions and rationale
2. ✅ **data-model.md**: Entity schemas and database design
3. ✅ **contracts/openapi.yaml**: API specification
4. ✅ **quickstart.md**: Developer setup guide
5. ✅ **plan.md**: This implementation plan

**Next Step**: Run `/sp.tasks` to generate atomic implementation checklist.

---

## 12. Architectural Decision Record (ADR) Suggestions

The following significant decisions should be documented as ADRs:

### ADR-001: Use Google Gemini Instead of OpenAI
**Decision**: Use Google Gemini (gemini-1.5-flash, text-embedding-004) for embeddings and chat.
**Rationale**: Free tier provides sufficient quota for MVP; 768-dim embeddings reduce storage by 50%.
**Tradeoffs**: Less mature ecosystem than OpenAI, but cost savings enable sustainable free tier operation.

### ADR-002: Qdrant Cloud Over Pinecone
**Decision**: Use Qdrant Cloud free tier for vector storage.
**Rationale**: No credit card required, 1GB sufficient, Python async client.
**Tradeoffs**: Less mature than Pinecone, but free tier is more accessible.

### ADR-003: 512-Token Chunking Strategy
**Decision**: Chunk textbook content into 512-token segments with 50-token overlap.
**Rationale**: Balances context size vs. granularity, fits GPT-4 input limits.
**Tradeoffs**: May split code blocks, but overlap mitigates semantic loss.

### ADR-004: Swizzle Root Instead of Layout
**Decision**: Swizzle Docusaurus Root component to inject ChatWidget globally.
**Rationale**: Root is more stable than Layout across Docusaurus versions.
**Tradeoffs**: Less theme-aware, but safer for long-term maintenance.

### ADR-005: Client-Side Session State
**Decision**: Store conversation history in React state (client-side only).
**Rationale**: Simplifies MVP, avoids server-side session management.
**Tradeoffs**: Conversations lost on page refresh, but acceptable for MVP.

**To document these ADRs**, run:
```bash
/sp.adr "Google Gemini Over OpenAI"
/sp.adr "Qdrant Cloud Vector Storage"
/sp.adr "512-Token Chunking Strategy"
/sp.adr "Swizzle Root Component"
/sp.adr "Client-Side Session State"
```

---

## 13. Definition of Done

**This feature is complete when**:

✅ Backend:
- [ ] `/api/chat` endpoint returns responses in <3s
- [ ] Rate limiting enforces 10 req/min per session
- [ ] Database schema deployed to Neon Postgres
- [ ] Qdrant collection contains all 65 chunks
- [ ] Ingestion script runs without errors
- [ ] Health check endpoint returns "healthy"

✅ Frontend:
- [ ] ChatWidget appears on all Docusaurus pages
- [ ] Users can send messages and receive responses
- [ ] Select-to-Ask includes highlighted text in queries
- [ ] Citation links navigate to correct chapters
- [ ] Error messages displayed for failures

✅ Testing:
- [ ] All acceptance scenarios from spec.md pass
- [ ] Load test: 100 concurrent users with <5s response
- [ ] Security: No XSS/injection vulnerabilities found

✅ Documentation:
- [ ] README.md updated with RAG chatbot section
- [ ] Quickstart.md tested by fresh developer
- [ ] ADRs created for 5 major decisions

**Ready to implement**: Run `/sp.tasks` to begin!

---

**Plan Complete** ✅

**Branch**: `002-rag-chatbot`
**Next Command**: `/sp.tasks` (generate atomic implementation tasks)
**Artifacts**:
- `specs/002-rag-chatbot/plan.md` (this file)
- `specs/002-rag-chatbot/research.md`
- `specs/002-rag-chatbot/data-model.md`
- `specs/002-rag-chatbot/contracts/openapi.yaml`
- `specs/002-rag-chatbot/quickstart.md`
