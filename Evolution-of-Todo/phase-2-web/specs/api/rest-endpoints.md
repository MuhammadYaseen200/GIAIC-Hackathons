# REST API Specification: Task Management Endpoints

**Status**: Draft
**Owner**: Backend Team
**Dependencies**: Phase 1 Core CRUD (001-core-crud), Authentication Spec
**Estimated Complexity**: Medium
**Created**: 2025-12-28
**Phase**: Phase II - Full-Stack Web Application

---

## 1. Purpose & Context

- **What**: RESTful HTTP API for CRUD operations on user tasks
- **Why**: Expose Phase 1 business logic to web clients via standard HTTP interface
- **Where**: Backend service (`/api/v1/tasks/*`) consumed by Next.js frontend

---

## 2. Constraints (MANDATORY)

### NOT Supported (v1)

- Batch operations (bulk create/update/delete)
- Task sharing between users
- Task attachments or file uploads
- Nested tasks or subtasks
- Task comments
- GraphQL or WebSocket interfaces
- Sorting or filtering query parameters (Phase V scope)
- Pagination beyond simple offset/limit

### Performance Limits

- **Max Request Body Size**: 10KB
- **Max Response Time**: 500ms (p99)
- **Max Tasks Per User**: 1000 (enforced at database level)
- **Rate Limit**: 100 requests/minute per authenticated user

### Security Boundaries

- **Authentication**: Required for ALL endpoints (Bearer JWT)
- **Authorization**: Users can ONLY access their own tasks
- **Data Isolation**: All queries MUST be scoped by `user_id` from JWT claims
- **Input Validation**: All inputs sanitized and validated before processing

### Technical Debt

- No caching layer in v1 (add in Phase IV)
- No API versioning strategy beyond `/v1/` prefix
- No webhook support for real-time updates

---

## 3. Authentication Contract

### Token Transmission

All requests MUST include a valid JWT in the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

### JWT Claims (Required)

The backend extracts user identity from JWT claims:

```json
{
  "sub": "<user_id>",
  "email": "<user_email>",
  "iat": 1735344000,
  "exp": 1735430400
}
```

| Claim | Type | Description |
|-------|------|-------------|
| `sub` | `string` | Unique user identifier (UUID format) |
| `email` | `string` | User email (for logging/audit) |
| `iat` | `integer` | Issued-at timestamp (Unix epoch) |
| `exp` | `integer` | Expiration timestamp (Unix epoch) |

### Authentication Errors

| Scenario | Status Code | Error Code | Message |
|----------|-------------|------------|---------|
| Missing Authorization header | `401` | `AUTH_MISSING` | "Authorization header is required" |
| Malformed Authorization header | `401` | `AUTH_MALFORMED` | "Authorization header must be: Bearer <token>" |
| Invalid/expired token | `401` | `AUTH_INVALID` | "Invalid or expired authentication token" |
| Token signature mismatch | `401` | `AUTH_SIGNATURE` | "Token signature verification failed" |

---

## 4. Common Data Schemas

### Task Entity Schema

```typescript
interface Task {
  id: string;           // UUID v4
  user_id: string;      // UUID v4, from JWT sub claim
  title: string;        // 1-200 characters, required
  description: string;  // 0-1000 characters, optional (default: "")
  completed: boolean;   // default: false
  created_at: string;   // ISO 8601 timestamp (UTC)
  updated_at: string;   // ISO 8601 timestamp (UTC)
}
```

### Task Input Schema (Create/Update)

```typescript
interface TaskInput {
  title: string;         // Required for create, optional for update
  description?: string;  // Optional, defaults to ""
}
```

