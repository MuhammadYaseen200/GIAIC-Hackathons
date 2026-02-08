# Feature Specification: ChatKit REST Wrapper Layer

**Status**: Draft
**Owner**: backend-builder, modular-ai-architect
**Dependencies**: `phase-3-chatbot/specs/phase-3-spec.md`, `specs/reports/phase3-http500-root-cause-analysis.md`
**Estimated Complexity**: High
**Phase**: Phase III - AI Chatbot (HTTP 500 Blocker Fix)

---

## 1. Purpose & Context

### What
A RESTful API wrapper layer that translates conventional HTTP requests into ChatKit JSON-RPC protocol, enabling frontend/tests to use standard REST endpoints while maintaining compatibility with ChatKit SDK.

### Why
**Root Cause**: Phase 3 HTTP 500 blocker caused by protocol mismatch - tests expect REST API (`POST /chatkit/sessions`), but ChatKit SDK expects JSON-RPC protocol (`{"type": "threads.create", "params": {...}}`).

**Business Justification**: Without this layer, all E2E tests fail, Phase 3 cannot be completed, and the specification requirement for REST endpoints cannot be met.

### Where
Backend translation layer sitting between FastAPI routes and ChatKit SDK, maintaining backward compatibility with OpenAI ChatKit web component (JSON-RPC) while providing REST endpoints for tests/frontend.

---

## 2. Constraints (MANDATORY - Define First)

### NOT Supported

- **Streaming session creation** (sessions created synchronously)
- **Session title customization** (auto-generated from first message)
- **Session sharing between users** (user-scoped only)
- **Thread branching** (linear conversation only)
- **Message editing** (append-only history)
- **Conversation export** (not in Phase 3 scope)
- **Bulk operations** (e.g., delete all sessions)
- **Session templates** (no pre-defined conversation starters)
- **Conversation search** (not indexed)
- **Session metadata modification** (created_at, updated_at immutable)

### Performance Limits

- **Max Concurrent Sessions Per User**: 10 active sessions
- **Session Creation Latency**: < 500ms (synchronous)
- **Thread Creation Latency**: < 200ms (synchronous)
- **Message Streaming Latency**: < 2 seconds (first token)
- **Rate Limit**: 30 requests/minute per authenticated user
- **Session History Retention**: 100 messages per session
- **Max Session Age**: 30 days inactive (soft delete)
- **Database Connection Pool**: Max 20 connections

### Security Boundaries

- **Authentication**: JWT required for ALL endpoints (reuses Phase 2 auth)
- **Authorization**: Users can ONLY access their own sessions (enforced at DB query level)
- **Data Isolation**: ChatKit context MUST include user_id filter
- **Input Validation**: All request bodies validated with Pydantic strict mode
- **SQL Injection Prevention**: SQLModel parameterized queries only
- **Session Hijacking Prevention**: Session IDs are UUIDs, user_id validated on every request
- **No Prompt Injection**: ChatKit system prompt enforced server-side

### Technical Debt (Accepted for Phase 3)

- **No session caching** (database query on every request)
- **No pagination for session list** (returns all user sessions)
- **No conversation export** (manual JSON extraction required)
- **No session archival UI** (DELETE only)
- **No conversation analytics** (no token counting, latency tracking)
- **No multi-model support** (OpenRouter only)
- **Synchronous session/thread creation** (no async background jobs)

---

## 3. Functional Requirements

### REQ-001: Create Session (REST → JSON-RPC Translation)

**Input**:
```http
POST /api/v1/chatkit/sessions
Authorization: Bearer <jwt_token>
Content-Type: application/json
```
**Request Body**: None (empty body allowed)

