# RAG Chatbot Research & Technology Decisions

**Feature**: RAG Chatbot (Physical AI Tutor)
**Created**: 2025-12-13
**Status**: Complete

## Overview

This document resolves all technical unknowns and documents technology choices for the RAG Chatbot implementation.

## 1. OpenAI Agents/ChatKit SDK Integration

### Decision
Use **OpenAI Python SDK v1.0+** with **Structured Outputs** for RAG response generation. Do NOT use a separate "Agents SDK" or "ChatKit SDK" as these are not official OpenAI products.

### Rationale
- **OpenAI Python SDK** is the official library for GPT-4 and embeddings
- **Structured Outputs** (via `response_format` parameter) ensures JSON responses with citations
- **Function Calling** can be added later for dynamic tool use (e.g., search, calculator)
- **Streaming Responses** via `stream=True` for real-time UI updates

### Implementation Pattern
```python
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Generate embedding
embedding_response = await client.embeddings.create(
    model="text-embedding-3-small",
    input=user_question
)

# Search Qdrant for top-k chunks
chunks = await qdrant_client.search(
    collection_name="textbook_chunks",
    query_vector=embedding_response.data[0].embedding,
    limit=5,
    score_threshold=0.7
)

# Generate response with context
chat_response = await client.chat.completions.create(
    model="gpt-4-turbo-preview",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context: {chunks}\n\nQuestion: {user_question}"}
    ],
    response_format={"type": "json_object"}  # Structured output
)
```

### Alternatives Considered
- **LangChain**: Rejected due to unnecessary abstraction overhead for MVP
- **LlamaIndex**: Rejected - designed for more complex multi-agent systems
- **Haystack**: Rejected - better for production pipelines, overkill for hackathon

### References
- OpenAI Python SDK: https://github.com/openai/openai-python
- Structured Outputs Guide: https://platform.openai.com/docs/guides/structured-outputs

---

## 2. Qdrant Vector Database Integration

### Decision
Use **Qdrant Cloud Free Tier** with **qdrant-client** Python library for vector storage and retrieval.

### Rationale
- **1GB free tier** is sufficient for textbook content (spec calculates 553KB usage)
- **Managed service** eliminates DevOps overhead during hackathon
- **Python client** has async support for FastAPI integration
- **Collections API** allows semantic chunking with metadata

### Implementation Pattern
```python
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

client = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

# Create collection (one-time setup)
await client.create_collection(
    collection_name="textbook_chunks",
    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
)

# Ingest chunks
await client.upsert(
    collection_name="textbook_chunks",
    points=[
        PointStruct(
            id=chunk_id,
            vector=embedding,
            payload={
                "text": chunk_text,
                "chapter_id": "module-1-ros2-basics/chapter-2",
                "module_id": "module-1",
                "title": "Chapter 2: Publisher-Subscriber",
                "section": "Creating a Publisher",
                "file_path": "docs/module-1-ros2-basics/chapter-2-pub-sub.md"
            }
        )
    ]
)

# Search
results = await client.search(
    collection_name="textbook_chunks",
    query_vector=query_embedding,
    limit=5,
    score_threshold=0.7
)
```

### Key Configuration Decisions
- **Distance Metric**: COSINE (standard for OpenAI embeddings)
- **Vector Dimensions**: 1536 (text-embedding-3-small output size)
- **Collection Name**: `textbook_chunks`
- **Payload Schema**: Includes metadata for citation generation

### Alternatives Considered
- **Pinecone**: Rejected - free tier requires credit card, Qdrant doesn't
- **Weaviate**: Rejected - requires Docker deployment, adds complexity
- **ChromaDB**: Rejected - SQLite-based, not suitable for production deployment

### References
- Qdrant Cloud: https://cloud.qdrant.io
- Python Client Docs: https://qdrant.tech/documentation/quick-start/

---

## 3. Neon Serverless Postgres Schema Design

### Decision
Use **Neon Serverless Postgres Free Tier** (0.5GB storage) for chat history and query logs.

### Rationale
- **Serverless Architecture**: Auto-scales to zero, no idle charges
- **PostgreSQL Compatibility**: Can use SQLAlchemy ORM for type-safe queries
- **Free Tier**: 0.5GB storage sufficient for MVP (chat history is text-only)
- **Connection Pooling**: Built-in pooling for FastAPI async operations

### Schema Design