### Success Response Envelope

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;
  meta?: {
    total?: number;      // For list endpoints
    limit?: number;
    offset?: number;
  };
}
```

### Error Response Envelope

```typescript
interface ErrorResponse {
  success: false;
  error: {
    code: string;        // Machine-readable error code
    message: string;     // Human-readable message
    details?: object;    // Optional validation details
  };
}
```

---

## 5. Endpoint Specifications

---

### EP-001: List All Tasks

**Purpose**: Retrieve all tasks belonging to the authenticated user

#### Request

```
GET /api/v1/tasks
```

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |
| `Accept` | No | `application/json` (default) |

**Query Parameters**:

| Parameter | Type | Required | Default | Constraints |
|-----------|------|----------|---------|-------------|
| `limit` | integer | No | `50` | 1-100 |
| `offset` | integer | No | `0` | >= 0 |

#### Response

**200 OK** - Tasks retrieved successfully

```json
{
  "success": true,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Buy groceries",
      "description": "Milk, eggs, bread",
      "completed": false,
      "created_at": "2025-12-28T10:00:00Z",
      "updated_at": "2025-12-28T10:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Call mom",
      "description": "",
      "completed": true,
      "created_at": "2025-12-28T09:00:00Z",
      "updated_at": "2025-12-28T11:00:00Z"
    }
  ],
  "meta": {
    "total": 2,
    "limit": 50,
    "offset": 0
  }
}
```

**200 OK** - No tasks found (empty list)

```json
{
  "success": true,
  "data": [],
  "meta": {
    "total": 0,
    "limit": 50,
    "offset": 0
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**400 Bad Request** - Invalid query parameters

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid query parameters",
    "details": {
      "limit": "Must be between 1 and 100"
    }
  }
}
```

---

### EP-002: Create Task

**Purpose**: Create a new task for the authenticated user

#### Request

```
POST /api/v1/tasks
```

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |
| `Content-Type` | Yes | `application/json` |

**Request Body**:

```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | Yes | 1-200 characters, non-empty after trim |
| `description` | string | No | 0-1000 characters, default "" |

#### Response

**201 Created** - Task created successfully

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "created_at": "2025-12-28T10:00:00Z",
    "updated_at": "2025-12-28T10:00:00Z"
  }
}
```

**400 Bad Request** - Validation failed

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Title cannot be empty"
    }
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Title must not exceed 200 characters"
    }
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**413 Payload Too Large** - Request body exceeds 10KB

```json
{
  "success": false,
  "error": {
    "code": "PAYLOAD_TOO_LARGE",
    "message": "Request body must not exceed 10KB"
  }
}
```

**422 Unprocessable Entity** - Malformed JSON

```json
{
  "success": false,
  "error": {
    "code": "INVALID_JSON",
    "message": "Request body must be valid JSON"
  }
}
```

---

### EP-003: Get Task by ID

**Purpose**: Retrieve a single task by its ID

#### Request

```
GET /api/v1/tasks/{task_id}
```

**Path Parameters**:

| Parameter | Type | Required | Format |
|-----------|------|----------|--------|
| `task_id` | string | Yes | UUID v4 |

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |

#### Response

**200 OK** - Task retrieved successfully

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "created_at": "2025-12-28T10:00:00Z",
    "updated_at": "2025-12-28T10:00:00Z"
  }
}
```

**400 Bad Request** - Invalid task ID format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ID_FORMAT",
    "message": "Task ID must be a valid UUID"
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**404 Not Found** - Task does not exist or belongs to another user

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID '550e8400-e29b-41d4-a716-446655440099' not found"
  }
}
```

---

### EP-004: Update Task

**Purpose**: Update an existing task's title and/or description

#### Request

```
PUT /api/v1/tasks/{task_id}
```

**Path Parameters**:

| Parameter | Type | Required | Format |
|-----------|------|----------|--------|
| `task_id` | string | Yes | UUID v4 |

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |
| `Content-Type` | Yes | `application/json` |

**Request Body**:

```json
{
  "title": "Buy groceries and fruits",
  "description": "Milk, eggs, bread, apples"
}
```

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `title` | string | No* | 1-200 characters if provided |
| `description` | string | No | 0-1000 characters if provided |

*At least one field (`title` or `description`) MUST be provided.

#### Response

**200 OK** - Task updated successfully

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Buy groceries and fruits",
    "description": "Milk, eggs, bread, apples",
    "completed": false,
    "created_at": "2025-12-28T10:00:00Z",
    "updated_at": "2025-12-28T12:00:00Z"
  }
}
```