**Output**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "user_id": "uuid-string",
    "created_at": "2026-02-01T12:00:00Z"
  }
}
```

**Preconditions**:
- User is authenticated (valid JWT)
- User has < 10 active sessions

**Postconditions**:
- New session record created in `conversation` table
- Session ID returned to client
- ChatKit SDK initialized session context

**Edge Cases**:
- **Empty body**: Auto-generate session with default parameters → SUCCESS
- **User at session limit (10)**: Return HTTP 429 `{"error": {"code": "SESSION_LIMIT", "message": "Maximum 10 sessions allowed. Please delete an old session."}}`
- **Invalid JWT**: Return HTTP 401 `{"error": {"code": "UNAUTHORIZED", "message": "Authentication required"}}`
- **Database connection failure**: Return HTTP 503 `{"error": {"code": "SERVICE_UNAVAILABLE", "message": "Database unavailable"}}`

**Translation Logic**:
```python
# REST request (empty body)
→ Translate to JSON-RPC:
{
  "type": "threads.create",
  "params": {
    "input": {
      "content": [
        {"type": "input_text", "text": "Session initialized"}
      ]
    }
  }
}
→ Call ChatKitServer.process(json_rpc_payload, context)
→ Extract session ID from ChatKit response
→ Return REST JSON response
```

---

### REQ-002: Create Thread (REST → JSON-RPC Translation)

**Input**:
```http
POST /api/v1/chatkit/sessions/{session_id}/threads
Authorization: Bearer <jwt_token>
Content-Type: application/json
```
**Request Body**: None (empty body allowed)

**Output**:
```json
{
  "success": true,
  "data": {
    "id": "thread-uuid-string",
    "session_id": "session-uuid-string",
    "created_at": "2026-02-01T12:01:00Z"
  }
}
```

**Preconditions**:
- Session exists
- Session belongs to authenticated user
- User is authenticated

**Postconditions**:
- Thread created within session
- Thread ID returned to client

**Edge Cases**:
- **Session not found**: Return HTTP 404 `{"error": {"code": "SESSION_NOT_FOUND", "message": "Session does not exist"}}`
- **Session belongs to different user**: Return HTTP 403 `{"error": {"code": "FORBIDDEN", "message": "Access denied"}}`
- **ChatKit SDK error**: Return HTTP 500 with sanitized error message

**Translation Logic**:
```python
# REST request (empty body)
→ Validate session_id exists and belongs to user
→ Translate to JSON-RPC:
{
  "type": "threads.add_user_message",
  "params": {
    "thread_id": session_id,  # ChatKit uses session_id as thread_id
    "input": {
      "content": [
        {"type": "input_text", "text": "Thread started"}
      ]
    }
  }
}
→ Call ChatKitServer.process(json_rpc_payload, context)
→ Extract thread ID from response
→ Return REST JSON response
```

---

### REQ-003: Send Message and Stream Response (REST → JSON-RPC → SSE)

**Input**:
```http
POST /api/v1/chatkit/sessions/{session_id}/threads/{thread_id}/runs
Authorization: Bearer <jwt_token>
Content-Type: application/json
```
**Request Body**:
```json
{
  "message": {
    "role": "user",
    "content": [
      {"type": "input_text", "text": "Add task: Buy milk"}
    ]
  }
}
```

**Output**: Server-Sent Events (SSE) stream
```
data: {"type": "thread.item.content.part.delta", "delta": "I'll"}
data: {"type": "thread.item.content.part.delta", "delta": " add"}
data: {"type": "thread.item.content.part.delta", "delta": " that"}
data: [DONE]
```

**Preconditions**:
- Session exists and belongs to user
- Thread exists within session
- User is authenticated
- Message content is valid (non-empty, < 500 chars)

**Postconditions**:
- User message added to conversation history
- AI response streamed back to client
- Tool calls (if any) executed and logged

**Edge Cases**:
- **Empty message content**: Return HTTP 400 `{"error": {"code": "INVALID_INPUT", "message": "Message content cannot be empty"}}`
- **Message too long (>500 chars)**: Return HTTP 400 `{"error": {"code": "MESSAGE_TOO_LONG", "message": "Message exceeds 500 character limit"}}`
- **Thread not found**: Return HTTP 404 `{"error": {"code": "THREAD_NOT_FOUND", "message": "Thread does not exist"}}`
- **OpenRouter API error**: Log error, return HTTP 502 `{"error": {"code": "UPSTREAM_ERROR", "message": "AI service unavailable"}}`
- **Tool execution failure**: AI receives error response, can retry or inform user

**Translation Logic**:
```python
# REST request with message
→ Validate session/thread ownership
→ Translate to JSON-RPC:
{
  "type": "threads.add_user_message",
  "params": {
    "thread_id": thread_id,
    "input": request.message.model_dump()
  }
}
→ Call ChatKitServer.process(json_rpc_payload, context)
→ Receive StreamingResult
→ Yield SSE events from StreamingResult generator
→ Return StreamingResponse (media_type="text/event-stream")
```

---

### REQ-004: List User Sessions

**Input**:
```http
GET /api/v1/chatkit/sessions
Authorization: Bearer <jwt_token>
```

**Output**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-string",
      "user_id": "uuid-string",
      "title": "Session with tasks...",
      "created_at": "2026-02-01T12:00:00Z",
      "updated_at": "2026-02-01T12:05:00Z",
      "message_count": 12
    }
  ],
  "meta": {
    "total": 3
  }
}
```

