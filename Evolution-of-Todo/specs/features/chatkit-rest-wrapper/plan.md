# Implementation Plan: ChatKit REST Wrapper Layer

**Branch**: `004-phase3-chatbot` | **Date**: 2026-02-01 | **Spec**: [chatkit-rest-wrapper/spec.md](./spec.md)
**Input**: Feature specification from `/specs/features/chatkit-rest-wrapper/spec.md`

**Note**: This template is filled in by the `/sp.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

A RESTful API wrapper layer that translates conventional HTTP requests into ChatKit JSON-RPC protocol, resolving Phase 3 HTTP 500 blocker. This enables frontend/tests to use standard REST endpoints (`POST /chatkit/sessions`) while maintaining compatibility with ChatKit SDK's JSON-RPC protocol (`{"type": "threads.create", "params": {...}}`). Critical fix to unblock 5/5 E2E tests and complete Phase 3.

## Technical Context

**Language/Version**: Python 3.13+ (existing backend stack)
**Primary Dependencies**: FastAPI 0.115+, SQLModel, ChatKit SDK (openai-chatkit), Pydantic v2
**Storage**: PostgreSQL (Neon Serverless) - reuses existing `conversation`, `message` tables
**Testing**: pytest (unit), pytest-asyncio (integration), Playwright (E2E)
**Target Platform**: Linux server (Vercel/cloud deployment)
**Project Type**: Web backend (REST API layer)
**Performance Goals**: <500ms session creation, <200ms thread creation, <2s first token streaming
**Constraints**: <200ms p95 latency, user-scoped data isolation (JWT), no session caching
**Scale/Scope**: 10 active sessions per user, 100 messages per session, 30 req/min rate limit

**Integration Points**:
- Reuses Phase 2 JWT authentication (`get_current_user` dependency)
- Integrates with existing ChatKitServer.process() method (JSON-RPC handler)
- Uses existing ChatContext (user_id, db session)
- OpenRouter integration already functional
- Coexists with ChatKit web component endpoint (dual entry points)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Spec-Driven Development
- **Status**: PASS
- **Evidence**: spec.md exists at `specs/features/chatkit-rest-wrapper/spec.md`
- **Traceability**: All endpoints map to REQ-001 through REQ-006
- **Task Linkage**: Will reference spec sections in tasks.md

### ✅ Principle II: Iterative Evolution (Brownfield Protocol)
- **Status**: PASS
- **Evidence**: Extends existing Phase 3 backend, no new projects
- **Integration**: Reuses JWT auth, database models, ChatKitServer
- **Backward Compatibility**: Maintains JSON-RPC endpoint for web component

### ✅ Principle III: Test-First Mindset
- **Status**: PASS
- **Evidence**: Fixing blocker in `test_openrouter_connection.py` (existing E2E tests)
- **Coverage Requirements**: 13 unit tests + 3 integration tests defined in spec
- **Acceptance Criteria**: 50+ testable conditions in spec.md (AC-001 to AC-008)

### ✅ Principle IV: Smallest Viable Diff
- **Status**: PASS
- **Evidence**: Single new file (`chatkit_rest.py`), no refactoring existing code
- **Scope Constraint**: REST wrapper ONLY, no ChatKitServer modifications
- **Technical Debt**: Accepts 7 limitations (no caching, pagination, etc.)

### ✅ Principle V: Intelligence Capture
- **Status**: PASS (with actions)
- **ADR Required**: ADR-015 (REST Wrapper for ChatKit JSON-RPC SDK)
- **PHR Required**: After implementation session
- **Skills Candidate**: "REST-to-JSON-RPC translation pattern" (reusable)

### ✅ Principle VI: AAIF Standards & Interoperability
- **Status**: PASS
- **MCP Usage**: `filesystem`, `postgres`, `code-search` for implementation
- **Agent Orchestration**: backend-builder (implement), qa-overseer (certify)
- **Goose Compatibility**: FastAPI + SQLModel patterns (Goose-compatible)

### ✅ Principle VII: Mandatory Clarification Gate
- **Status**: PASS
- **Evidence**: ChatKit SDK protocol researched in `specs/reports/phase3-http500-root-cause-analysis.md`
- **Unknowns Resolved**: JSON-RPC vs REST architecture clarified
- **No NEEDS CLARIFICATION**: All technical unknowns resolved

### ✅ Principle VIII: Process Failure Prevention
- **Status**: PASS
- **Environment Validation**: Phase 3 profile validated (`verify-env.py`)
- **Type Safety**: Pydantic strict mode enforced in all models
- **Error Logging**: Comprehensive logging strategy defined (DEBUG/INFO/ERROR)
- **Working Directory**: Validated at `E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo`

**GATE RESULT**: ✅ **ALL CHECKS PASS** - Proceed to Phase 0

---

## Project Structure

### Documentation (this feature)

```text
specs/features/chatkit-rest-wrapper/
├── spec.md              # Feature specification (COMPLETED)
├── plan.md              # This file (IN PROGRESS)
├── research.md          # Phase 0 output (NEXT)
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI schemas)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
phase-3-chatbot/backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── chatkit.py         # EXISTING - JSON-RPC handler (no changes)
│   │       └── chatkit_rest.py    # NEW - REST wrapper layer
│   ├── chatkit/
│   │   ├── server.py              # EXISTING - ChatKitServer (no changes)
│   │   └── store.py               # EXISTING - Database store (no changes)
│   ├── models/
│   │   └── conversation.py        # EXISTING - May need extensions
│   └── core/
│       ├── config.py              # EXISTING - No changes
│       └── database.py            # EXISTING - No changes
└── tests/
    ├── test_chatkit_rest.py       # NEW - REST endpoint unit tests
    ├── test_chatkit_integration.py # NEW - Integration tests
    └── test_openrouter_connection.py # EXISTING - Should pass after fix
