# Research Document: ChatKit REST Wrapper Implementation

**Feature**: ChatKit REST Wrapper Layer
**Date**: 2026-02-01
**Researchers**: modular-ai-architect, spec-architect
**Input**: phase3-http500-root-cause-analysis.md, phase3-ai-integration-stack.md

---

## Executive Summary

This research resolves all technical unknowns for implementing a REST-to-JSON-RPC translation layer for ChatKit SDK integration. All "NEEDS CLARIFICATION" items from Technical Context have been investigated and architectural decisions documented with rationale.

---

## Research Tasks Completed

### 1. ChatKit SDK Protocol Analysis

**Question**: What protocol does ChatKit SDK use? REST or JSON-RPC?

**Investigation**:
- Analyzed ChatKit SDK source code (`chatkit/server.py:389`)
- Reviewed error logs showing `TypeAdapter[ChatKitReq].validate_json(b'')`
- Examined request type definitions (`ThreadsCreateReq`, `ThreadsAddUserMessageReq`, etc.)

**Finding**: **JSON-RPC Protocol**

ChatKit SDK expects all requests in this format:
```json
{
  "type": "threads.create",
  "params": {
    "input": {
      "content": [{"type": "input_text", "text": "Hello"}]
    }
  }
}
```

**Evidence**:
```python
# chatkit/server.py:389
parsed_request = TypeAdapter[ChatKitReq](ChatKitReq).validate_json(request)

# ChatKitReq is a union of:
# ThreadsCreateReq | ThreadsAddUserMessageReq | ThreadsGetByIdReq | ...
```

**Decision**: Build REST wrapper layer that translates HTTP requests to JSON-RPC payloads

**Rationale**:
- Spec requires REST API (`POST /chatkit/sessions`)
- ChatKit SDK requires JSON-RPC protocol
- Translation layer satisfies both requirements

**Alternatives Considered**:
- **Option A**: Rewrite tests to send JSON-RPC directly
  - **Rejected**: Violates spec requirement for REST endpoints
  - **Reason**: Frontend/tests expect conventional HTTP API

- **Option B**: Fork ChatKit SDK and add REST support
  - **Rejected**: High maintenance burden, violates dependency stability
  - **Reason**: SDK updates would break custom fork

- **Option C**: Use different chat SDK with native REST support
  - **Rejected**: Would require complete rewrite of Phase 3
  - **Reason**: OpenRouter integration already working with ChatKit

**Selected**: **Option D** - Build thin REST translation layer
  - **Pro**: Minimal code (single file)
  - **Pro**: Maintains both REST and JSON-RPC entry points
  - **Pro**: No modifications to existing ChatKit integration
  - **Con**: Introduces translation complexity (acceptable)

---

### 2. Session Management Pattern

**Question**: How should sessions be created in REST API?

**Investigation**:
- ChatKit SDK has no explicit "create session" method
- Sessions are created implicitly when first message is sent
- Our tests expect: `POST /sessions` → returns `{id}`

**Finding**: **Session-as-Resource Pattern**

REST API should treat sessions as resources:
1. `POST /sessions` creates empty session (returns UUID)
2. Session stored in database immediately
3. First `POST /threads` associates thread with session
4. Messages appended to thread via `POST /runs`

**Evidence**:
```python
# test_openrouter_connection.py:59-62
session_response = await client.post(
    f"{BASE_URL}/chatkit/sessions",
    headers={"Authorization": f"Bearer {token}"}
)
# Expects: {"id": "uuid", "user_id": "uuid", "created_at": "..."}
```

**Decision**: Create sessions on-demand when `POST /sessions` is called

**Rationale**:
- Matches RESTful resource design (sessions are first-class entities)
- Allows session listing/deletion before any messages sent
- Simplifies frontend state management (session ID known upfront)

**Alternatives Considered**:
- **Option A**: Create sessions lazily on first message
  - **Rejected**: Breaks REST semantics (POST /sessions should create session)
  - **Reason**: Would return 404 on `GET /sessions` before first message

- **Option B**: Create sessions during JWT login
  - **Rejected**: Tight coupling between auth and chat
  - **Reason**: Users may not want chat session immediately

**Selected**: **On-demand creation**
  - **Pro**: RESTful semantics maintained
  - **Pro**: Session ID available before chatting
  - **Con**: Empty sessions in database (acceptable)

---

### 3. Dual Entry Point Strategy