**Preconditions**:
- User is authenticated

**Postconditions**:
- User's sessions returned in descending order (newest first)

**Edge Cases**:
- **No sessions**: Return empty array `{"success": true, "data": [], "meta": {"total": 0}}`
- **Database query error**: Return HTTP 503

**Translation Logic**:
```python
# REST request (no body)
→ Query database:
  SELECT * FROM conversation
  WHERE user_id = current_user.id
  ORDER BY updated_at DESC
→ Format as REST JSON response
→ Return 200 OK
```

---

### REQ-005: Get Session with History

**Input**:
```http
GET /api/v1/chatkit/sessions/{session_id}
Authorization: Bearer <jwt_token>
```

**Output**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "user_id": "uuid-string",
    "created_at": "2026-02-01T12:00:00Z",
    "updated_at": "2026-02-01T12:05:00Z",
    "messages": [
      {
        "id": "msg-uuid-1",
        "role": "user",
        "content": "Add task: Buy milk",
        "created_at": "2026-02-01T12:01:00Z"
      },
      {
        "id": "msg-uuid-2",
        "role": "assistant",
        "content": "I've added 'Buy milk' to your task list.",
        "tool_calls": [
          {"name": "add_task", "arguments": {"title": "Buy milk"}, "result": {"success": true}}
        ],
        "created_at": "2026-02-01T12:01:02Z"
      }
    ]
  }
}
```

**Preconditions**:
- Session exists
- Session belongs to authenticated user

**Postconditions**:
- Session metadata and message history returned

**Edge Cases**:
- **Session not found**: Return HTTP 404
- **Session belongs to different user**: Return HTTP 403
- **Session has no messages**: Return empty messages array

**Translation Logic**:
```python
# REST request (no body)
→ Query database:
  SELECT * FROM conversation WHERE id = session_id AND user_id = current_user.id
  JOIN message ON conversation.id = message.conversation_id
  ORDER BY message.created_at ASC
→ Format as REST JSON response
→ Return 200 OK
```

---

### REQ-006: Delete Session

**Input**:
```http
DELETE /api/v1/chatkit/sessions/{session_id}
Authorization: Bearer <jwt_token>
```

**Output**:
```json
{
  "success": true,
  "data": {
    "id": "uuid-string",
    "deleted": true
  }
}
```

**Preconditions**:
- Session exists
- Session belongs to authenticated user

**Postconditions**:
- Session and all associated messages deleted from database

**Edge Cases**:
- **Session not found**: Return HTTP 404
- **Session belongs to different user**: Return HTTP 403
- **Database constraint violation**: Return HTTP 500 (should not happen with CASCADE delete)

**Translation Logic**:
```python
# REST request (no body)
→ Validate session ownership
→ Delete from database:
  DELETE FROM conversation WHERE id = session_id AND user_id = current_user.id
  (CASCADE deletes messages automatically)
