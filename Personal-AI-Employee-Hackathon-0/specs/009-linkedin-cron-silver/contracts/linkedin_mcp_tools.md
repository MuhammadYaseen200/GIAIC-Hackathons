# MCP Tool Contracts: LinkedIn MCP Server

**Feature**: `009-linkedin-cron-silver` | **Date**: 2026-03-05
**Server**: `mcp_servers/linkedin/server.py` | **Transport**: stdio JSON-RPC

---

## Tool: `post_update`

Posts a text update to LinkedIn on behalf of the owner.

**Input schema**:
```json
{
  "text": {
    "type": "string",
    "minLength": 1,
    "maxLength": 3000,
    "description": "Post content. Must have passed Privacy Gate before calling this tool."
  },
  "visibility": {
    "type": "string",
    "enum": ["PUBLIC", "CONNECTIONS"],
    "default": "PUBLIC",
    "description": "Post visibility. PUBLIC = anyone on LinkedIn. CONNECTIONS = 1st-degree connections only."
  }
}
```

**Success response** (status 201 from LinkedIn API):
```json
{
  "post_urn": "urn:li:ugcPost:7123456789012345678",
  "published_at": "2026-03-05T09:01:34Z",
  "word_count": 187,
  "visibility": "PUBLIC"
}
```

**Error responses**:
```json
// Auth failure (token expired + refresh failed)
{"isError": true, "content": "{\"error\": \"auth_required\", \"message\": \"LinkedIn token expired. Run scripts/linkedin_auth.py\"}"}

// Rate limited by LinkedIn API
{"isError": true, "content": "{\"error\": \"rate_limited\", \"message\": \"LinkedIn API: daily post limit exceeded\"}"}

// API unreachable
{"isError": true, "content": "{\"error\": \"api_unavailable\", \"message\": \"LinkedIn API unreachable: <detail>\"}"}

// Text too long
{"isError": true, "content": "{\"error\": \"validation_error\", \"message\": \"text exceeds 3000 character limit\"}"}
```

**Contract test cases**:

| # | Input | Expected Output |
|---|-------|-----------------|
| 1 | `text="Hello world", visibility="PUBLIC"` | `post_urn` present, `published_at` ISO format, `word_count=2` |
| 2 | `text="..."` (3001 chars) | `isError=true`, `error="validation_error"` |
| 3 | Token expired, refresh succeeds | Post published, no error surfaced |
| 4 | Token expired, refresh fails | `isError=true`, `error="auth_required"` |
| 5 | `visibility="CONNECTIONS"` | Post published with CONNECTIONS visibility |
| 6 | LinkedIn API 503 | `isError=true`, `error="api_unavailable"` |

---

## Tool: `get_profile`

Retrieves the owner's LinkedIn profile — used to verify LINKEDIN_PERSON_URN.

**Input schema**: none

**Success response**:
```json
{
  "person_urn": "urn:li:person:abc123XYZ",
  "display_name": "Muhammad Yaseen",
  "headline": "AI Developer | Python | Web Dev",
  "fetched_at": "2026-03-05T09:00:00Z"
}
```

**Error responses**:
```json
{"isError": true, "content": "{\"error\": \"auth_required\", \"message\": \"...\"}"}
{"isError": true, "content": "{\"error\": \"api_unavailable\", \"message\": \"...\"}"}
```

**Contract test cases**:

| # | Condition | Expected Output |
|---|-----------|-----------------|
| 1 | Valid token, API available | `person_urn` matches `LINKEDIN_PERSON_URN` env var |
| 2 | Token expired, refresh succeeds | Returns profile after silent refresh |
| 3 | Auth failure | `isError=true`, `error="auth_required"` |

---

## Tool: `health_check`

Verifies LinkedIn API connectivity and OAuth token validity.

**Input schema**: none

**Success response**:
```json
{
  "status": "healthy",
  "person_urn": "urn:li:person:abc123XYZ",
  "token_expires_at": "2026-05-04T09:01:34Z",
  "checked_at": "2026-03-05T09:00:00Z"
}
```

**Degraded response** (API down but token valid):
```json
{
  "status": "degraded",
  "person_urn": "urn:li:person:abc123XYZ",
  "token_expires_at": "2026-05-04T09:01:34Z",
  "checked_at": "2026-03-05T09:00:00Z",
  "warning": "LinkedIn API unreachable — posts will fail until connectivity restored"
}
```

**Error response** (auth required):
```json
{"isError": true, "content": "{\"error\": \"auth_required\", \"message\": \"Run scripts/linkedin_auth.py\"}"}
```

**Contract test cases**:

| # | Condition | Expected Output |
|---|-----------|-----------------|
| 1 | Valid token, API available | `status="healthy"`, `person_urn` present |
| 2 | Valid token, API unavailable | `status="degraded"`, `warning` present |
| 3 | Token expired, refresh succeeds | `status="healthy"` after silent refresh |
| 4 | Token missing entirely | `isError=true`, `error="auth_required"` |

---

## Pydantic v2 Models (`mcp_servers/linkedin/models.py`)

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class PostUpdateInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000)
    visibility: Literal["PUBLIC", "CONNECTIONS"] = "PUBLIC"

class PostUpdateResult(BaseModel):
    post_urn: str
    published_at: str  # ISO 8601
    word_count: int
    visibility: str

class ProfileResult(BaseModel):
    person_urn: str
    display_name: str
    headline: str
    fetched_at: str  # ISO 8601

class HealthCheckResult(BaseModel):
    status: Literal["healthy", "degraded"]
    person_urn: str
    token_expires_at: str  # ISO 8601
    checked_at: str  # ISO 8601
    warning: str | None = None
```