```

**Structure Decision**:
- **Web backend** structure (Option 2 from template)
- Single new file: `app/api/v1/chatkit_rest.py` (REST wrapper)
- No refactoring of existing ChatKit implementation
- Maintains dual entry points:
  - `/api/v1/chatkit/*` → JSON-RPC (web component)
  - `/api/v1/chatkit/sessions`, `/api/v1/chatkit/sessions/*/threads` → REST (tests/frontend)

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**N/A** - No constitution violations detected. All principles satisfied.

---

## Phase 0: Outline & Research

### Research Tasks

**RESEARCH COMPLETE** - All unknowns resolved in:
- `specs/reports/phase3-http500-root-cause-analysis.md` (architectural analysis)
- `specs/research/phase3-ai-integration-stack.md` (ChatKit SDK protocol)

**Key Findings**:
1. **ChatKit SDK Protocol**: JSON-RPC, not REST
   - Decision: Build REST wrapper layer
   - Rationale: Spec requires REST API, SDK is JSON-RPC
   - Alternative Rejected: Rewrite tests to JSON-RPC (violates spec)

2. **Session Management Pattern**:
   - Decision: Create sessions on-demand (first message)
   - Rationale: ChatKit SDK doesn't have explicit "create session" call
   - Alternative Rejected: Pre-create empty sessions (unnecessary DB overhead)

3. **Dual Entry Point Strategy**:
   - Decision: Maintain both REST and JSON-RPC endpoints
   - Rationale: Web component needs JSON-RPC, tests need REST
   - Alternative Rejected: Single protocol (breaks one use case)

4. **Database Schema**:
   - Decision: Reuse existing `conversation`, `message` tables
   - Rationale: Schema already supports ChatKit data model
   - Alternative Rejected: New tables (violates Smallest Viable Diff)

5. **Error Handling Strategy**:
   - Decision: HTTP status codes for REST, exception propagation for JSON-RPC
   - Rationale: REST clients expect standard codes (400, 500, 502)
   - Alternative Rejected: Generic 500 for all errors (poor DX)

**Output**: research.md (NEXT STEP - consolidate findings)

---

## Phase 1: Design & Contracts

### Prerequisites
- ✅ Specification complete (`spec.md`)
- ⏳ Research complete (`research.md` - IN PROGRESS)
- ⏳ Constitution check passed

### Deliverables

1. **data-model.md** - Entity definitions:
   - Session entity (id, user_id, created_at, updated_at)
   - Thread entity (id, session_id, messages[])
   - Message entity (id, thread_id, role, content, tool_calls)
   - Validation rules from spec REQ-001 to REQ-006

2. **contracts/** - OpenAPI schemas:
   - `/contracts/sessions.yaml` - Session CRUD endpoints
   - `/contracts/threads.yaml` - Thread CRUD endpoints
   - `/contracts/runs.yaml` - Message streaming endpoint
   - Request/Response schemas with Pydantic strict mode examples

3. **quickstart.md** - Developer onboarding:
   - How to test REST endpoints (curl examples)
   - How to debug JSON-RPC translation
   - How to add new endpoints
   - How to handle ChatKit SDK errors

4. **Agent context update**:
   - Run: `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
   - Add: "ChatKit REST wrapper pattern" to CLAUDE.md skills
   - Preserve: Existing Phase 3 context

