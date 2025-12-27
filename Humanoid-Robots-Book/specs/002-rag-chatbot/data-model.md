# RAG Chatbot Data Model

**Feature**: RAG Chatbot (Physical AI Tutor)
**Created**: 2025-12-13
**Status**: Complete

## Overview

This document defines all data entities, schemas, and relationships for the RAG Chatbot system.

---

## 1. Domain Entities

### 1.1 ChatSession

**Purpose**: Represents a conversation thread initiated by a user.

**Lifecycle**: Created when user opens chat widget, persists for session duration.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session_id` | UUID | Primary Key, Auto-generated | Unique session identifier |
| `started_at` | Timestamp | Not Null, Default NOW() | Session creation time |
| `chapter_context` | String | Optional | Chapter ID user was reading (e.g., "module-1-ros2-basics/chapter-2") |
| `user_agent` | String | Optional | Browser user agent for analytics |
| `created_at` | Timestamp | Not Null, Default NOW() | Record creation time |

**Business Rules**:
- `session_id` generated client-side (UUID v4) and sent with every request
- `chapter_context` extracted from current URL path if user on chapter page
- Session expires when chat widget is closed (client-side only)

**State Transitions**:
```
[Created] → [Active] → [Closed]
   ↓           ↓           ↓
(started_at) (messages) (no server-side cleanup, logs persist)
```

---

### 1.2 ChatMessage

**Purpose**: Represents a single message in a conversation (user or assistant).

**Lifecycle**: Created when user sends message or assistant responds.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `message_id` | UUID | Primary Key, Auto-generated | Unique message identifier |
| `session_id` | UUID | Foreign Key → ChatSession, Not Null | Parent session |
| `role` | Enum | "user" \| "assistant", Not Null | Message sender |
| `content` | Text | Not Null, Max 10,000 chars | Message text (markdown for assistant) |
| `citations` | JSONB | Optional | Array of citation objects (assistant only) |
| `timestamp` | Timestamp | Not Null, Default NOW() | Message creation time |
| `created_at` | Timestamp | Not Null, Default NOW() | Record creation time |

**Business Rules**:
- User messages: `citations` is NULL
- Assistant messages: `citations` array contains ≥1 citation object
- `content` for assistant messages is markdown-formatted
- Cascade delete: If `ChatSession` deleted, all messages deleted

**Citations Schema**:
```json
{
  "citations": [
    {
      "title": "Chapter 2: Publisher-Subscriber Communication",
      "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
      "chapter_id": "module-1-ros2-basics/chapter-2"
    }
  ]
}
```

**Validation Rules**:
- `role` must be exactly "user" or "assistant"
- `content` length: 1–10,000 characters
- `citations` (if present): Array of objects with required keys `title`, `url`, `chapter_id`

---

### 1.3 VectorChunk

**Purpose**: Textbook content segment stored in Qdrant for RAG retrieval.

**Lifecycle**: Created during ingestion script run, read-only during chat.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `chunk_id` | String | Unique ID | Format: `{chapter_id}_{chunk_index}` (e.g., "module-1-chapter-2_003") |
| `text` | String | 512 tokens ± 50 | Actual text content from markdown |
| `embedding` | Float[1536] | Not Null | OpenAI text-embedding-3-small vector |
| `metadata` | Object | Not Null | Structured metadata for citations |

**Metadata Schema**:
```json
{
  "chapter_id": "module-1-ros2-basics/chapter-2",
  "module_id": "module-1",
  "title": "Chapter 2: Publisher-Subscriber Communication",
  "section": "Creating a Publisher",
  "file_path": "docs/module-1-ros2-basics/chapter-2-pub-sub.md"
}
```

**Storage Location**: Qdrant Cloud collection `textbook_chunks`

**Business Rules**:
- `chunk_id` ensures uniqueness across all chapters
- `text` chunked using tiktoken with 512-token size, 50-token overlap
- `embedding` generated via OpenAI `text-embedding-3-small` API
- `metadata.file_path` is relative to Docusaurus site root

**Indexing**: Cosine similarity search on `embedding` field

---

### 1.4 Citation

**Purpose**: Reference to source textbook chapter in assistant responses.

**Lifecycle**: Generated during RAG response creation, embedded in ChatMessage.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | String | Not Null | Human-readable chapter title |
| `url` | String | Not Null, Valid path | Relative URL to chapter markdown |
| `chapter_id` | String | Not Null | Matches VectorChunk metadata |

**Example**:
```json
{
  "title": "Chapter 6: URDF Modeling",
  "url": "../module-2-digital-twin/chapter-6-urdf-modeling.md",
  "chapter_id": "module-2-digital-twin/chapter-6"
}
```

**Business Rules**:
- `url` must be valid Docusaurus relative path
- `chapter_id` must match existing VectorChunk metadata
- Citations sorted by similarity score (highest first)

**Rendering**: Frontend converts to clickable markdown links

---

### 1.5 QueryLog

**Purpose**: Analytics record for monitoring chatbot performance and accuracy.

**Lifecycle**: Created after every successful chat response.

**Fields**:
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `query_id` | UUID | Primary Key, Auto-generated | Unique log identifier |
| `session_id` | UUID | Foreign Key → ChatSession, Optional | Parent session (NULL if session deleted) |
| `question` | Text | Not Null | User's original question |
| `answer` | Text | Not Null | Assistant's response (without citations) |
| `tokens_used` | Integer | Not Null | Total tokens (prompt + completion) |
| `response_time_ms` | Integer | Not Null | End-to-end latency in milliseconds |
| `chunks_retrieved` | Integer | Not Null, Default 5 | Number of vector chunks retrieved |
| `avg_similarity_score` | Float | Optional | Average cosine similarity of retrieved chunks |
| `timestamp` | Timestamp | Not Null, Default NOW() | Query execution time |

**Business Rules**:
- `tokens_used` includes both prompt and completion tokens
- `response_time_ms` measures from API request to final response
- `chunks_retrieved` typically 5 (per FR-004), may be less if threshold not met
- `avg_similarity_score` calculated from Qdrant search results

**Analytics Queries**:
- Average response time: `SELECT AVG(response_time_ms) FROM query_logs WHERE timestamp > NOW() - INTERVAL '1 day'`
- Token usage trends: `SELECT DATE(timestamp), SUM(tokens_used) FROM query_logs GROUP BY DATE(timestamp)`
- Popular questions: `SELECT question, COUNT(*) FROM query_logs GROUP BY question ORDER BY COUNT(*) DESC LIMIT 10`

---

## 2. Database Schema (Neon Postgres)

### 2.1 DDL (Data Definition Language)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Chat sessions table
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    chapter_context TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) BETWEEN 1 AND 10000),
    citations JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Query logs table
CREATE TABLE query_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    chunks_retrieved INTEGER NOT NULL DEFAULT 5,
    avg_similarity_score FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_messages_session_time ON chat_messages(session_id, timestamp DESC);
CREATE INDEX idx_query_logs_session ON query_logs(session_id);
CREATE INDEX idx_query_logs_timestamp ON query_logs(timestamp DESC);
CREATE INDEX idx_sessions_started ON chat_sessions(started_at DESC);

-- JSONB index for citations search (if needed)
CREATE INDEX idx_messages_citations ON chat_messages USING GIN (citations);
```

