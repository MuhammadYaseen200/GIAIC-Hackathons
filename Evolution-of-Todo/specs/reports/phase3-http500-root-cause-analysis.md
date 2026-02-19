# Phase 3 HTTP 500 Root Cause Analysis

**Date**: 2026-02-01
**Branch**: `004-phase3-chatbot`
**Blocker**: HTTP 500 session creation error
**Analyst**: modular-ai-architect agent

---

## Executive Summary

**Problem**: Test expects REST API (`POST /chatkit/sessions`), but ChatKit SDK expects JSON-RPC protocol with structured payloads.

**Root Cause**: **Protocol Mismatch** - We built a REST API wrapper around a JSON-RPC SDK.

**Impact**: Phase 3 blocked at 31% completion, all E2E tests failing.

**Recommendation**: **Option B - Build REST Wrapper Layer** (architectural fix required)

---

## 1. Evidence Analysis

### Test Expectation (REST API)

**File**: `phase-3-chatbot/backend/tests/test_openrouter_connection.py:59-62`

```python
# Test expects REST endpoints:
session_response = await client.post(
    f"{BASE_URL}/chatkit/sessions",
    headers={"Authorization": f"Bearer {token}"}
    # NO request body - expects server to auto-create session
)
```

**Expected Behavior**:
- REST endpoint auto-generates session ID
- Returns JSON: `{"id": "session_xxx", "created_at": "..."}`
- Client uses session ID for subsequent requests

---

### Current Implementation (JSON-RPC Pass-Through)

**File**: `phase-3-chatbot/backend/app/api/v1/chatkit.py:191-195`

```python
# Catch-all handler passes raw body to ChatKit SDK:
body = await request.body()  # Returns b'' for empty POST
result = await server.process(body, context)  # Fails validation
```

**ChatKit SDK Expectation**:

**File**: `chatkit/server.py:389`

```python
async def process(self, request: str | bytes | bytearray, context: TContext):
    """Parse an incoming ChatKit request and route it to handlers."""
    parsed_request = TypeAdapter[ChatKitReq](ChatKitReq).validate_json(request)
    # ^^ Fails: Invalid JSON: EOF while parsing (empty body)
```

**Required Payload** (JSON-RPC format):

```json
{
  "type": "threads.create",
  "params": {
    "input": {
      "content": [
        {"type": "input_text", "text": "Hello"}
      ]
    }
  },
  "metadata": {}
}
```

---

### The Mismatch

| Layer | Expected Protocol | Actual Implementation |
|-------|-------------------|----------------------|
| **Test** | REST (`POST /sessions` with empty body) | Sends empty body |
| **API Handler** | Pass-through (agnostic) | Forwards raw body |
| **ChatKit SDK** | JSON-RPC with `type` + `params` | Expects structured JSON |

**Result**: `ValidationError: EOF while parsing` → HTTP 500

---

## 2. Architecture Analysis

### ChatKit SDK Protocol (JSON-RPC)

**Discovery**: ChatKit SDK is NOT a REST API. It's a **JSON-RPC server** that expects all requests to follow this contract:

**Request Structure**:
```typescript
interface ChatKitReq {
  type: "threads.create"
      | "threads.list"
      | "threads.get_by_id"
      | "threads.add_user_message"
      | "threads.add_client_tool_output"
      | "items.list"
      | "items.feedback"
      | "attachments.create"
      | "attachments.delete"
      // ... more operations

  params: {
    // Operation-specific parameters
    // e.g., for threads.create: { input: { content: [...] } }
  }

  metadata?: Record<string, any>
}
```

**Routing Logic**:

**File**: `chatkit/server.py:399-424`

```python
async def _process_non_streaming(self, request: NonStreamingReq, context: TContext):
    match request:
        case ThreadsGetByIdReq():
            # Handle GET thread by ID
        case ThreadsListReq():
            # Handle LIST threads
        case ThreadsCreateReq():
            # Handle CREATE thread (streaming)
        case ItemsFeedbackReq():
            # Handle feedback
        # ... more cases
```

**Key Insight**: ChatKit SDK uses **pattern matching on `request.type`** to route operations. It does NOT use HTTP method/path routing.

---

### Current Architecture (Incorrect)

