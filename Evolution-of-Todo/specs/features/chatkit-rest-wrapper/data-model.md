# Data Model: ChatKit REST Wrapper

**Feature**: ChatKit REST Wrapper Layer
**Date**: 2026-02-01
**Input**: spec.md (REQ-001 to REQ-006), research.md (session management pattern)

---

## Overview

This document defines the data entities, relationships, and validation rules for the ChatKit REST wrapper layer. **Key Decision**: Reuse existing `conversation` and `message` tables (no schema changes required).

---

## Entity Definitions

### 1. Session (maps to `conversation` table)

**Purpose**: Represents a chat session for a user. Sessions contain threads, threads contain messages.

**Database Table**: `conversation` (EXISTING - no changes)

**Schema**:
```sql
CREATE TABLE conversation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES user(id) ON DELETE CASCADE,
    title TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(id, user_id)  -- Composite index for user-scoped queries
);

CREATE INDEX idx_conversation_user_id ON conversation(user_id);
```

**SQLModel Representation** (EXISTING):
```python
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime

class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False, index=True)
    title: str | None = Field(default=None, max_length=200)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation", cascade_delete=True)
    user: "User" = Relationship(back_populates="conversations")

    model_config = ConfigDict(strict=True)
```

**Validation Rules**:
- `id`: Must be valid UUID v4
- `user_id`: Must exist in `user` table (foreign key constraint)
- `title`: Auto-generated from first message content (max 200 chars)
- `created_at`: Immutable after creation
- `updated_at`: Updated on every message addition

**State Transitions**:
```
[None] → POST /sessions → [Created] → POST /threads → [Active] → DELETE /sessions → [Deleted]
```

**Constraints**:
- Max 10 active sessions per user (enforced at application layer)
- Cascade delete: Deleting session deletes all threads and messages
- User-scoped queries: `WHERE conversation.user_id = :current_user_id`

---

### 2. Thread (implicit - not a separate table)

**Purpose**: Represents a conversation thread within a session. In ChatKit data model, threads are implicit (sessions contain message arrays).

**Database Representation**: Messages belong to `conversation` (no separate `thread` table)

**REST API Representation**:
```python
class ThreadResponse(BaseModel):
    id: UUID  # Same as conversation.id (1:1 mapping)
    session_id: UUID  # Same as conversation.id
    created_at: datetime

    model_config = ConfigDict(strict=True)
```

**Mapping Logic**:
- In ChatKit SDK: Session has one thread
- In our REST API: `POST /sessions/{id}/threads` creates first thread implicitly
- Thread ID = Conversation ID (1:1 relationship)

**Validation Rules**:
- Thread creation only allowed once per session (idempotent)
- Thread ID must match parent session ID
- User must own the parent session

---

### 3. Message (maps to `message` table)

**Purpose**: Individual messages in a conversation (user messages, assistant responses, tool calls).

**Database Table**: `message` (EXISTING - may need tool_calls column)

**Schema**:
```sql
CREATE TABLE message (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    tool_calls JSONB,  -- POTENTIAL NEW COLUMN (verify if exists)
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_message_conversation_id ON message(conversation_id);
CREATE INDEX idx_message_created_at ON message(created_at);
```

**SQLModel Representation**:
```python
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"

class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", nullable=False, index=True)
    role: MessageRole = Field(nullable=False)
    content: str = Field(nullable=False)
    tool_calls: dict | None = Field(default=None, sa_type=JSONB)  # OpenAI tool call format
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")

    model_config = ConfigDict(strict=True)
```

**Validation Rules**:
- `id`: Must be valid UUID v4
- `conversation_id`: Must exist in `conversation` table
- `role`: Must be one of: user, assistant, system, tool
- `content`: Cannot be empty string (min length: 1)
- `tool_calls`: If present, must be valid JSON matching OpenAI format
- `created_at`: Immutable, auto-set on creation

**Tool Calls Schema** (if `role == "assistant"`):
```python
# OpenAI tool call format
{
    "tool_calls": [
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "add_task",
                "arguments": "{\"title\": \"Buy milk\", \"priority\": \"high\"}"
            }
        }
    ]
}
```

**Constraints**:
- Max 100 messages per conversation (enforced at application layer)
- Messages are append-only (no updates/deletes)
- User-scoped access via `conversation.user_id`