**400 Bad Request** - Validation failed

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "body": "At least one field (title or description) must be provided"
    }
  }
}
```

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Title cannot be empty"
    }
  }
}
```

**400 Bad Request** - Invalid task ID format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ID_FORMAT",
    "message": "Task ID must be a valid UUID"
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**404 Not Found** - Task does not exist or belongs to another user

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID '550e8400-e29b-41d4-a716-446655440099' not found"
  }
}
```

---

### EP-005: Delete Task

**Purpose**: Permanently delete a task

#### Request

```
DELETE /api/v1/tasks/{task_id}
```

**Path Parameters**:

| Parameter | Type | Required | Format |
|-----------|------|----------|--------|
| `task_id` | string | Yes | UUID v4 |

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |

#### Response

**200 OK** - Task deleted successfully

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "deleted": true
  }
}
```

**400 Bad Request** - Invalid task ID format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ID_FORMAT",
    "message": "Task ID must be a valid UUID"
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**404 Not Found** - Task does not exist or belongs to another user

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID '550e8400-e29b-41d4-a716-446655440099' not found"
  }
}
```

---

### EP-006: Toggle Task Completion

**Purpose**: Toggle the completion status of a task (pending <-> completed)

#### Request

```
PATCH /api/v1/tasks/{task_id}/complete
```

**Path Parameters**:

| Parameter | Type | Required | Format |
|-----------|------|----------|--------|
| `task_id` | string | Yes | UUID v4 |

**Headers**:

| Header | Required | Value |
|--------|----------|-------|
| `Authorization` | Yes | `Bearer <jwt_token>` |

**Request Body**: None required (toggle operation)

#### Response

**200 OK** - Task completion status toggled (was pending, now completed)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": true,
    "created_at": "2025-12-28T10:00:00Z",
    "updated_at": "2025-12-28T14:00:00Z"
  }
}
```

**200 OK** - Task completion status toggled (was completed, now pending)

```json
{
  "success": true,
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "created_at": "2025-12-28T10:00:00Z",
    "updated_at": "2025-12-28T15:00:00Z"
  }
}
```

**400 Bad Request** - Invalid task ID format

```json
{
  "success": false,
  "error": {
    "code": "INVALID_ID_FORMAT",
    "message": "Task ID must be a valid UUID"
  }
}
```

**401 Unauthorized** - Authentication failed

```json
{
  "success": false,
  "error": {
    "code": "AUTH_INVALID",
    "message": "Invalid or expired authentication token"
  }
}
```

**404 Not Found** - Task does not exist or belongs to another user

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID '550e8400-e29b-41d4-a716-446655440099' not found"
  }
}
```

---

## 6. Error Code Reference

### Authentication Errors (4xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_MISSING` | 401 | Authorization header not provided |
| `AUTH_MALFORMED` | 401 | Authorization header format invalid |
| `AUTH_INVALID` | 401 | Token invalid or expired |
| `AUTH_SIGNATURE` | 401 | Token signature verification failed |

### Validation Errors (4xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request body/params failed validation |
| `INVALID_JSON` | 422 | Request body is not valid JSON |
| `INVALID_ID_FORMAT` | 400 | Path parameter is not a valid UUID |
| `PAYLOAD_TOO_LARGE` | 413 | Request body exceeds 10KB limit |

### Resource Errors (4xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `TASK_NOT_FOUND` | 404 | Task does not exist or user lacks access |