### 2.2 Constraints Summary

| Table | Constraint Type | Definition |
|-------|----------------|------------|
| chat_messages | Foreign Key | `session_id` → chat_sessions (CASCADE DELETE) |
| chat_messages | Check | `role IN ('user', 'assistant')` |
| chat_messages | Check | `LENGTH(content) BETWEEN 1 AND 10000` |
| query_logs | Foreign Key | `session_id` → chat_sessions (SET NULL on delete) |

---

## 3. Qdrant Vector Database Schema

### 3.1 Collection Configuration

```python
from qdrant_client.models import Distance, VectorParams

collection_config = {
    "collection_name": "textbook_chunks",
    "vectors_config": VectorParams(
        size=1536,  # OpenAI text-embedding-3-small dimension
        distance=Distance.COSINE  # Cosine similarity
    )
}
```

### 3.2 Point Structure

```python
from qdrant_client.models import PointStruct

point = PointStruct(
    id="module-1-ros2-basics_chapter-2_003",  # chunk_id
    vector=[0.123, -0.456, ...],  # 1536-dimensional embedding
    payload={
        "text": "In ROS 2, a publisher sends messages to a topic...",
        "chapter_id": "module-1-ros2-basics/chapter-2",
        "module_id": "module-1",
        "title": "Chapter 2: Publisher-Subscriber Communication",
        "section": "Creating a Publisher",
        "file_path": "docs/module-1-ros2-basics/chapter-2-pub-sub.md"
    }
)
```