**Question**: Can REST and JSON-RPC endpoints coexist?

**Investigation**:
- Existing: `/api/v1/chatkit/*` → JSON-RPC handler (web component)
- New: `/api/v1/chatkit/sessions`, `/api/v1/chatkit/sessions/*/threads` → REST handler
- FastAPI routing priority: specific routes matched before catch-all

**Finding**: **Dual Entry Points Supported**

FastAPI routing allows this pattern:
```python
# Specific routes (higher priority)
@router.post("/sessions")  # REST - matched first
@router.post("/sessions/{id}/threads")  # REST

# Catch-all route (lower priority)
@router.api_route("/{path:path}", methods=["GET", "POST", ...])  # JSON-RPC
```

**Decision**: Maintain both entry points

**Rationale**:
- Web component needs JSON-RPC (OpenAI ChatKit standard)
- Tests/frontend need REST (spec requirement)
- No conflicts if routes registered in correct order

**Implementation Details**:
```python
# v1/router.py
from .chatkit_rest import router as chatkit_rest_router
from .chatkit import router as chatkit_jsonrpc_router

# Register REST first (specific routes have priority)
api_router.include_router(chatkit_rest_router, prefix="/chatkit", tags=["ChatKit REST"])
api_router.include_router(chatkit_jsonrpc_router, prefix="/chatkit", tags=["ChatKit JSON-RPC"])
```

**Alternatives Considered**:
- **Option A**: Single protocol (REST only, deprecate JSON-RPC)
  - **Rejected**: Breaks web component integration
  - **Reason**: OpenAI ChatKit web component requires JSON-RPC

- **Option B**: Different URL paths (/chatkit-rest vs /chatkit-rpc)
  - **Rejected**: Violates spec (spec defines /chatkit/sessions path)
  - **Reason**: Would require frontend changes

**Selected**: **Dual entry points with route priority**
  - **Pro**: Zero breaking changes
  - **Pro**: Both use cases supported
  - **Con**: Two routing paths (acceptable complexity)

---

### 4. Database Schema Reuse

**Question**: Do we need new database tables for REST sessions?

**Investigation**:
- Existing `conversation` table structure:
  ```sql
  CREATE TABLE conversation (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    title TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
  )
  ```
- Existing `message` table stores conversation history
- ChatKit SDK already persists to these tables via `store.py`

**Finding**: **Existing Schema Sufficient**

The `conversation` table already models sessions:
- `id` → session ID
- `user_id` → owner
- `title` → auto-generated from first message
- `created_at` / `updated_at` → timestamps

**Decision**: Reuse existing `conversation` table for REST sessions

**Rationale**:
- Schema matches REST session requirements
- No data duplication
- Maintains single source of truth
- ChatKitServer already handles persistence

**Alternatives Considered**:
- **Option A**: Create new `rest_session` table
  - **Rejected**: Data duplication, violates normalization
  - **Reason**: Session data would exist in two places

- **Option B**: Add `session_type` column to `conversation`
  - **Rejected**: Unnecessary complexity
  - **Reason**: All sessions are semantically identical

**Selected**: **Direct reuse**
  - **Pro**: Zero schema changes
  - **Pro**: Single data model
  - **Con**: None identified

---

### 5. Error Handling Strategy

**Question**: How should ChatKit SDK errors map to HTTP status codes?

**Investigation**:
- ChatKit SDK throws `pydantic.ValidationError` for malformed requests
- OpenRouter API returns various HTTP errors (401, 429, 500, 502)
- Database can throw connection errors, constraint violations
- JWT auth can fail (expired token, invalid signature)

**Finding**: **HTTP Status Code Mapping Required**