### Server Errors (5xx)

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INTERNAL_ERROR` | 500 | Unexpected server error |
| `DATABASE_ERROR` | 503 | Database connection/query failure |

---

## 7. Field Validation Rules

### Title Field

| Rule | Constraint | Error Message |
|------|------------|---------------|
| Required (create) | Must be present | "Title is required" |
| Non-empty | After trim, length >= 1 | "Title cannot be empty" |
| Max length | length <= 200 | "Title must not exceed 200 characters" |
| Type | Must be string | "Title must be a string" |

### Description Field

| Rule | Constraint | Error Message |
|------|------------|---------------|
| Optional | Default to "" if not provided | N/A |
| Max length | length <= 1000 | "Description must not exceed 1000 characters" |
| Type | Must be string | "Description must be a string" |

### Task ID Field

| Rule | Constraint | Error Message |
|------|------------|---------------|
| Format | Valid UUID v4 | "Task ID must be a valid UUID" |
| Ownership | Must belong to authenticated user | "Task with ID '{id}' not found" |

### Query Parameters

| Parameter | Rule | Error Message |
|-----------|------|---------------|
| `limit` | Integer 1-100 | "Limit must be between 1 and 100" |
| `offset` | Integer >= 0 | "Offset must be a non-negative integer" |

---

## 8. HTTP Headers Reference

### Required Request Headers

| Endpoint | Header | Value |
|----------|--------|-------|
| All | `Authorization` | `Bearer <jwt_token>` |
| POST, PUT | `Content-Type` | `application/json` |

### Response Headers (All Endpoints)

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Response format |
| `X-Request-Id` | UUID | Request tracing identifier |
| `X-RateLimit-Limit` | 100 | Requests allowed per window |
| `X-RateLimit-Remaining` | 0-100 | Requests remaining in window |
| `X-RateLimit-Reset` | Unix timestamp | Window reset time |

---

## 9. Non-Functional Requirements

### Performance

- **Response Time**: < 500ms (p99) for all endpoints
- **Throughput**: 100 requests/user/minute
- **Database Queries**: Max 2 queries per request

### Security

- **Transport**: HTTPS only in production
- **Token Validation**: Every request validates JWT signature and expiration
- **SQL Injection**: All inputs parameterized (SQLModel handles this)
- **XSS Prevention**: JSON responses only, no HTML rendering
- **CORS**: Configured for frontend origin only

### Observability

- **Logging**: All requests logged with user_id, endpoint, status, latency
- **Tracing**: X-Request-Id propagated through all services
- **Metrics**: Request count, latency histogram, error rate by endpoint

---

## 10. Acceptance Criteria

### Authentication

- [ ] AC-AUTH-01: Request without Authorization header returns 401 with AUTH_MISSING
- [ ] AC-AUTH-02: Request with malformed header returns 401 with AUTH_MALFORMED
- [ ] AC-AUTH-03: Request with expired token returns 401 with AUTH_INVALID
- [ ] AC-AUTH-04: Request with valid token proceeds to endpoint logic

### EP-001: List Tasks

- [ ] AC-LIST-01: Returns all tasks for authenticated user
- [ ] AC-LIST-02: Returns empty array when user has no tasks
- [ ] AC-LIST-03: Tasks from other users are NOT included
- [ ] AC-LIST-04: Pagination with limit/offset works correctly
- [ ] AC-LIST-05: Invalid limit/offset returns 400

### EP-002: Create Task

- [ ] AC-CREATE-01: Valid request creates task and returns 201
- [ ] AC-CREATE-02: Task auto-assigned UUID and timestamps
- [ ] AC-CREATE-03: Task user_id matches authenticated user
- [ ] AC-CREATE-04: Empty title returns 400 with VALIDATION_ERROR
- [ ] AC-CREATE-05: Title > 200 chars returns 400 with VALIDATION_ERROR
- [ ] AC-CREATE-06: Description > 1000 chars returns 400 with VALIDATION_ERROR
- [ ] AC-CREATE-07: Missing title returns 400 with VALIDATION_ERROR

### EP-003: Get Task

- [ ] AC-GET-01: Valid task_id returns task with 200
- [ ] AC-GET-02: Invalid UUID format returns 400 with INVALID_ID_FORMAT
- [ ] AC-GET-03: Non-existent task_id returns 404 with TASK_NOT_FOUND
- [ ] AC-GET-04: Task belonging to another user returns 404 (not 403)

### EP-004: Update Task

- [ ] AC-UPDATE-01: Valid update returns modified task with 200
- [ ] AC-UPDATE-02: Only title can be updated (description unchanged)
- [ ] AC-UPDATE-03: Only description can be updated (title unchanged)
- [ ] AC-UPDATE-04: updated_at timestamp is refreshed
- [ ] AC-UPDATE-05: Empty body returns 400
- [ ] AC-UPDATE-06: Empty title string returns 400 with VALIDATION_ERROR
- [ ] AC-UPDATE-07: Non-existent task returns 404

### EP-005: Delete Task

- [ ] AC-DELETE-01: Valid delete returns confirmation with 200
- [ ] AC-DELETE-02: Task is permanently removed from database
- [ ] AC-DELETE-03: Subsequent GET for deleted task returns 404
- [ ] AC-DELETE-04: Non-existent task returns 404

### EP-006: Toggle Completion

- [ ] AC-COMPLETE-01: Pending task becomes completed
- [ ] AC-COMPLETE-02: Completed task becomes pending
- [ ] AC-COMPLETE-03: updated_at timestamp is refreshed
- [ ] AC-COMPLETE-04: Non-existent task returns 404

---

## 11. OpenAPI Summary

```yaml
openapi: 3.0.3
info:
  title: Todo API
  version: 1.0.0