**Output**: data-model.md, contracts/, quickstart.md (PENDING Phase 0 completion)

---

## Phase 2: Implementation Strategy (High-Level)

**NOTE**: Detailed tasks will be generated by `/sp.tasks` command after Phase 1 completion.

### Component Breakdown

**Component 1: REST Request Handler** (`chatkit_rest.py`)
- FastAPI router with 6 endpoints
- JWT authentication dependency injection
- Request validation (Pydantic models)
- User-scoped data filtering

**Component 2: JSON-RPC Translator** (`chatkit_rest.py::_translate_to_jsonrpc`)
- REST → JSON-RPC payload construction
- ThreadsCreateReq, ThreadsAddUserMessageReq builders
- InferenceOptions mapping
- UserMessageInput formatting

**Component 3: Response Formatter** (`chatkit_rest.py::_format_rest_response`)
- JSON-RPC → REST JSON conversion
- SSE streaming passthrough (runs endpoint)
- Error translation (ChatKit errors → HTTP status codes)
- Success/data wrapper format

**Component 4: Session State Manager** (`chatkit_rest.py::_ensure_session`)
- Create session if not exists
- Validate user ownership
- Return session ID for thread creation
- Handle max sessions limit (10)

**Component 5: Database Integration** (uses existing `store.py`)
- No new database methods required
- Reuse: `store.load_conversation()`, `store.save_conversation()`
- Leverage: Existing CASCADE delete for threads
- Query: `SELECT * FROM conversation WHERE user_id = :user_id`

**Component 6: Error Handling** (`chatkit_rest.py::_handle_chatkit_error`)
- Map ChatKit ValidationError → HTTP 400
- Map OpenRouter errors → HTTP 502
- Map Database errors → HTTP 503
- Generic exceptions → HTTP 500 with logged details

### Sequence Diagrams

**Session Creation Flow**:
```
Client → POST /chatkit/sessions
    ↓
FastAPI → Validate JWT (get_current_user)
    ↓
chatkit_rest → Check active sessions count (<10)
    ↓
chatkit_rest → Create empty conversation in DB
    ↓
chatkit_rest → Return {id, user_id, created_at}
```

**Message Sending Flow (Complex)**:
```
Client → POST /chatkit/sessions/{id}/threads/{tid}/runs
    ↓
FastAPI → Validate JWT, extract body
    ↓
chatkit_rest → _translate_to_jsonrpc(body)
    ↓
chatkit_rest → Build ThreadsAddUserMessageReq
    ↓
ChatKitServer.process(json_rpc_payload)
    ↓
OpenRouter API → Stream response (SSE)
    ↓
chatkit_rest → Passthrough SSE events
    ↓
Client receives streamed response
```

### System Responsibilities

**chatkit_rest.py** (NEW):
- REST endpoint routing
- JWT authentication enforcement
- Request validation (Pydantic)
- REST ↔ JSON-RPC translation
- Response formatting
- Error handling
- Session state management

**chatkit.py** (EXISTING - NO CHANGES):
- JSON-RPC endpoint for web component
- Direct ChatKitServer.process() delegation
- SSE streaming passthrough
- ChatContext initialization

**server.py** (EXISTING - NO CHANGES):
- ChatKit SDK JSON-RPC protocol handling
- Tool execution (add_task, list_tasks, etc.)
- OpenRouter API integration
- Conversation persistence via store

**store.py** (EXISTING - NO CHANGES):
- Database CRUD operations
- Conversation loading/saving
- Message history management
- User-scoped queries

### Integration Points

**Authentication**: Reuse `get_current_user` from `api/deps.py`
**Database**: Reuse `get_session` from `core/database.py`
**Models**: Extend `Conversation` model if needed (likely no changes)
**ChatKit SDK**: Call `ChatKitServer.process()` with translated payloads
**OpenRouter**: No changes (already integrated in ChatKitServer)

### Testing Strategy

**Unit Tests** (`test_chatkit_rest.py`):
- Test each endpoint with mocked ChatKitServer
- Test JWT authentication rejection
- Test user-scoped data isolation
- Test request validation (Pydantic)
- Test JSON-RPC translation correctness
- Test error handling (all HTTP status codes)

**Integration Tests** (`test_chatkit_integration.py`):
- Test full flow with real database (SQLite in-memory)
- Test OpenRouter integration (mocked API)
- Test session creation → thread → message → response
- Test concurrent requests (rate limiting)
- Test max sessions enforcement

**E2E Tests** (`test_openrouter_connection.py` - EXISTING):
- Should PASS after implementation
- Tests real OpenRouter API
- Tests full stack (JWT → REST → JSON-RPC → OpenRouter → SSE)