REST API clients expect semantic HTTP codes:
- `400` - Client error (validation failure)
- `401` - Unauthorized (JWT failure)
- `403` - Forbidden (user doesn't own resource)
- `404` - Not Found (session/thread doesn't exist)
- `429` - Rate Limit Exceeded
- `500` - Server error (unexpected exception)
- `502` - Bad Gateway (OpenRouter API failure)
- `503` - Service Unavailable (database down)

**Decision**: Explicit error mapping in REST wrapper

**Implementation**:
```python
def _handle_chatkit_error(e: Exception) -> JSONResponse:
    if isinstance(e, ValidationError):
        return JSONResponse(status_code=400, content={"error": str(e)})
    elif isinstance(e, OpenRouterAPIError):
        return JSONResponse(status_code=502, content={"error": "AI service unavailable"})
    elif isinstance(e, DBAPIError):
        return JSONResponse(status_code=503, content={"error": "Database unavailable"})
    else:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

**Rationale**:
- REST clients rely on status codes for error handling
- Enables proper retry logic (502/503 are retryable, 400 is not)
- Matches HTTP semantics

**Alternatives Considered**:
- **Option A**: Return 500 for all errors (simple)
  - **Rejected**: Poor developer experience
  - **Reason**: Client can't distinguish validation vs infrastructure errors

- **Option B**: Include error details in response body always
  - **Rejected**: Potential information leakage
  - **Reason**: Internal errors shouldn't expose stack traces to clients

**Selected**: **Semantic HTTP codes + safe error messages**
  - **Pro**: Standard REST error handling
  - **Pro**: Client-friendly debugging
  - **Con**: More complex error handling logic (acceptable)

---

### 6. Best Practices: FastAPI REST to JSON-RPC Translation

**Question**: What patterns exist for REST-to-RPC translation in Python?

**Investigation**:
- Reviewed FastAPI middleware patterns
- Studied gRPC-JSON transcoding (Google API design)
- Analyzed JSON-RPC libraries (jsonrpcserver, tinyrpc)

**Finding**: **Request Interceptor Pattern**

Standard pattern:
1. FastAPI route receives REST request
2. Extract path params, query params, body
3. Build RPC payload structure
4. Delegate to RPC handler
5. Transform RPC response to REST response

**Best Practices Identified**:
- **Type Safety**: Use Pydantic models for both REST and RPC payloads
- **Validation**: Validate REST request BEFORE translation
- **Logging**: Log both REST request and translated RPC payload (DEBUG level)
- **Error Propagation**: Don't swallow RPC errors, translate them
- **Idempotency**: Ensure POST /sessions is idempotent (return existing session if duplicate)

**Decision**: Implement Request Interceptor Pattern with FastAPI dependencies

**Code Pattern**:
```python
@router.post("/sessions")
async def create_session(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    # Step 1: Validate user has < 10 sessions
    session_count = await _count_user_sessions(db, current_user.id)
    if session_count >= 10:
        raise HTTPException(status_code=429, detail="Max sessions limit reached")

    # Step 2: Build JSON-RPC payload
    jsonrpc_payload = {
        "type": "threads.create",
        "params": {
            "input": {
                "content": [{"type": "input_text", "text": "Session initialized"}]
            }
        }
    }

    # Step 3: Delegate to ChatKitServer
    context = ChatContext(user_id=current_user.id, db=db)
    result = await server.process(json.dumps(jsonrpc_payload).encode(), context)

    # Step 4: Extract session ID from result
    session_id = result.get("id")

    # Step 5: Return REST response
    return {"success": True, "data": {"id": session_id, "user_id": current_user.id, "created_at": datetime.utcnow()}}
```

**Rationale**:
- Leverages FastAPI dependency injection (JWT, DB session)
- Type-safe with Pydantic
- Clear separation between REST and RPC layers

**Alternatives Considered**:
- **Option A**: Middleware-based translation
  - **Rejected**: Over-engineering for 6 endpoints
  - **Reason**: Middleware adds complexity for minimal code reuse

- **Option B**: Generic translation function
  - **Rejected**: Loses type safety
  - **Reason**: Each endpoint has different payload structure

**Selected**: **Per-endpoint translation functions**
  - **Pro**: Type-safe, explicit
  - **Pro**: Easy to debug
  - **Con**: Some code duplication (acceptable for 6 endpoints)

---

### 7. Streaming Response Passthrough

**Question**: Can SSE streaming responses pass through REST wrapper?

**Investigation**:
- ChatKit SDK returns `StreamingResult` for message runs
- `StreamingResult` yields SSE-formatted bytes: `b"data: {json}\n\n"`
- FastAPI `StreamingResponse` can forward bytes directly

**Finding**: **Passthrough Supported**

No translation needed for streaming:
```python
@router.post("/sessions/{session_id}/threads/{thread_id}/runs")
async def send_message(...):
    # ... translate REST request to JSON-RPC ...
    result = await server.process(jsonrpc_payload, context)

    if isinstance(result, StreamingResult):
        # Direct passthrough - no re-encoding
        async def generate():
            async for event in result:
                if isinstance(event, bytes):
                    yield event.decode('utf-8')

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
        )
```

**Decision**: Byte-for-byte forwarding (no re-encoding)

**Rationale**:
- ChatKit SDK already formats SSE correctly
- Re-parsing and re-encoding adds latency
- Reduces risk of corrupting streaming data

**Alternatives Considered**:
- **Option A**: Parse SSE, extract JSON, re-encode
  - **Rejected**: Unnecessary overhead
  - **Reason**: SSE format is already correct

- **Option B**: Use different streaming protocol (WebSockets)
  - **Rejected**: Spec requires SSE (ChatKit standard)
  - **Reason**: Frontend expects Server-Sent Events

**Selected**: **Direct passthrough**
  - **Pro**: Zero latency overhead
  - **Pro**: No risk of data corruption
  - **Con**: None identified

---

## Technology Decisions Summary

| Decision | Choice | Rationale | Alternatives Rejected |
|----------|--------|-----------|----------------------|
| Protocol Translation | REST → JSON-RPC wrapper | Spec requires REST, SDK requires JSON-RPC | Rewrite SDK, change spec, use different SDK |
| Session Management | On-demand creation | RESTful resource semantics | Lazy creation, login-time creation |
| Dual Entry Points | Maintain both REST + JSON-RPC | Support tests/frontend + web component | Single protocol, different URL paths |
| Database Schema | Reuse `conversation` table | Zero schema changes, single data model | New table, add discriminator column |
| Error Handling | Semantic HTTP status codes | REST client best practices | Generic 500, expose stack traces |
| Translation Pattern | Per-endpoint functions | Type safety, explicit | Middleware, generic translation |
| Streaming | Byte-for-byte passthrough | Zero latency, no corruption risk | Re-parse and re-encode, WebSockets |

---

## Unknowns Resolved

All "NEEDS CLARIFICATION" items from Technical Context resolved:

- ✅ **ChatKit SDK Protocol**: JSON-RPC (documented)
- ✅ **Session Creation Pattern**: On-demand with database persistence (documented)
- ✅ **Dual Entry Point Feasibility**: Supported via FastAPI route priority (documented)
- ✅ **Database Schema Requirements**: Reuse existing tables (documented)
- ✅ **Error Handling Strategy**: HTTP status code mapping (documented)
- ✅ **Translation Complexity**: Per-endpoint functions pattern (documented)
- ✅ **Streaming Compatibility**: Direct passthrough supported (documented)

---

## Implementation Risks & Mitigations

### High Risk

**JSON-RPC Payload Construction**:
- **Risk**: Incorrect TypeAdapter usage → ChatKit SDK crashes
- **Mitigation**: Unit tests for each request type, reference ChatKit SDK tests
- **Acceptance**: If translation fails, error logged with full payload for debugging

### Medium Risk

**Session Count Query Performance**:
- **Risk**: `COUNT(*)` query slow for users with many sessions
- **Mitigation**: Index on `user_id`, limit enforced at 10 (small count)
- **Fallback**: Cache session count (future optimization if needed)

### Low Risk

**Streaming Response Corruption**:
- **Risk**: Bytes not properly decoded
- **Mitigation**: Test SSE format with E2E tests, log streaming errors
- **Fallback**: Detailed error message to user, log full event sequence

---

## Next Steps (Post-Research)

1. ✅ **Phase 0 Complete**: research.md created
2. **Phase 1 Next**: Generate `data-model.md`
3. **Phase 1 Next**: Generate `contracts/` OpenAPI schemas
4. **Phase 1 Next**: Generate `quickstart.md` developer guide
5. **Phase 2**: Run `/sp.tasks` to break plan into atomic tasks
6. **Implementation**: Deploy backend-builder agent with research context

---

## References

- `specs/reports/phase3-http500-root-cause-analysis.md` - Root cause investigation
- `specs/research/phase3-ai-integration-stack.md` - ChatKit SDK analysis
- `phase-3-chatbot/backend/tests/test_openrouter_connection.py` - Test requirements
- `phase-3-chatbot/backend/app/chatkit/server.py` - ChatKit SDK integration
- ChatKit SDK documentation (inferred from source code)
- FastAPI documentation (routing, dependencies, streaming)

---

**Research Status**: ✅ **COMPLETE**
**Unknowns Remaining**: 0
**Decisions Documented**: 7
**Next Phase**: data-model.md generation