```sql
-- Chat sessions table
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    chapter_context TEXT,  -- Optional: Which chapter user was reading
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    citations JSONB,  -- Array of {title, url, chapter_id}
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Query logs (analytics)
CREATE TABLE query_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tokens_used INTEGER,
    response_time_ms INTEGER,
    chunks_retrieved INTEGER,
    avg_similarity_score FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_messages_session ON chat_messages(session_id, timestamp);
CREATE INDEX idx_query_logs_session ON query_logs(session_id);
CREATE INDEX idx_sessions_started ON chat_sessions(started_at DESC);
```

### SQLAlchemy Models Pattern
```python
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    chapter_context = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Alternatives Considered
- **Supabase**: Rejected - requires learning additional auth layer
- **PlanetScale**: Rejected - MySQL-based, no JSONB support for citations
- **SQLite**: Rejected - not suitable for serverless deployment

### References
- Neon Docs: https://neon.tech/docs
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html

---

## 4. Content Chunking Strategy (ADR-003 Reference)

### Decision
Use **512-token chunks** with **50-token overlap** for RAG retrieval.

### Rationale
- **512 tokens ≈ 2048 characters**: Balances context vs. granularity
- **50-token overlap**: Prevents semantic breaks at chunk boundaries
- **Total chunks for 13 chapters**: ~65 chunks (spec: 553KB / 8.5KB per chunk)
- **Fits GPT-4 context**: 5 chunks × 512 tokens = 2560 tokens (well within 128k limit)

### Chunking Algorithm
```python
import tiktoken