```
Frontend Test
    |
    | POST /chatkit/sessions (empty body)
    v
FastAPI Handler (chatkit.py:191-195)
    |
    | await request.body()  # b''
    v
ChatKitServer.process(b'', context)
    |
    | TypeAdapter[ChatKitReq].validate_json(b'')
    v
❌ ValidationError: EOF while parsing
```

**Why This Fails**:
1. Test expects REST endpoint to handle empty body
2. ChatKit SDK expects JSON-RPC payload with `type` field
3. No translation layer exists

---

## 3. Root Cause Classification

**Category**: **Architectural Mismatch**

**Specific Issue**: **Protocol Impedance**

We attempted to use a **JSON-RPC SDK** as if it were a **REST API library**.

**Analogy**: Like trying to use a GraphQL client to handle REST endpoints - the protocols are fundamentally incompatible.

---

## 4. Why Did This Happen?

### Violated Process Rules

**From AGENTS.md**:

> ❌ **DON'T** skip clarification when encountering unknowns
> - SDK mysteries are blockers, not optional research

**What Should Have Happened**:

1. **Encounter ChatKit SDK** (new, undocumented)
2. **STOP and run `/sp.clarify`** (MANDATORY for unknowns)
3. **Create research doc**: `specs/research/chatkit-protocol.md`
4. **Discover JSON-RPC protocol** (via SDK inspection)
5. **Design architecture**: REST wrapper OR direct JSON-RPC
6. **Document decision in ADR**

**What Actually Happened**:

1. Encounter ChatKit SDK
2. ~~Skip `/sp.clarify`~~ (VIOLATION)
3. Assume SDK is REST-compatible
4. Build pass-through handler
5. Implement tests expecting REST API
6. **34-day overrun** fixing protocol mismatch

**Lesson**: Phase 3 retrospective identifies this as **primary failure mode**.

---

## 5. Solution Options

### Option A: Fix Test to Use JSON-RPC (Band-Aid)

**Change test to send JSON-RPC payload**:

```python
# Instead of:
session_response = await client.post(
    f"{BASE_URL}/chatkit/sessions",
    headers={"Authorization": f"Bearer {token}"}
)

# Use:
session_response = await client.post(
    f"{BASE_URL}/chatkit",  # Single endpoint
    headers={"Authorization": f"Bearer {token}"},
    json={
        "type": "threads.create",
        "params": {
            "input": {
                "content": [{"type": "input_text", "text": "Start session"}]
            }
        }
    }
)
```

**Pros**:
- Minimal code changes
- Uses ChatKit SDK as designed

**Cons**:
- Frontend must construct JSON-RPC payloads (complex)
- Violates REST conventions (confusing for developers)
- Spec requires REST API (`/sessions`, `/threads`)
- Test already written expecting REST

**Verdict**: ❌ **Violates spec requirements**

---

### Option B: Build REST Wrapper Layer (Correct Architecture)

**Create REST endpoints that translate to JSON-RPC**:

```python
# New REST endpoints (chatkit_rest.py)

@router.post("/sessions")
async def create_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Create ChatKit session (REST endpoint)."""
    context = ChatContext(user_id=current_user.id, db=db)

    # Translate REST request to JSON-RPC
    chatkit_request = {
        "type": "threads.create",
        "params": {
            "input": {
                "content": [
                    {"type": "input_text", "text": "Session started"}
                ]
            }
        }
    }

    # Call ChatKit SDK
    result = await server.process(
        json.dumps(chatkit_request).encode(),
        context
    )

    # Extract session ID from response
    response_data = json.loads(result.json)
    return {"id": response_data["id"], "created_at": response_data["created_at"]}


@router.post("/sessions/{session_id}/threads")
async def create_thread(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Create thread in session (REST endpoint)."""
    context = ChatContext(user_id=current_user.id, db=db)

    # Translate to JSON-RPC
    chatkit_request = {
        "type": "threads.add_user_message",
        "params": {
            "thread_id": session_id,
            "input": {
                "content": [
                    {"type": "input_text", "text": "Thread started"}
                ]
            }
        }
    }

    result = await server.process(
        json.dumps(chatkit_request).encode(),
        context
    )

    response_data = json.loads(result.json)
    return {"id": response_data["thread_id"]}


@router.post("/sessions/{session_id}/threads/{thread_id}/runs")
async def create_run(
    session_id: str,
    thread_id: str,
    message: UserMessageInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """Send message and get AI response (streaming)."""
    context = ChatContext(user_id=current_user.id, db=db)

    # Translate to JSON-RPC
    chatkit_request = {
        "type": "threads.add_user_message",
        "params": {
            "thread_id": thread_id,
            "input": message.model_dump()
        }
    }

    result = await server.process(
        json.dumps(chatkit_request).encode(),
        context
    )

    # Return streaming response
    return StreamingResponse(
        result,
        media_type="text/event-stream"
    )
```