### Success Metrics

**Performance**:
- Session creation: <500ms (target: 200ms)
- Thread creation: <200ms (target: 100ms)
- First token latency: <2s (target: 1s)

**Quality**:
- 100% type coverage (mypy strict mode)
- 100% test pass rate (13 unit + 3 integration)
- 5/5 E2E tests passing
- Zero Pydantic validation bypasses

**Technical**:
- Single file addition (chatkit_rest.py)
- No existing code modified
- Backward compatible with web component
- ADR-015 documented

---

## Phase 3: Risk Assessment

### High-Risk Areas

1. **JSON-RPC Translation Complexity**
   - **Risk**: Incorrect payload structure → ChatKit SDK errors
   - **Mitigation**: Unit tests for each request type, schema validation
   - **Fallback**: Detailed error logging to debug translation failures

2. **Session State Synchronization**
   - **Risk**: Race conditions in session creation (concurrent requests)
   - **Mitigation**: Database unique constraints on (user_id, session_id)
   - **Fallback**: Return existing session instead of failing on duplicate

3. **Streaming Response Passthrough**
   - **Risk**: SSE events corrupted during passthrough
   - **Mitigation**: Byte-for-byte forwarding, no re-encoding
   - **Fallback**: Log streaming errors, return HTTP 500 with details

4. **OpenRouter API Failures**
   - **Risk**: External API downtime → user-facing errors
   - **Mitigation**: Proper error mapping (HTTP 502), retry logic
   - **Fallback**: Detailed error messages for debugging

### Medium-Risk Areas

1. **Max Sessions Enforcement**
   - **Risk**: Count query performance degradation
   - **Mitigation**: Indexed user_id column, limit to 10 (small count)
   - **Fallback**: Cache session count (future optimization)

2. **JWT Token Expiry**
   - **Risk**: Mid-conversation token expiry → 401 errors
   - **Mitigation**: Frontend token refresh logic (out of scope)
   - **Fallback**: Clear error message to re-authenticate

### Low-Risk Areas

1. **Database Schema Changes**
   - **Risk**: N/A (reusing existing tables)
   - **Evidence**: `conversation`, `message` tables already support data model

2. **Type Safety**
   - **Risk**: N/A (Pydantic strict mode enforced)
   - **Evidence**: All models use `ConfigDict(strict=True)`

---

## Phase 4: Deployment Considerations

### Pre-Deployment Checklist

- [ ] All unit tests passing (13/13)
- [ ] All integration tests passing (3/3)
- [ ] All E2E tests passing (5/5)
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] ADR-015 created and reviewed
- [ ] README.md updated with REST endpoints
- [ ] Environment variables validated (OPENROUTER_API_KEY)
- [ ] Database migrations applied (if any)
- [ ] No dead code remaining
- [ ] qa-overseer certification complete

### Rollback Strategy

**If Implementation Fails**:
1. Delete `chatkit_rest.py`
2. Revert router changes in `v1/router.py` (if any)
3. Restore original `chatkit.py` (if modified)
4. Tag commit before implementation: `git tag pre-rest-wrapper`
5. Document failure in PHR
6. Return to spec review (re-evaluate approach)

**Partial Success Scenario**:
- If 3/6 endpoints work, deploy those only
- Feature-flag broken endpoints (return 501 Not Implemented)
- Document technical debt in ADR-015
- Plan fix in next iteration

### Production Monitoring

**Key Metrics**:
- Session creation latency (p50, p95, p99)
- Thread creation latency
- OpenRouter API error rate
- Database connection pool usage
- Active sessions per user (max 10 enforcement)

**Alerts**:
- Session creation >500ms (warning)
- Session creation >1s (critical)
- OpenRouter 5xx rate >5% (critical)
- Database connection pool exhausted (critical)

---

## Next Steps

1. **Complete Phase 0**: Generate `research.md` (consolidate findings)
2. **Execute Phase 1**: Generate `data-model.md`, `contracts/`, `quickstart.md`
3. **Run `/sp.tasks`**: Break plan into atomic tasks
4. **Deploy backend-builder agent**: Implement `chatkit_rest.py`
5. **Deploy qa-overseer agent**: Certify E2E tests passing
6. **Create ADR-015**: Document architectural decision
7. **Update README.md**: Document REST endpoints

---

**Plan Status**: ✅ **PHASE 0 & 1 READY** - Awaiting research.md generation

**Estimated Implementation Time**: 8-12 hours (1-2 days)

**Blocker Resolution Impact**: Unblocks 5/5 E2E tests, completes Phase 3 HTTP 500 fix