### 3.3 Search Query

```python
search_result = await client.search(
    collection_name="textbook_chunks",
    query_vector=query_embedding,  # 1536-dim vector from user question
    limit=5,  # Top-5 results (FR-004)
    score_threshold=0.7,  # Minimum cosine similarity (FR-004)
    with_payload=True  # Include metadata in results
)
```

**Search Response Structure**:
```python
[
    ScoredPoint(
        id="module-1-chapter-2_003",
        score=0.89,  # Cosine similarity
        payload={
            "text": "...",
            "chapter_id": "...",
            "title": "...",
            ...
        }
    ),
    ...
]
```

---

## 4. API Request/Response Schemas

### 4.1 POST /api/chat Request

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, UUID4
from typing import Optional

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="User's question")
    session_id: UUID4 = Field(..., description="Client-generated session UUID")
    chapter_context: Optional[str] = Field(None, description="Current chapter ID (e.g., 'module-1-ros2-basics/chapter-2')")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "How do I create a ROS 2 subscriber?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "chapter_context": "module-1-ros2-basics/chapter-2"
            }
        }
```

**JSON Example**:
```json
{
  "question": "How do I create a ROS 2 subscriber?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "chapter_context": "module-1-ros2-basics/chapter-2"
}
```

### 4.2 POST /api/chat Response

**Pydantic Model**:
```python
from typing import List

class Citation(BaseModel):
    title: str
    url: str
    chapter_id: str

class ChatResponse(BaseModel):
    answer: str = Field(..., description="Markdown-formatted response")
    citations: List[Citation] = Field(..., min_items=1, description="Source citations")
    tokens_used: int = Field(..., ge=0, description="Total tokens consumed")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To create a ROS 2 subscriber, inherit from `rclpy.node.Node` and use `create_subscription()`:\n\n```python\nclass MySubscriber(Node):\n    def __init__(self):\n        super().__init__('my_subscriber')\n        self.subscription = self.create_subscription(\n            String,\n            'topic_name',\n            self.listener_callback,\n            10\n        )\n```",
                "citations": [
                    {
                        "title": "Chapter 2: Publisher-Subscriber Communication",
                        "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
                        "chapter_id": "module-1-ros2-basics/chapter-2"
                    }
                ],
                "tokens_used": 1247
            }
        }
```

**JSON Example**:
```json
{
  "answer": "To create a ROS 2 subscriber, inherit from `rclpy.node.Node`...",
  "citations": [
    {
      "title": "Chapter 2: Publisher-Subscriber Communication",
      "url": "../module-1-ros2-basics/chapter-2-pub-sub.md",
      "chapter_id": "module-1-ros2-basics/chapter-2"
    }
  ],
  "tokens_used": 1247
}
```

### 4.3 Error Response

```python
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# Example
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 10 requests per minute. Try again in 45 seconds."
}
```

---

## 5. Relationships and Cardinality

```
ChatSession (1) ──< (N) ChatMessage
     │
     │ (optional)
     └──< (N) QueryLog