**Architecture**:

```
Frontend Test
    |
    | POST /chatkit/sessions (empty body)
    v
REST Wrapper Layer (NEW)
    |
    | Translate: REST → JSON-RPC
    | Construct: {"type": "threads.create", "params": {...}}
    v
ChatKitServer.process(json_rpc_payload, context)
    |
    | TypeAdapter[ChatKitReq].validate_json(json_rpc_payload)
    v
✅ Success: Route to threads.create handler
```

**Pros**:
- Complies with spec (REST API)
- Tests work without changes
- Frontend uses simple REST calls
- ChatKit SDK used correctly
- Separation of concerns (REST ↔ JSON-RPC)

**Cons**:
- Additional translation layer (complexity)
- Duplicate endpoint definitions (REST + JSON-RPC)
- Must maintain mapping logic

**Verdict**: ✅ **RECOMMENDED** (correct architectural fix)

---

### Option C: Redesign Spec to Use JSON-RPC (Nuclear)

**Change spec to require JSON-RPC frontend**:

**Spec Update**:
```typescript
// Frontend must send:
POST /chatkit
Content-Type: application/json

{
  "type": "threads.create",
  "params": { "input": { "content": [...] } }
}
```

**Pros**:
- Uses ChatKit SDK as designed
- No translation layer needed

**Cons**:
- Violates spec (breaking change)
- Frontend complexity increased
- Tests must be rewritten
- Non-standard API (confusing)
- Requires user approval to change spec

**Verdict**: ❌ **Not recommended** (spec change requires user approval)

---

## 6. Recommended Solution

**Choice**: **Option B - Build REST Wrapper Layer**

### Implementation Strategy

**1. Create REST Wrapper Module**

**File**: `phase-3-chatbot/backend/app/api/v1/chatkit_rest.py`

```python
"""REST API wrapper for ChatKit JSON-RPC SDK.

This module provides RESTful endpoints that translate to ChatKit's
JSON-RPC protocol internally, allowing the frontend to use
conventional HTTP methods and paths.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.chatkit.server import TodoChatKitServer
from app.chatkit.store import ChatContext, DatabaseStore
from app.models.user import User

router = APIRouter(prefix="/chatkit", tags=["chatkit"])
store = DatabaseStore()
server = TodoChatKitServer(store)

# REST endpoints (implement as shown above)
```

**2. Update Router Registration**

**File**: `phase-3-chatbot/backend/app/api/v1/router.py`

```python
from app.api.v1 import auth, tasks, chatkit_rest

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tasks.router)
api_router.include_router(chatkit_rest.router)  # Use REST wrapper
```

**3. Keep JSON-RPC Handler for Frontend Web Component**

**File**: `phase-3-chatbot/backend/app/api/v1/chatkit.py` (existing)

```python
# Keep catch-all handler for OpenAI ChatKit web component
# (it sends JSON-RPC directly)

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def chatkit_handler(request: Request, ...):
    # Existing JSON-RPC handler (for web component usage)
    body = await request.body()
    result = await server.process(body, context)
    # ...
```

**Architecture** (Final):

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
│  (REST Wrapper)          (JSON-RPC Pass-Through)             │
│       │                         │                            │
│       └─────────┬───────────────┘                            │
│                 │                                            │
│                 ▼                                            │
│       TodoChatKitServer.process()                            │
│       (ChatKit SDK - JSON-RPC)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Benefits**:
- **Backward compatible**: Existing web component still works
- **Test compatible**: REST tests work without changes
- **Spec compliant**: Implements required REST endpoints
- **Clean separation**: Two entry points for two use cases

---

## 7. Implementation Tasks

**Priority**: **P0 - Blocker**

### Task Breakdown