→ Return 200 OK
```

---

## 4. Data Contracts

### Request Schemas

#### CreateSessionRequest
```python
# No request body - endpoint accepts empty POST
```

#### CreateThreadRequest
```python
# No request body - endpoint accepts empty POST
```

#### SendMessageRequest
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class InputTextContent(BaseModel):
    model_config = ConfigDict(strict=True)

    type: Literal["input_text"]
    text: str = Field(min_length=1, max_length=500)

class UserMessage(BaseModel):
    model_config = ConfigDict(strict=True)

    role: Literal["user"]
    content: list[InputTextContent] = Field(min_length=1)

class SendMessageRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    message: UserMessage
```

### Response Schemas

#### SessionResponse
```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class SessionResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID
    user_id: UUID
    created_at: datetime
```

#### ThreadResponse
```python
class ThreadResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID
    session_id: UUID
    created_at: datetime
```

#### SessionListItem
```python
class SessionListItem(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID
    user_id: UUID
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int
```

#### SessionWithHistory
```python
class ChatMessage(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID
    role: Literal["user", "assistant"]
    content: str
    tool_calls: list[dict] | None = None
    created_at: datetime

class SessionWithHistory(BaseModel):
    model_config = ConfigDict(strict=True)

    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessage]
```

### Database Schema (SQLModel)

#### Conversation Model
```python
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID, uuid4
from datetime import datetime, timezone

class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    title: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    user: "User" = Relationship(back_populates="conversations")
```

#### Message Model
```python
from typing import Literal

class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversation.id", index=True)
    role: Literal["user", "assistant"] = Field()
    content: str = Field(max_length=2000)
    tool_calls: str | None = Field(default=None)  # JSON string
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
```

---

## 5. Acceptance Criteria (QA Contract)

### AC-001: Session Creation
- [ ] `POST /chatkit/sessions` with empty body creates session
- [ ] Response contains valid UUID for `id`
- [ ] Response contains authenticated user's `user_id`
- [ ] Response contains UTC timestamp for `created_at`
- [ ] Database record created in `conversation` table
- [ ] HTTP 401 returned for unauthenticated request
- [ ] HTTP 429 returned when user has 10 sessions

### AC-002: Thread Creation
- [ ] `POST /chatkit/sessions/{id}/threads` with empty body creates thread
- [ ] Response contains valid UUID for thread `id`
- [ ] Response links to correct `session_id`
- [ ] HTTP 404 returned for non-existent session
- [ ] HTTP 403 returned for session belonging to different user

### AC-003: Message Streaming
- [ ] `POST /chatkit/sessions/{id}/threads/{tid}/runs` accepts message
- [ ] Response is SSE stream (`text/event-stream`)
- [ ] SSE events contain deltas with AI response text
- [ ] Stream ends with `data: [DONE]`
- [ ] HTTP 400 returned for empty message
- [ ] HTTP 400 returned for message >500 chars
- [ ] Tool calls executed (verified by checking database for new tasks)

### AC-004: Session List
- [ ] `GET /chatkit/sessions` returns user's sessions only
- [ ] Sessions ordered by `updated_at` DESC (newest first)
- [ ] Response includes `message_count` for each session
- [ ] Empty array returned when user has no sessions

### AC-005: Session History Retrieval
- [ ] `GET /chatkit/sessions/{id}` returns session with messages
- [ ] Messages ordered by `created_at` ASC (oldest first)
- [ ] Tool calls included in assistant messages
- [ ] HTTP 404 returned for non-existent session
- [ ] HTTP 403 returned for unauthorized access