VectorChunk (N) ──> (1) Citation (derived relationship)
```

**Relationships**:
1. **ChatSession → ChatMessage**: One-to-Many
   - One session contains multiple messages
   - Cascade delete: Deleting session deletes all messages

2. **ChatSession → QueryLog**: One-to-Many (nullable)
   - One session generates multiple query logs
   - Set NULL on delete: Logs persist even if session deleted

3. **VectorChunk → Citation**: Many-to-One (derived)
   - Multiple chunks may reference same chapter
   - Citation created from VectorChunk metadata during retrieval

---

## 6. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User sends message                                           │
│    ChatRequest { question, session_id, chapter_context }        │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Generate embedding (OpenAI text-embedding-3-small)           │
│    question → embedding[1536]                                   │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Search Qdrant                                                │
│    VectorChunk.search(embedding, limit=5, threshold=0.7)        │
│    Returns: [ {text, metadata}, ... ]                           │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. Generate response (OpenAI GPT-4 Turbo)                       │
│    Prompt: System + Context + Question → Answer                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Create citations from VectorChunk metadata                   │
│    metadata → Citation { title, url, chapter_id }               │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Save to Neon Postgres                                        │
│    ChatMessage (user message + assistant message)               │
│    QueryLog (question, answer, tokens, latency)                 │
└────────────────────────┬────────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Return response                                              │
│    ChatResponse { answer, citations, tokens_used }              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Validation Rules Summary

| Entity | Field | Validation |
|--------|-------|------------|
| ChatRequest | `question` | Length: 1–500 chars |
| ChatRequest | `session_id` | Valid UUID v4 |
| ChatRequest | `chapter_context` | Optional, matches pattern `module-\d+-\w+/chapter-\d+` |
| ChatMessage | `role` | Enum: "user" \| "assistant" |
| ChatMessage | `content` | Length: 1–10,000 chars |
| ChatMessage | `citations` | If role=assistant: Array length ≥ 1 |
| Citation | `url` | Valid relative path (starts with `../` or `/`) |
| Citation | `chapter_id` | Matches VectorChunk metadata pattern |
| VectorChunk | `text` | 512 tokens ± 50 (validated during ingestion) |
| VectorChunk | `embedding` | Array length = 1536 |
| QueryLog | `tokens_used` | Integer ≥ 0 |
| QueryLog | `response_time_ms` | Integer ≥ 0 |
| QueryLog | `chunks_retrieved` | Integer 1–5 |
| QueryLog | `avg_similarity_score` | Float 0.0–1.0 |

---

## 8. SQLAlchemy ORM Models

```python
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func
from uuid import uuid4

class Base(AsyncAttrs, DeclarativeBase):
    pass

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    started_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    chapter_context = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_role"),
        CheckConstraint("LENGTH(content) BETWEEN 1 AND 10000", name="check_content_length"),
    )

class QueryLog(Base):
    __tablename__ = "query_logs"

    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.session_id", ondelete="SET NULL"), nullable=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    chunks_retrieved = Column(Integer, nullable=False, default=5)
    avg_similarity_score = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    session = relationship("ChatSession", back_populates="query_logs")
```

---

## 9. Migration Files

**File**: `backend/db/migrations/002_rag_chatbot_schema.sql`

```sql
-- Migration: RAG Chatbot Schema
-- Created: 2025-12-13
-- Description: Creates tables for chat sessions, messages, and query logs

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Chat sessions
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    chapter_context TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Chat messages
CREATE TABLE chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL CHECK (LENGTH(content) BETWEEN 1 AND 10000),
    citations JSONB,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Query logs
CREATE TABLE query_logs (
    query_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES chat_sessions(session_id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    tokens_used INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL,
    chunks_retrieved INTEGER NOT NULL DEFAULT 5,
    avg_similarity_score FLOAT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_session_time ON chat_messages(session_id, timestamp DESC);
CREATE INDEX idx_query_logs_session ON query_logs(session_id);
CREATE INDEX idx_query_logs_timestamp ON query_logs(timestamp DESC);
CREATE INDEX idx_sessions_started ON chat_sessions(started_at DESC);
CREATE INDEX idx_messages_citations ON chat_messages USING GIN (citations);
```

---

## 10. Acceptance Criteria

**Data Model Completeness**:
- ✅ All entities from spec defined (ChatSession, ChatMessage, VectorChunk, Citation, QueryLog)
- ✅ All fields have type constraints and validation rules
- ✅ Relationships and cardinality documented
- ✅ Database schema matches Pydantic models
- ✅ Migration script ready for deployment

**Traceability to Requirements**:
- ✅ FR-011: `ChatRequest` schema matches endpoint spec
- ✅ FR-012: `ChatResponse` schema includes citations and tokens
- ✅ FR-014: VectorChunk uses 512-token chunks with 50-token overlap
- ✅ FR-016: VectorChunk metadata includes all required fields
- ✅ FR-018: QueryLog captures all analytics metrics

**Ready for Implementation**: All data structures defined, ready for Phase 2 (tasks.md generation).