paths:
  /api/v1/tasks:
    get:
      summary: List all tasks
      security: [BearerAuth: []]
      responses:
        '200': {description: Tasks retrieved}
        '401': {description: Unauthorized}
    post:
      summary: Create task
      security: [BearerAuth: []]
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/TaskInput'}
      responses:
        '201': {description: Task created}
        '400': {description: Validation error}
        '401': {description: Unauthorized}
  /api/v1/tasks/{task_id}:
    get:
      summary: Get task by ID
      security: [BearerAuth: []]
      parameters:
        - name: task_id
          in: path
          required: true
          schema: {type: string, format: uuid}
      responses:
        '200': {description: Task retrieved}
        '401': {description: Unauthorized}
        '404': {description: Not found}
    put:
      summary: Update task
      security: [BearerAuth: []]
      responses:
        '200': {description: Task updated}
        '400': {description: Validation error}
        '401': {description: Unauthorized}
        '404': {description: Not found}
    delete:
      summary: Delete task
      security: [BearerAuth: []]
      responses:
        '200': {description: Task deleted}
        '401': {description: Unauthorized}
        '404': {description: Not found}
  /api/v1/tasks/{task_id}/complete:
    patch:
      summary: Toggle task completion
      security: [BearerAuth: []]
      responses:
        '200': {description: Completion toggled}
        '401': {description: Unauthorized}
        '404': {description: Not found}
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
  schemas:
    TaskInput:
      type: object
      properties:
        title: {type: string, minLength: 1, maxLength: 200}
        description: {type: string, maxLength: 1000}
      required: [title]
```

---

## 12. Migration Notes (Phase I to Phase II)

### ID Format Change

| Phase I | Phase II |
|---------|----------|
| Sequential integer (1, 2, 3...) | UUID v4 |

**Rationale**: UUIDs prevent ID enumeration attacks and support distributed systems in future phases.

### User Scoping

| Phase I | Phase II |
|---------|----------|
| Single user (implicit) | Multi-user (JWT-based) |

**Rationale**: All queries MUST include `WHERE user_id = <jwt.sub>` for data isolation.

### Timestamp Format

| Phase I | Phase II |
|---------|----------|
| Python datetime | ISO 8601 string (UTC) |

**Rationale**: JSON serialization standard; timezone-agnostic storage.

---

## Approval

**Specification Status**: Draft - Ready for Review

- [ ] All 6 endpoints fully specified
- [ ] Request/response schemas defined
- [ ] Error codes documented
- [ ] Acceptance criteria testable
- [ ] Security constraints explicit
- [ ] Migration path from Phase I documented

**Next Step**: Upon approval, proceed to database schema specification (`database/schema.md`).