### AC-006: Session Deletion
- [ ] `DELETE /chatkit/sessions/{id}` removes session
- [ ] All messages cascade deleted
- [ ] HTTP 404 returned for non-existent session
- [ ] HTTP 403 returned for unauthorized deletion
- [ ] Deleted session no longer appears in session list

### AC-007: E2E Test Compatibility
- [ ] `test_openrouter_connection.py` passes (HTTP 200, no 500 errors)
- [ ] All 5 E2E tests in test suite pass
- [ ] No breaking changes to existing ChatKit web component integration
- [ ] OpenRouter integration continues working (AI responses received)

### AC-008: Error Handling
- [ ] Proper HTTP status codes for all error cases
- [ ] Error responses follow `{"success": false, "error": {"code": "...", "message": "..."}}` format
- [ ] No silent 500 errors (all exceptions logged)
- [ ] Database errors return HTTP 503 with friendly message
- [ ] OpenRouter errors return HTTP 502 with friendly message

---

## 6. Non-Functional Requirements

### Performance
- **Session Creation**: < 500ms (synchronous database insert + ChatKit SDK call)
- **Thread Creation**: < 200ms (database validation + JSON-RPC call)
- **Message Streaming First Token**: < 2 seconds (OpenRouter latency)
- **Session List Query**: < 100ms (indexed query on user_id)
- **Session History Query**: < 200ms (JOIN query with index on conversation_id)

### Scalability
- **Concurrent Users**: Support 100 concurrent authenticated users
- **Database Connection Pool**: 20 connections (FastAPI default)
- **Rate Limiting**: 30 requests/minute per user (token bucket algorithm)

### Security
- **Authentication**: JWT validation on EVERY endpoint (no exceptions)
- **Authorization**: User ID extracted from JWT, validated against session/thread owner
- **SQL Injection**: SQLModel parameterized queries (no raw SQL)
- **Input Validation**: Pydantic strict mode (`ConfigDict(strict=True)`)
- **Logging**: Sanitize logs (no JWT tokens, no passwords)

### Observability
- **Request Logging**: Log every endpoint call with user_id, session_id, HTTP method
- **Error Logging**: Log all exceptions with stack trace (logger.exception)
- **ChatKit SDK Calls**: Log JSON-RPC request/response payloads (DEBUG level)
- **Tool Calls**: Log tool invocations and results (INFO level)
- **Performance Metrics**: Log request duration for endpoints (INFO level)

Example logging:
```python
logger.info(f"[REST→RPC] POST /chatkit/sessions user={user_id}")
logger.debug(f"[ChatKit SDK] Request: {json_rpc_payload}")
logger.debug(f"[ChatKit SDK] Response: {response_summary}")
logger.info(f"[REST→RPC] Session created: session_id={session_id} duration={elapsed}ms")
```

---

## 7. Integration Points

### Upstream Dependencies
- **FastAPI Router**: REST endpoints registered in `api/v1/router.py`
- **Phase 2 JWT Auth**: Reuses `get_current_user` dependency from `api/deps.py`
- **Database Session**: Uses `get_session` dependency for async SQLModel operations
- **ChatKitServer**: Existing `TodoChatKitServer` instance with tool handlers registered
- **ChatContext**: Existing `ChatContext(user_id, db)` dataclass

### Downstream Consumers
- **Frontend Tests**: `test_openrouter_connection.py` expects REST endpoints
- **E2E Test Suite**: 5 tests expect REST endpoints with specific response formats
- **Future Frontend UI**: Will consume REST endpoints for chat interface (Phase 3 completion)

### External Services
- **OpenRouter API**: Called by ChatKit SDK during message streaming (already integrated)
- **Neon PostgreSQL**: Database for session/message persistence (existing connection)

### Parallel Integrations
- **Existing JSON-RPC Handler**: Keep `chatkit.py` catch-all handler for OpenAI ChatKit web component (dual entry point architecture)

