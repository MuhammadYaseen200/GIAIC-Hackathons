# Feature Specification: OpenRouter API Integration

**Feature Branch**: `004-phase3-chatbot`
**Created**: 2026-01-22
**Status**: Draft - Pending Approval
**Phase**: Phase III - AI Chatbot (Maintenance)
**Author**: @lead-architect
**Priority**: P0 (Blocking - Current Gemini API rate-limited)

---

## 1. Purpose & Context

- **What**: Migrate the AI backend from direct Gemini API to OpenRouter, an OpenAI-compatible API aggregator that provides access to multiple models including free-tier options
- **Why**: The current Gemini API integration is hitting rate limits (HTTP 429 errors), blocking chat functionality. OpenRouter provides higher rate limits on free models and serves as an abstraction layer for future model flexibility
- **Where**: Backend only - `phase-3-chatbot/backend/app/chatkit/server.py` and `phase-3-chatbot/backend/app/core/config.py`

### Problem Statement

The Phase 3 AI Chatbot is functionally complete but operationally blocked:

```
ERROR: Gemini API returned 429 Too Many Requests
```

This specification defines the migration path to OpenRouter to unblock chat functionality.

---

## 2. Constraints

### MUST Requirements

- **MUST** use OpenRouter's OpenAI-compatible API endpoint
- **MUST** maintain compatibility with existing ChatKit frontend (no UI changes)
- **MUST** preserve all MCP tool schemas and handlers (no tool changes)
- **MUST** continue using SSE streaming for responses
- **MUST** secure API key in `.env` (never commit to git)

### MUST NOT Requirements

- **MUST NOT** change the ChatKit frontend implementation
- **MUST NOT** modify MCP tool definitions or handlers
- **MUST NOT** alter the response format to the frontend
- **MUST NOT** commit API keys to version control

### Performance Requirements

| Metric | Requirement | Rationale |
|--------|-------------|-----------|
| Response latency | < 3 seconds | Match or improve current Gemini latency |
| Streaming support | Required | ChatKit expects SSE streams |
| Rate limit | > 30 req/min | Must exceed current Gemini limit |

---

## 3. Technical Specification

### 3.1 OpenRouter API Configuration

**Endpoint**: `https://openrouter.ai/api/v1`

**Required Headers**:
```
Authorization: Bearer ${OPENROUTER_API_KEY}
HTTP-Referer: ${APP_URL}  # Optional but recommended
X-Title: Evolution of Todo  # Optional but recommended
```

**Recommended Models** (Free Tier):
| Model ID | Context | Speed | Tool Support |
|----------|---------|-------|--------------|
| `google/gemini-2.0-flash-exp:free` | 1M tokens | Fast | Yes |
| `meta-llama/llama-3.3-70b-instruct:free` | 128K | Fast | Yes |
| `deepseek/deepseek-chat-v3-0324:free` | 64K | Medium | Yes |

**Default Model**: `google/gemini-2.0-flash-exp:free`

### 3.2 Configuration Changes

**File**: `backend/app/core/config.py`

**New Settings**:
```python
# OpenRouter Configuration (replaces direct Gemini)
OPENROUTER_API_KEY: str = Field(default="")
OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1")
OPENROUTER_MODEL: str = Field(default="google/gemini-2.0-flash-exp:free")

# Deprecated but kept for backward compatibility
GEMINI_API_KEY: str = Field(default="")  # Deprecated
GEMINI_MODEL: str = Field(default="gemini-2.0-flash")  # Deprecated
```

### 3.3 Client Initialization Changes

**File**: `backend/app/chatkit/server.py`

**Current Implementation** (to be replaced):
```python
gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)
```

**New Implementation**:
```python
openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": "https://evolution-of-todo.vercel.app",
        "X-Title": "Evolution of Todo",
    },
)
```

### 3.4 Model Call Changes

**Current** (line 229-235 in server.py):
```python
response = await gemini_client.chat.completions.create(
    model=settings.GEMINI_MODEL,
    messages=messages,
    tools=TOOL_SCHEMAS,
    timeout=settings.AGENT_TIMEOUT_SECONDS,
    stream=True,
)
```

**New**:
```python
response = await openrouter_client.chat.completions.create(
    model=settings.OPENROUTER_MODEL,
    messages=messages,
    tools=TOOL_SCHEMAS,
    timeout=settings.AGENT_TIMEOUT_SECONDS,
    stream=True,
)
```

---

## 4. Environment Configuration

### 4.1 Required Environment Variables

**Add to `.env`**:
```bash
# OpenRouter Configuration (Phase 3 AI Backend)
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXXXXXXXXXXXXXXXXXXXXXX
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free
```

### 4.2 Update `.env.example`

**Add**:
```bash
# Phase 3: AI Configuration (OpenRouter)
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Deprecated: Direct Gemini API (replaced by OpenRouter)
# GEMINI_API_KEY=deprecated_use_openrouter
# GEMINI_MODEL=gemini-2.0-flash
```

---

## 5. Security Requirements

### 5.1 API Key Management

| Requirement | Implementation |
|-------------|----------------|
| Key storage | `.env` file only (gitignored) |
| Key rotation | Rotate if exposed in logs/commits |
| Key scope | Backend only (never expose to frontend) |
| Verification | Check key existence on startup |

### 5.2 Security Checklist

- [ ] API key added to `.gitignore` patterns
- [ ] Key not present in any committed files
- [ ] Key validated on application startup
- [ ] Failed auth results in graceful error (no key exposure)

---

## 6. Testing Requirements

### 6.1 Unit Tests