---

## Relationships

```
User (1) ──< (many) Conversation
    │
    └─ Conversation (1) ──< (many) Message
```

**Foreign Key Cascade**:
- `DELETE User` → CASCADE DELETE `Conversation` → CASCADE DELETE `Message`
- `DELETE Conversation` → CASCADE DELETE `Message`

**Query Optimization**:
- Index on `conversation.user_id` (user session listing)
- Index on `message.conversation_id` (message history retrieval)
- Index on `message.created_at` (chronological ordering)

---

## Pydantic Models (Request/Response)

### Session Models

**CreateSessionRequest** (REQ-001):
```python
class CreateSessionRequest(BaseModel):
    # No body required - empty POST accepted
    pass
```

**SessionResponse** (REQ-001):
```python
class SessionResponse(BaseModel):
    success: bool = True
    data: SessionData

class SessionData(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = ConfigDict(strict=True)
```

**SessionListResponse** (REQ-004):
```python
class SessionListItem(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int  # Computed field

    model_config = ConfigDict(strict=True)

class SessionListResponse(BaseModel):
    success: bool = True
    data: list[SessionListItem]
```

**SessionDetailResponse** (REQ-005):
```python
class MessageDetail(BaseModel):
    id: UUID
    role: MessageRole
    content: str
    tool_calls: dict | None
    created_at: datetime

    model_config = ConfigDict(strict=True)

class SessionDetailData(BaseModel):
    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageDetail]

    model_config = ConfigDict(strict=True)

class SessionDetailResponse(BaseModel):
    success: bool = True
    data: SessionDetailData
```

### Thread Models

**CreateThreadRequest** (REQ-002):
```python
class CreateThreadRequest(BaseModel):
    # No body required - thread created implicitly
    pass
```

**ThreadResponse** (REQ-002):
```python
class ThreadData(BaseModel):
    id: UUID  # Same as conversation.id
    session_id: UUID
    created_at: datetime

    model_config = ConfigDict(strict=True)

class ThreadResponse(BaseModel):
    success: bool = True
    data: ThreadData
```

### Message Models

**SendMessageRequest** (REQ-003):
```python
class MessageContent(BaseModel):
    type: Literal["input_text"] = "input_text"
    text: str = Field(min_length=1, max_length=10000)

    model_config = ConfigDict(strict=True)

class UserMessage(BaseModel):
    role: Literal["user"] = "user"
    content: list[MessageContent]

    model_config = ConfigDict(strict=True)

class SendMessageRequest(BaseModel):
    message: UserMessage

    model_config = ConfigDict(strict=True)
```

**StreamingMessageResponse** (REQ-003):
```
# Server-Sent Events format (text/event-stream)
data: {"type": "response.chunk", "content": "Hello"}

data: {"type": "response.chunk", "content": " world"}

data: {"type": "response.done", "finish_reason": "stop"}

[done]
```

---

## Validation Summary

### Session Validation

| Field | Rule | Error Code |
|-------|------|------------|
| `user_id` | Must exist in `user` table | 401 Unauthorized |
| Active session count | Must be < 10 | 429 Too Many Requests |
| `id` | Must be valid UUID v4 | 400 Bad Request |
| Ownership | `conversation.user_id == current_user.id` | 403 Forbidden |

### Thread Validation

| Field | Rule | Error Code |
|-------|------|------------|
| `session_id` | Must exist in `conversation` table | 404 Not Found |
| Ownership | `conversation.user_id == current_user.id` | 403 Forbidden |
| Thread count | Max 1 per session (idempotent) | 200 OK (return existing) |

### Message Validation

| Field | Rule | Error Code |
|-------|------|------------|
| `thread_id` | Must exist (same as `conversation.id`) | 404 Not Found |
| `message.content[].text` | Min length: 1, max: 10000 | 400 Bad Request |
| `message.role` | Must be "user" | 400 Bad Request |
| Message count | Max 100 per conversation | 429 Too Many Requests |

---

## Query Patterns

### Count Active Sessions (REQ-001 precondition)

```python
async def count_user_sessions(db: AsyncSession, user_id: UUID) -> int:
    """Count active sessions for rate limiting."""
    stmt = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one()
```