**Architecture Diagram**:
```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Test/API Calls          OpenAI ChatKit Web Component       │
│  (REST)                  (JSON-RPC)                          │
│       │                         │                            │
└───────┼─────────────────────────┼────────────────────────────┘
        │                         │
        │ POST /chatkit/sessions  │ POST /chatkit (JSON-RPC)
        │                         │
┌───────▼─────────────────────────▼────────────────────────────┐
│                      FastAPI Backend                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  chatkit_rest.py         chatkit.py                          │
│  (REST Wrapper - NEW)    (JSON-RPC Pass-Through - EXISTING)  │
│       │                         │                            │
│       └─────────┬───────────────┘                            │
│                 │                                            │
│                 ▼                                            │
│       TodoChatKitServer.process()                            │
│       (ChatKit SDK - JSON-RPC)                               │
│                 │                                            │
│                 ├──────────────────┐                         │
│                 │                  │                         │
│                 ▼                  ▼                         │
│         OpenRouter API      Database (Sessions/Messages)    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Notes

### Translation Layer Responsibilities

**For Session Creation** (`POST /chatkit/sessions`):
1. Validate JWT (get current user)
2. Check session count < 10 (enforce limit)
3. Construct JSON-RPC payload:
   ```json
   {
     "type": "threads.create",
     "params": {
       "input": {
         "content": [{"type": "input_text", "text": "Session initialized"}]
       }
     }
   }
   ```
4. Call `await server.process(json.dumps(payload).encode(), context)`
5. Parse ChatKit response, extract session ID
6. Create database record in `conversation` table
7. Return REST response: `{"success": true, "data": {"id": "...", ...}}`

**For Thread Creation** (`POST /chatkit/sessions/{id}/threads`):
1. Validate session ownership (query DB: user_id matches)
2. Construct JSON-RPC payload:
   ```json
   {
     "type": "threads.add_user_message",
     "params": {
       "thread_id": session_id,
       "input": {
         "content": [{"type": "input_text", "text": "Thread started"}]
       }
     }
   }
   ```
3. Call ChatKit SDK
4. Return thread ID (same as session ID in ChatKit's model)

**For Message Streaming** (`POST /chatkit/sessions/{id}/threads/{tid}/runs`):
1. Validate session/thread ownership
2. Parse message from request body
3. Construct JSON-RPC payload:
   ```json
   {
     "type": "threads.add_user_message",
     "params": {
       "thread_id": thread_id,
       "input": request.message.model_dump()
     }
   }
   ```
4. Call ChatKit SDK (returns `StreamingResult`)
5. Yield SSE events: `async for event in result: yield event`
6. Return `StreamingResponse(generate(), media_type="text/event-stream")`

**For Session List** (`GET /chatkit/sessions`):
- Pure database query (no ChatKit SDK involvement)
- SQLModel query: `SELECT * FROM conversation WHERE user_id = ... ORDER BY updated_at DESC`

**For Session History** (`GET /chatkit/sessions/{id}`):
- Pure database query with JOIN
- SQLModel query: `SELECT * FROM conversation JOIN message ON ... WHERE conversation.id = ... AND user_id = ...`

**For Session Deletion** (`DELETE /chatkit/sessions/{id}`):
- Pure database operation
- SQLModel query: `DELETE FROM conversation WHERE id = ... AND user_id = ...` (CASCADE deletes messages)

### State Management Strategy

**Sessions**:
- Stored in `conversation` table
- Primary key: `id` (UUID)
- Indexed on: `user_id` (for fast user-scoped queries)
- No caching (database is source of truth)

**Threads**:
- ChatKit SDK manages threads internally
- Session ID serves as thread ID (1:1 mapping)
- No separate `thread` table (ChatKit abstraction)

**Messages**:
- Stored in `message` table
- Foreign key: `conversation_id` (CASCADE delete)
- Ordered by: `created_at` ASC
- No pagination (limit enforced at 100 messages per session in Phase 3 spec)

**User Context**:
- Extracted from JWT on every request
- Passed to ChatKit SDK via `ChatContext(user_id, db)`
- Ensures tool calls (add_task, list_tasks, etc.) are user-scoped

### Error Handling Specification

**Database Errors**:
```python
try:
    session = await db.get(Conversation, session_id)