**T1**: Create REST wrapper module (`chatkit_rest.py`)
- Implement `POST /chatkit/sessions` → `threads.create`
- Implement `POST /chatkit/sessions/{id}/threads` → `threads.add_user_message`
- Implement `POST /chatkit/sessions/{id}/threads/{tid}/runs` → streaming run
- Implement `GET /chatkit/sessions` → `threads.list`
- Implement `GET /chatkit/sessions/{id}` → `threads.get_by_id`
- Implement `DELETE /chatkit/sessions/{id}` → `threads.delete`

**T2**: Update router registration
- Register `chatkit_rest.router` in `api/v1/router.py`
- Update OpenAPI tags for clarity

**T3**: Update tests
- Verify REST endpoints work with existing tests
- No test changes required (already REST-based)

**T4**: Document architecture decision
- Create ADR-015: REST Wrapper for ChatKit JSON-RPC SDK
- Document protocol mismatch discovery
- Document dual-entry-point architecture

**T5**: Update README
- Document both REST and JSON-RPC endpoints
- Clarify when to use each

**Estimated Effort**: **8-12 hours** (1-2 days)

---

## 8. Missing Specifications

**Identified Gaps** (mentioned in context):

1. **ADR-013**: OpenRouter Migration
   - **Status**: Missing
   - **Need**: Document decision to use OpenRouter instead of OpenAI
   - **Impact**: No record of why/how provider was chosen

2. **ADR-014**: Custom ChatKit Server
   - **Status**: Missing
   - **Need**: Document decision to build custom ChatKit server vs using Agents SDK
   - **Impact**: No architectural justification on record

3. **specs/api/mcp-tools.md**
   - **Status**: Missing
   - **Need**: API contract for MCP tool integration
   - **Impact**: No spec for how backend exposes tools to agents

**Recommendation**: Create these after fixing HTTP 500 blocker.

---

## 9. Lessons Learned (Retrospective)

### Process Violations That Led to This

**From AGENTS.md Phase 3 Lessons**:

> ❌ **NEVER** skip `/sp.clarify` for unknowns (ChatKit, OpenRouter, K8s, etc.)

**What Happened**:
1. Encountered ChatKit SDK (unknown, undocumented)
2. Did NOT run `/sp.clarify` (VIOLATION)
3. Did NOT create `specs/research/chatkit-protocol.md`
4. Assumed SDK was REST-compatible (wrong)
5. Built pass-through handler (incorrect architecture)
6. Tests failed → 34-day overrun

**Correct Process** (Should Have Followed):

```
Encounter Unknown SDK
    ↓
STOP ✋
    ↓
Run /sp.clarify
    ↓
Research SDK protocol
    ↓
Document findings (specs/research/chatkit-protocol.md)
    ↓
Design architecture (REST wrapper vs JSON-RPC)
    ↓
Create ADR (document decision)
    ↓
Implement with tests
    ↓
✅ Success
```

### New Process Rule (Proposal)

**Add to AGENTS.md**:

> **SDK Unknown Protocol Detection Rule**:
>
> When integrating a new SDK:
> 1. Run `pip show <package>` to find source
> 2. Read `server.py` or equivalent to identify protocol
> 3. If protocol is NOT REST, STOP and create research doc
> 4. Document protocol in `specs/research/<sdk>-protocol.md`
> 5. Design translation layer if needed
> 6. Create ADR documenting architectural choice

---

## 10. Conclusion

**Root Cause**: Protocol impedance mismatch - REST test calling JSON-RPC SDK.

**Solution**: Build REST wrapper layer (`chatkit_rest.py`) to translate REST → JSON-RPC.

**Impact**: Unblocks Phase 3, enables all tests to pass.

**Timeline**: 1-2 days implementation + testing.

**Process Fix**: Never skip `/sp.clarify` for unknown SDKs (MANDATORY).

---

## Approval Required

**Question for User**:

> **Phase 3 is blocked on HTTP 500 error. Root cause identified: protocol mismatch.**
>
> **Recommended Fix**: Build REST wrapper layer (Option B - 1-2 days)
>
> **Options**:
> - **A**: Proceed with Option B (REST wrapper implementation)
> - **B**: Review alternative solutions first
> - **C**: Pause Phase 3, document as technical debt, proceed to Phase 4
>
> **What would you like to do?**

---

**Version**: 1.0.0
**Author**: modular-ai-architect
**Phase**: III - AI Chatbot
**Status**: Draft - Awaiting User Approval