| Test Case | Expected Result |
|-----------|-----------------|
| Config loads with OPENROUTER_API_KEY | Settings object has key |
| Config loads without key | Empty string default |
| Client initialization | No exceptions |

### 6.2 Integration Tests

| Test Case | Expected Result |
|-----------|-----------------|
| Simple chat message | Response received |
| Tool call (add_task) | Task created successfully |
| Streaming response | SSE chunks received |
| Rate limit handling | Graceful error message |

### 6.3 CRUD Matrix Verification

All existing MCP tools must continue to work:

| Tool | Test Command | Expected Result |
|------|--------------|-----------------|
| `add_task` | "Add task Buy milk" | Task created |
| `list_tasks` | "Show my tasks" | Tasks listed |
| `complete_task` | "Complete Buy milk" | Task marked done |
| `delete_task` | "Delete Buy milk" | Task removed |
| `update_task` | "Rename task to..." | Task updated |

---

## 7. Rollback Plan

If OpenRouter integration fails:

1. Revert `server.py` changes
2. Revert `config.py` changes
3. Restore `.env` with original GEMINI_API_KEY
4. Test Gemini API (may still be rate-limited)

**Alternative Fallback**: Use a different free model on OpenRouter:
```python
OPENROUTER_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
```

---

## 8. Files to Modify

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/core/config.py` | Modify | Add OPENROUTER_* settings |
| `backend/app/chatkit/server.py` | Modify | Update client initialization and model calls |
| `backend/.env` | Modify | Add OPENROUTER_API_KEY |
| `backend/.env.example` | Modify | Document new variables |

**Files NOT Modified**:
- Frontend components (no changes)
- MCP tool definitions (no changes)
- ChatKit store (no changes)
- API routes (no changes)

---

## 9. Implementation Tasks

### T-401: Update Config with OpenRouter Settings [P1]

**Description**: Add OpenRouter configuration to Settings class
**Files**: `backend/app/core/config.py`
**Dependencies**: None
**Verification**: `uv run python -c "from app.core.config import settings; print(settings.OPENROUTER_BASE_URL)"`

### T-402: Secure OpenRouter API Key in .env [P1]

**Description**: Add OPENROUTER_API_KEY to .env file (not committed)
**Files**: `backend/.env`
**Dependencies**: None
**Verification**: Key exists in .env, not in any git-tracked file

### T-403: Update .env.example with OpenRouter Variables [P2]

**Description**: Document new environment variables
**Files**: `backend/.env.example`
**Dependencies**: T-401
**Verification**: .env.example shows all OpenRouter variables

### T-404: Migrate Client Initialization to OpenRouter [P1]

**Description**: Replace Gemini client with OpenRouter client
**Files**: `backend/app/chatkit/server.py`
**Dependencies**: T-401, T-402
**Verification**: Server starts without errors

### T-405: Update Model Reference in Chat Completions [P1]

**Description**: Use OPENROUTER_MODEL instead of GEMINI_MODEL
**Files**: `backend/app/chatkit/server.py`
**Dependencies**: T-404
**Verification**: Chat completions call uses correct model

### T-406: Test OpenRouter Connection [P1]

**Description**: Verify OpenRouter API responds correctly
**Files**: None (manual test)
**Dependencies**: T-405
**Verification**: Simple chat message returns response

### T-407: Run CRUD Matrix Tests [P1]

**Description**: Verify all MCP tools work through OpenRouter
**Files**: Test scripts
**Dependencies**: T-406
**Verification**: All 5 core tools execute successfully

### T-408: Create ADR-013 for Provider Migration [P2]

**Description**: Document the decision to switch from Gemini to OpenRouter
**Files**: `history/adr/ADR-013-openrouter-migration.md`
**Dependencies**: T-407
**Verification**: ADR follows template

---

## 10. Success Criteria

### Functional Criteria

- [ ] Chat messages receive AI responses
- [ ] Streaming responses work correctly
- [ ] All MCP tools execute without error
- [ ] No 429 rate limit errors during normal use

### Non-Functional Criteria

- [ ] Response latency < 3 seconds
- [ ] API key secured in .env only
- [ ] No breaking changes to frontend

### Documentation Criteria

- [ ] ADR-013 created
- [ ] .env.example updated
- [ ] CLAUDE.md updated if needed

---

## 11. Acceptance Criteria

**AC-OR-01**: Given a user sends a chat message, when the backend calls OpenRouter API, then a valid response is returned without rate limiting errors.

**AC-OR-02**: Given the chat includes a tool call (e.g., "Add task Buy milk"), when the AI processes the request, then the MCP tool executes successfully and the task is created.

**AC-OR-03**: Given the OpenRouter API key is missing, when the server starts, then a clear error message is logged (not a crash).

**AC-OR-04**: Given the response is streaming, when the AI generates text, then the ChatKit frontend receives SSE chunks correctly.

---

## 12. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenRouter free tier rate limits | Low | Medium | Use paid tier or alternative model |
| Model tool-calling differences | Low | High | Test all tools before deployment |
| API key exposure | Medium | Critical | Strict .env-only storage |
| Streaming format incompatibility | Low | Medium | OpenRouter uses OpenAI format |

---

## Approval

**Specification Status**: Draft - Awaiting Approval

- [x] Purpose clearly defined
- [x] Technical changes documented
- [x] Security requirements specified
- [x] Testing requirements defined
- [x] Rollback plan documented
- [x] Tasks broken into atomic units

**Approval Required From**:
- [ ] @lead-architect (this spec author)
- [ ] @qa-overseer (testing verification)

---

**Version**: 1.0.0 | **Author**: @lead-architect | **Date**: 2026-01-22
