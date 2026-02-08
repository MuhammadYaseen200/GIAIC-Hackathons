# QuickStart: ChatKit REST Wrapper

**For**: Backend developers implementing or debugging the REST wrapper layer
**Complexity**: High (JSON-RPC translation logic)
**Time**: 30 minutes to understand, 8-12 hours to implement

---

## Prerequisites

- Python 3.13+ installed
- UV package manager configured
- PostgreSQL database (Neon Serverless) accessible
- OpenRouter API key (in `.env`)
- Existing Phase 3 backend running

---

## Understanding the Architecture

### The Problem

```
Test Expectation:     POST /chatkit/sessions (empty body)
ChatKit SDK Reality:  {"type": "threads.create", "params": {...}} (JSON-RPC)
Result:              HTTP 500 - ValidationError: EOF while parsing
```

### The Solution

```
Client (REST) → chatkit_rest.py (Translation) → ChatKitServer.process() (JSON-RPC) → OpenRouter API
```

### Dual Entry Points

- **REST**: `/api/v1/chatkit/sessions` → Tests/Frontend
- **JSON-RPC**: `/api/v1/chatkit/*` (catch-all) → Web Component

Both coexist without conflict (FastAPI route priority).

---

## Testing the REST Endpoints

### 1. Start Backend

```bash
cd phase-3-chatbot/backend
uv run uvicorn app.main:app --reload --port 8000
```

### 2. Register User & Login

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","username":"testuser"}'

# Login (save token)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}' \
  | jq -r '.data.token')

echo "Token: $TOKEN"
```

### 3. Create Session

```bash
curl -X POST http://localhost:8000/api/v1/chatkit/sessions \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

**Expected Response**:
```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "created_at": "2026-02-01T12:00:00Z"
  }
}
```

### 4. Create Thread

```bash
SESSION_ID="550e8400-e29b-41d4-a716-446655440000"

curl -X POST "http://localhost:8000/api/v1/chatkit/sessions/$SESSION_ID/threads" \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

### 5. Send Message (Streaming)

```bash
THREAD_ID="$SESSION_ID"  # Thread ID = Session ID

curl -X POST "http://localhost:8000/api/v1/chatkit/sessions/$SESSION_ID/threads/$THREAD_ID/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "content": [{"type": "input_text", "text": "Add task: Buy milk"}]
    }
  }' \
  --no-buffer
```

**Expected Output** (SSE stream):
```
data: {"type": "response.chunk", "content": "I'll"}

data: {"type": "response.chunk", "content": " add"}

data: {"type": "response.done", "finish_reason": "stop"}
```

### 6. List Sessions

```bash
curl -X GET http://localhost:8000/api/v1/chatkit/sessions \
  -H "Authorization: Bearer $TOKEN" \
  | jq
```

---

## Debugging Translation Errors

### Enable Debug Logging

```python
# chatkit_rest.py
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Before translation
logger.debug(f"REST Request: {request.method} {request.url}")
logger.debug(f"Body: {await request.body()}")

# After translation
logger.debug(f"JSON-RPC Payload: {jsonrpc_payload}")
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ValidationError: EOF while parsing` | Empty body sent to ChatKit SDK | Provide default JSON-RPC payload |
| `KeyError: 'id'` | Response doesn't contain session ID | Check ChatKitServer.process() return value |
| `403 Forbidden` | User doesn't own session | Add `WHERE user_id = :current_user_id` to query |
| `502 Bad Gateway` | OpenRouter API failure | Check OPENROUTER_API_KEY in .env |

---

## Adding New Endpoints

### Step 1: Define Pydantic Model

```python
# chatkit_rest.py
class NewEndpointRequest(BaseModel):
    field: str
    model_config = ConfigDict(strict=True)
```

### Step 2: Create Route

```python
@router.post("/new-endpoint")
async def new_endpoint(
    request_body: NewEndpointRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    # Translate to JSON-RPC
    jsonrpc_payload = {
        "type": "new_operation",
        "params": {"field": request_body.field}
    }

    # Delegate to ChatKitServer
    context = ChatContext(user_id=current_user.id, db=db)
    result = await server.process(json.dumps(jsonrpc_payload).encode(), context)

    # Format response
    return {"success": True, "data": result}
```

### Step 3: Add to Router

```python
# v1/router.py
from .chatkit_rest import router as chatkit_rest_router
api_router.include_router(chatkit_rest_router, prefix="/chatkit", tags=["ChatKit REST"])
```

---

## Running Tests

```bash
# Unit tests (fast)
cd phase-3-chatbot/backend
uv run pytest tests/test_chatkit_rest.py -v

# Integration tests (with database)
uv run pytest tests/test_chatkit_integration.py -v

# E2E tests (with OpenRouter API)
uv run pytest tests/test_openrouter_connection.py -v
```

---

## Performance Monitoring

### Key Metrics

- Session creation latency (target: <500ms)
- Thread creation latency (target: <200ms)
- First token latency (target: <2s)
- OpenRouter API error rate (alert: >5%)

### Logging Strategy

- **DEBUG**: Translation payloads, query results
- **INFO**: Request/response times, session creation
- **ERROR**: OpenRouter failures, validation errors, exceptions

---

## Rollback Plan

If implementation fails:

```bash
# 1. Tag current state
git tag pre-rest-wrapper

# 2. Delete new file
rm app/api/v1/chatkit_rest.py

# 3. Revert router changes
git checkout app/api/v1/router.py

# 4. Document failure in PHR
```

---

## Next Steps

1. Read `spec.md` (requirements)
2. Read `plan.md` (architecture)
3. Read `data-model.md` (database models)
4. Review `contracts/*.yaml` (OpenAPI schemas)
5. Implement `chatkit_rest.py` (translation layer)
6. Write unit tests
7. Run E2E tests
8. Create ADR-015 (document decision)

---

**Status**: ✅ **PLANNING COMPLETE** - Ready for `/sp.tasks`