### List User Sessions (REQ-004)

```python
async def list_user_sessions(db: AsyncSession, user_id: UUID) -> list[SessionListItem]:
    """List all sessions for authenticated user."""
    stmt = (
        select(
            Conversation.id,
            Conversation.user_id,
            Conversation.title,
            Conversation.created_at,
            Conversation.updated_at,
            func.count(Message.id).label("message_count")
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )
    result = await db.execute(stmt)
    return [SessionListItem(**row._asdict()) for row in result]
```

### Get Session with Messages (REQ-005)

```python
async def get_session_with_messages(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID
) -> SessionDetailData | None:
    """Get session with full message history."""
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == session_id, Conversation.user_id == user_id)
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()

    if not conversation:
        return None

    return SessionDetailData(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageDetail(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                tool_calls=msg.tool_calls,
                created_at=msg.created_at
            )
            for msg in sorted(conversation.messages, key=lambda m: m.created_at)
        ]
    )
```

### Delete Session (REQ-006)

```python
async def delete_session(
    db: AsyncSession,
    session_id: UUID,
    user_id: UUID
) -> bool:
    """Delete session and cascade to messages."""
    stmt = delete(Conversation).where(
        Conversation.id == session_id,
        Conversation.user_id == user_id
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
```

---

## Schema Migration Requirements

**VERIFICATION NEEDED**: Check if `message` table has `tool_calls` column

**If Missing**:
```sql
-- Migration: add_tool_calls_to_message.sql
ALTER TABLE message ADD COLUMN tool_calls JSONB;
CREATE INDEX idx_message_tool_calls ON message USING GIN (tool_calls);
```

**Alembic Migration**:
```python
# alembic/versions/xxx_add_tool_calls_column.py
def upgrade():
    op.add_column('message', sa.Column('tool_calls', postgresql.JSONB(), nullable=True))
    op.create_index('idx_message_tool_calls', 'message', ['tool_calls'], postgresql_using='gin')

def downgrade():
    op.drop_index('idx_message_tool_calls', table_name='message')
    op.drop_column('message', 'tool_calls')
```

**If Exists**: No migration required

---

## Data Integrity Constraints

### Application-Level Constraints

- **Max Sessions**: 10 per user (checked before `POST /sessions`)
- **Max Messages**: 100 per conversation (checked before `POST /runs`)
- **Rate Limiting**: 30 requests/minute per user (middleware)
- **Session Age**: 30 days inactive → soft delete (background job, not in scope)

### Database-Level Constraints

- **Foreign Keys**: CASCADE DELETE on `conversation` → `message`
- **Unique Constraints**: `(id, user_id)` on `conversation` (composite index)
- **Check Constraints**: `role IN ('user', 'assistant', 'system', 'tool')`
- **NOT NULL**: `user_id`, `role`, `content`, `created_at`

---

## Performance Considerations

### Indexed Queries

✅ **Fast**:
- `SELECT * FROM conversation WHERE user_id = ?` (indexed)
- `SELECT * FROM message WHERE conversation_id = ?` (indexed)
- `SELECT COUNT(*) FROM conversation WHERE user_id = ?` (indexed)

⚠️ **Slow** (but acceptable for Phase 3):
- `SELECT * FROM message WHERE content LIKE '%query%'` (full-text search not indexed)
- Session list with message counts (requires JOIN, but limited to 10 sessions max)

### Query Optimization Strategies

- **Eager Loading**: Use `selectinload(Conversation.messages)` for session detail
- **Pagination**: Not implemented in Phase 3 (max 10 sessions, acceptable)
- **Caching**: Not implemented in Phase 3 (acceptable technical debt)

---

## Next Steps

1. ✅ **data-model.md created**
2. **Next**: Generate `contracts/` OpenAPI schemas
3. **Next**: Generate `quickstart.md` developer guide
4. **Verify**: Check if `message.tool_calls` column exists (run migration if needed)
5. **Implementation**: Use these models in `chatkit_rest.py`

---

**Data Model Status**: ✅ **COMPLETE**
**Schema Changes Required**: ⚠️ VERIFY `tool_calls` column exists
**Query Patterns Defined**: 5 patterns documented
**Validation Rules**: 15 rules with HTTP error codes