def chunk_markdown(text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Chunk markdown text using tiktoken tokenizer.

    Args:
        text: Full markdown content
        chunk_size: Target tokens per chunk
        overlap: Overlap tokens between chunks

    Returns:
        List of text chunks
    """
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = encoding.encode(text)

    chunks = []
    start = 0

    while start < len(tokens):
        end = start + chunk_size
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Overlap for next chunk
        start = end - overlap

    return chunks
```

### Metadata Extraction
Each chunk includes:
- `chapter_id`: e.g., "module-1-ros2-basics/chapter-2"
- `module_id`: e.g., "module-1"
- `title`: Human-readable chapter title
- `section`: Extracted from markdown headers (`##` or `###`)
- `file_path`: Relative path for citation links

### Alternatives Considered
- **256 tokens**: Rejected - too granular, loses context
- **1024 tokens**: Rejected - exceeds OpenAI embedding limit (8191 tokens) risk
- **Recursive character splitter**: Rejected - tokens are more accurate for LLMs

### References
- Tiktoken Library: https://github.com/openai/tiktoken
- Chunking Best Practices: https://www.pinecone.io/learn/chunking-strategies/

---

## 5. Select-to-Ask Feature Implementation

### Decision
Use **browser Selection API** with React state management to capture highlighted text as context.

### Rationale
- **Native Browser API**: No external libraries needed
- **Docusaurus Compatible**: Works with static site generation
- **Minimal Performance Impact**: Event listener on mouseup only

### Implementation Pattern
```typescript
// src/components/ChatWidget/SelectToAsk.tsx
import React, { useEffect, useState } from 'react';

export function useSelectedText() {
  const [selectedText, setSelectedText] = useState<string>('');

  useEffect(() => {
    function handleSelection() {
      const selection = window.getSelection();
      const text = selection?.toString().trim() || '';

      if (text.length > 10) {  // Minimum 10 chars
        setSelectedText(text);
      }
    }

    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, []);

  return selectedText;
}

// Usage in ChatWidget
const selectedText = useSelectedText();

const handleSendMessage = async (userMessage: string) => {
  const context = selectedText
    ? `Selected text from page: "${selectedText}"\n\n${userMessage}`
    : userMessage;

  // Send context to API
  const response = await fetch('/api/chat', {
    method: 'POST',
    body: JSON.stringify({
      question: context,
      session_id: sessionId
    })
  });
};
```

### UX Behavior
1. User highlights text on any Docusaurus page
2. Chat widget shows "Use selected text" badge
3. User types question, widget automatically includes selected text as context
4. Backend receives: `"Selected text: [highlighted content]\n\nQuestion: [user input]"`

### Alternatives Considered
- **External library (react-highlight)**: Rejected - unnecessary dependency
- **Copy-paste prompt**: Rejected - poor UX, requires manual action
- **Browser extension**: Rejected - out of scope for web app

### References
- Selection API: https://developer.mozilla.org/en-US/docs/Web/API/Selection
- React Hooks Best Practices: https://react.dev/reference/react/hooks

---

## 6. Docusaurus Root Swizzling

### Decision
Swizzle **Docusaurus `Root` component** to inject ChatWidget globally without modifying theme internals.

### Rationale
- **Root component**: Wraps entire Docusaurus app, ensures widget appears on all pages
- **Non-invasive**: Doesn't modify Layout theme (avoids breaking on Docusaurus upgrades)
- **Client-side only**: Uses `ExecutionEnvironment.canUseDOM` to avoid SSR issues

### Implementation Steps
```bash
# 1. Swizzle Root component (safe, non-ejecting)
npm run swizzle @docusaurus/theme-classic Root -- --wrap

# Creates: src/theme/Root.tsx
```

```typescript
// src/theme/Root.tsx
import React from 'react';
import ExecutionEnvironment from '@docusaurus/ExecutionEnvironment';
import ChatWidget from '@site/src/components/ChatWidget';

export default function Root({children}) {
  return (
    <>
      {children}
      {ExecutionEnvironment.canUseDOM && <ChatWidget />}
    </>
  );
}
```

### Why Not Layout Component
- **Layout is theme-specific**: Breaking changes in Docusaurus updates
- **Root is stable**: Guaranteed to exist across all themes
- **Better separation**: ChatWidget is app-level, not theme-level

### Alternatives Considered
- **Custom plugin**: Rejected - overkill for single component
- **Modify docusaurus.config.js scripts**: Rejected - global script injection is hacky
- **MDX import in every page**: Rejected - manual, error-prone

### References
- Swizzling Guide: https://docusaurus.io/docs/swizzling
- Root Component: https://docusaurus.io/docs/advanced/client#root

---

## 7. FastAPI Async Architecture

### Decision
Use **async/await** for all I/O operations (database, OpenAI API, Qdrant) with **dependency injection** for clients.

### Rationale
- **Non-blocking I/O**: Handles 100 concurrent users (SC-007) without thread pool exhaustion
- **Dependency Injection**: FastAPI's `Depends()` ensures proper connection lifecycle
- **Type Safety**: Pydantic models validate request/response schemas

### Implementation Pattern
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from uuid import UUID

app = FastAPI()

# Pydantic models
class ChatRequest(BaseModel):
    question: str
    session_id: UUID
    chapter_context: str | None = None

class Citation(BaseModel):
    title: str
    url: str
    chapter_id: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    tokens_used: int

# Dependency injection
async def get_db_session():
    async with async_session_maker() as session:
        yield session

async def get_qdrant_client():
    client = AsyncQdrantClient(...)
    try:
        yield client
    finally:
        await client.close()

# Endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db_session),
    qdrant: AsyncQdrantClient = Depends(get_qdrant_client)
):
    # All operations are async
    embedding = await generate_embedding(request.question)
    chunks = await qdrant.search(query_vector=embedding, ...)
    response = await generate_response(request.question, chunks)

    # Log to database
    await log_query(db, request.session_id, request.question, response)

    return ChatResponse(...)
```

### Error Handling Strategy
```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    # Log to monitoring system
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

### Alternatives Considered
- **Synchronous FastAPI**: Rejected - blocks event loop, poor scalability
- **Flask + Celery**: Rejected - adds Redis dependency, overkill for MVP
- **Django**: Rejected - too heavy for simple API

### References
- FastAPI Async SQL: https://fastapi.tiangolo.com/advanced/async-sql-databases/
- Dependency Injection: https://fastapi.tiangolo.com/tutorial/dependencies/

---

## 8. Rate Limiting Implementation

### Decision
Use **slowapi** library with **session-based limits** (10 requests/minute per session).

### Rationale
- **Prevents API abuse**: FR-017 requires rate limiting
- **Session-based**: Fair limits per user, not global
- **Redis-free**: Uses in-memory storage (acceptable for single-instance MVP)

### Implementation Pattern
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/chat")
@limiter.limit("10/minute")
async def chat_endpoint(request: Request, ...):
    ...
```

### Alternatives Considered
- **Custom middleware**: Rejected - reinventing the wheel
- **Redis-backed limits**: Rejected - adds dependency, overkill for MVP
- **API Gateway rate limiting**: Rejected - deployment-specific, not portable

### References
- slowapi: https://github.com/laurents/slowapi

---

## Technology Stack Summary

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Backend Framework | FastAPI | 0.110+ | Async-first, type-safe, auto-docs |
| Database | Neon Postgres | Serverless | Free tier, auto-scaling, PostgreSQL compatibility |
| Vector DB | Qdrant Cloud | Free (1GB) | Managed, Python async client, sufficient storage |
| LLM | OpenAI GPT-4 Turbo | gpt-4-turbo-preview | Best reasoning, structured outputs |
| Embeddings | OpenAI | text-embedding-3-small | 1536-dim, cost-effective |
| Frontend Framework | React 18 | 18.x | Docusaurus dependency, hooks support |
| Static Site | Docusaurus | 3.x | Already installed, MDX support |
| Styling | Tailwind CSS | 3.x | Utility-first, Docusaurus compatible |
| ORM | SQLAlchemy | 2.0+ | Async support, type-safe queries |
| Rate Limiting | slowapi | 0.1.9+ | FastAPI integration, in-memory |
| Tokenization | tiktoken | 0.5.1+ | Official OpenAI tokenizer |

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Pages (Frontend)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Docusaurus Static Site                                     │ │
│  │  - React ChatWidget Component                              │ │
│  │  - Select-to-Ask (Browser Selection API)                   │ │
│  │  - Markdown Content (13 chapters)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTPS API Calls
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Railway (Backend)                           │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ FastAPI Service                                            │ │
│  │  - POST /api/chat (async endpoint)                         │ │
│  │  - Rate Limiting (slowapi)                                 │ │
│  │  - OpenAI SDK (embeddings + chat)                          │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────┬──────────────────────────┬──────────────────────┬────────┘
       │                          │                      │
       ▼                          ▼                      ▼
┌──────────────┐       ┌──────────────────┐   ┌──────────────────┐
│ Neon Postgres│       │  Qdrant Cloud    │   │   OpenAI API     │
│  (Chat Logs) │       │ (Vector Search)  │   │ (LLM + Embed)    │
│   0.5GB Free │       │    1GB Free      │   │   Paid Tier      │
└──────────────┘       └──────────────────┘   └──────────────────┘
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-username.github.io",  # GitHub Pages
        "http://localhost:3000"  # Local dev
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## Security Considerations

1. **Environment Variables**: All API keys in `.env`, never committed
2. **CORS**: Whitelist only GitHub Pages and localhost
3. **Rate Limiting**: 10 req/min per session prevents abuse
4. **Input Validation**: Pydantic models validate all inputs
5. **SQL Injection**: SQLAlchemy ORM prevents raw SQL
6. **XSS**: React escapes all user content by default

---

## Cost Estimation (Monthly)

| Service | Usage | Cost |
|---------|-------|------|
| OpenAI Embeddings | 65 chunks × $0.00002/1k tokens ≈ 33k tokens | $0.0007 |
| OpenAI GPT-4 | 1000 queries × 1k tokens × $0.01/1k | $10.00 |
| Qdrant Cloud | 1GB free tier | $0.00 |
| Neon Postgres | 0.5GB free tier | $0.00 |
| Railway | 500 hours free tier | $0.00 |
| GitHub Pages | Unlimited free | $0.00 |
| **Total** | | **~$10/month** ✅ |

Meets constraint: "Must operate within $10/month budget" (spec line 168)

---

## Open Questions Resolved

✅ **Q1**: Which OpenAI SDK to use?
**A**: OpenAI Python SDK v1.0+ (official library)

✅ **Q2**: How to handle chat history persistence?
**A**: Neon Postgres with SQLAlchemy async ORM

✅ **Q3**: Chunking strategy for textbook content?
**A**: 512 tokens with 50-token overlap (ADR-003)

✅ **Q4**: How to inject ChatWidget globally?
**A**: Swizzle Docusaurus Root component

✅ **Q5**: Rate limiting implementation?
**A**: slowapi library (in-memory, session-based)

---

## Next Steps

1. **Phase 1**: Create data-model.md with entity schemas
2. **Phase 1**: Generate API contracts (OpenAPI spec)
3. **Phase 1**: Create quickstart.md with setup instructions
4. **Phase 2**: Generate tasks.md with implementation checklist

**Status**: All research complete, ready for design phase ✅