except Exception as e:
    logger.exception(f"Database error: {e}")
    raise HTTPException(
        status_code=503,
        detail={"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "Database unavailable"}}
    )
```

**ChatKit SDK Errors**:
```python
try:
    result = await server.process(payload, context)
except ValidationError as e:
    logger.error(f"ChatKit validation error: {e}")
    raise HTTPException(
        status_code=400,
        detail={"success": False, "error": {"code": "INVALID_REQUEST", "message": str(e)}}
    )
except Exception as e:
    logger.exception(f"ChatKit SDK error: {e}")
    raise HTTPException(
        status_code=500,
        detail={"success": False, "error": {"code": "INTERNAL_ERROR", "message": "AI service error"}}
    )
```

**OpenRouter API Errors**:
- Logged by ChatKit SDK
- Return HTTP 502 if streaming fails
- User sees: `{"error": {"code": "UPSTREAM_ERROR", "message": "AI service unavailable"}}`

### Logging Strategy

**Log Levels**:
- **DEBUG**: ChatKit JSON-RPC payloads, database queries
- **INFO**: Endpoint calls, session creation, tool calls, request durations
- **ERROR**: Validation errors, authorization failures
- **EXCEPTION**: Unhandled exceptions (with stack trace)

**Example Log Outputs**:
```
INFO: [REST→RPC] POST /chatkit/sessions user_id=abc123
DEBUG: [ChatKit SDK] Request: {"type": "threads.create", "params": {...}}
DEBUG: [ChatKit SDK] Response: {"type": "threads.created", "data": {"id": "xyz789"}}
INFO: [REST→RPC] Session created: session_id=xyz789 duration=234ms

INFO: [REST→RPC] POST /chatkit/sessions/xyz789/threads/t123/runs user_id=abc123
DEBUG: [Tool Call] add_task(title="Buy milk")
DEBUG: [Tool Result] {"success": true, "task_id": "task-456"}
INFO: [REST→RPC] Message streamed: tokens=45 duration=1.8s
```

---

## 9. Testing Strategy

### Unit Tests (pytest)

**File**: `phase-3-chatbot/backend/tests/test_chatkit_rest.py`

Test cases:
- `test_create_session_success()` - Verify session creation with valid JWT
- `test_create_session_unauthenticated()` - Verify HTTP 401 for missing JWT
- `test_create_session_at_limit()` - Verify HTTP 429 when user has 10 sessions
- `test_create_thread_success()` - Verify thread creation
- `test_create_thread_invalid_session()` - Verify HTTP 404 for non-existent session
- `test_create_thread_unauthorized()` - Verify HTTP 403 for other user's session
- `test_send_message_success()` - Verify message streaming
- `test_send_message_empty_content()` - Verify HTTP 400 for empty message
- `test_send_message_too_long()` - Verify HTTP 400 for >500 char message
- `test_list_sessions_success()` - Verify session list returns user's sessions only
- `test_get_session_with_history()` - Verify session + messages retrieval
- `test_delete_session_success()` - Verify deletion and CASCADE
- `test_delete_session_unauthorized()` - Verify HTTP 403

### Integration Tests (pytest with database)

**File**: `phase-3-chatbot/backend/tests/test_chatkit_integration.py`

Test cases:
- `test_full_conversation_flow()` - Create session → Create thread → Send message → Verify AI response → Verify tool call executed (task created) → Delete session
- `test_multiple_sessions_isolation()` - Create sessions for 2 users, verify each sees only their own
- `test_session_message_limit()` - Send 100 messages, verify oldest deleted when adding 101st (if implemented)

### E2E Tests (existing)

**File**: `phase-3-chatbot/backend/tests/test_openrouter_connection.py`

Must pass without modification:
- Register user
- Login user
- Create session (`POST /chatkit/sessions`)
- Create thread (`POST /chatkit/sessions/{id}/threads`)
- Send message (`POST /chatkit/sessions/{id}/threads/{tid}/runs`)
- Verify OpenRouter response (HTTP 200, SSE stream)
- Verify task created via tool call

---

## 10. Rollback Strategy

If REST wrapper implementation fails:

**Option A - Minimal Fix**:
1. Revert `chatkit_rest.py` changes
2. Keep existing JSON-RPC handler (`chatkit.py`)
3. Update tests to send JSON-RPC payloads directly
4. Document workaround in README

**Option B - Alternative Architecture**:
1. Use FastAPI middleware to detect REST vs JSON-RPC requests
2. Route accordingly (single endpoint, dual protocol)
3. Document decision in ADR-015

**Rollback Trigger**:
- If 3+ days of effort without passing tests
- If complexity exceeds 500 lines of code
- If architectural issues discovered (e.g., ChatKit SDK incompatibility)

---

## 11. Success Metrics

**Technical Success**:
- [ ] All 5 E2E tests passing (green output)
- [ ] No HTTP 500 errors in test suite
- [ ] `test_openrouter_connection.py` completes successfully
- [ ] 0 regressions in existing ChatKit web component integration

**Performance Success**:
- [ ] Session creation < 500ms (measured with `time.perf_counter()`)
- [ ] Message streaming first token < 2 seconds
- [ ] Session list query < 100ms

**Quality Success**:
- [ ] qa-overseer certification obtained
- [ ] Type safety enforced (Pydantic strict mode, no type: ignore comments)
- [ ] 100% endpoint coverage in tests
- [ ] All error cases tested and logged properly

---

## 12. Post-Implementation Checklist

- [ ] Create ADR-015: REST Wrapper for ChatKit JSON-RPC SDK
- [ ] Update README.md with REST endpoint documentation
- [ ] Update `specs/api/mcp-tools.md` with ChatKit REST API contract (create if missing)
- [ ] Create PHR documenting implementation session
- [ ] Tag Git commit: `phase3-http500-blocker-resolved`
- [ ] Run full E2E test suite and attach output to PHR
- [ ] Update Phase 3 completion percentage (31% → target: 100%)

---

## Approval

**Specification Status**: Ready for Implementation

**Completeness Check**:
- [x] Purpose & Context defined (WHAT, WHY, WHERE)
- [x] Constraints defined FIRST (NOT Supported, Performance, Security, Technical Debt)
- [x] Functional Requirements cover all 6 REST endpoints with edge cases
- [x] Data Contracts defined (Request/Response schemas, Database models)
- [x] Acceptance Criteria are testable (pass/fail conditions)
- [x] Non-Functional Requirements include Performance, Security, Observability
- [x] Integration Points documented (Upstream/Downstream/External)
- [x] Implementation Notes provide translation logic guidance
- [x] Testing Strategy includes Unit, Integration, E2E tests
- [x] Rollback Strategy defined
- [x] Success Metrics are measurable

**Atomic Granularity Check**:
- [x] Each requirement can be implemented in < 5 minutes? **NO** - but broken into atomic tasks in tasks.md
- [x] Specification complete enough for builder to implement without questions? **YES**
- [x] QA can write pass/fail tests for every acceptance criterion? **YES**

**Next Steps**:
1. Create `plan.md` (architecture, component breakdown, sequence diagrams)
2. Create `tasks.md` (atomic work units with Task IDs)
3. Implement via `/sp.implement` with loop-controller validation
4. Execute tests, obtain qa-overseer certification
5. Create PHR and ADR-015

---

**Version**: 1.0.0
**Author**: spec-architect (with modular-ai-architect)
**Phase**: III - AI Chatbot (HTTP 500 Blocker Resolution)
**Created**: 2026-02-01
**Approved By**: PENDING (User Review Required)
