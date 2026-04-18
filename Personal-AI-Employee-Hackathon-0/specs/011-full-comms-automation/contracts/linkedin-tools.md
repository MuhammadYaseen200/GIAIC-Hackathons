# MCP Tool Contracts: LinkedIn (Phase 6.5 Extensions)

**MCP Server**: `mcp_servers/linkedin/server.py` + `mcp_servers/linkedin/dm_server.py`
**Date**: 2026-04-11

---

## New Tools (server.py)

### `update_profile_field`
```
Input:
  field: str  # headline | summary | current_position | open_to_work | hiring_status
  value: str | bool
Output:
  updated: bool
  field: str
  new_value: str
```

### `get_analytics`
```
Input:
  period: str  # 1d | 7d | 30d (default: 7d)
Output:
  AnalyticsReport:
    impressions: int
    profile_views: int
    post_reach: int
    follower_count: int
    follower_growth: int
    top_post_id: str | None
    top_post_impressions: int | None
    period: str
```

### `react_post`
```
Input:
  post_id: str
  reaction: str  # like | celebrate | support | funny | love | insightful
Output:
  reacted: bool
Notes:
  Requires HITL approval (irreversible — visible on CEO's public profile).
```

### `comment_post`
```
Input:
  post_id: str
  text: str  (max 1250 chars)
Output:
  comment_id: str
Notes:
  Requires HITL approval.
```

### `accept_connection`
```
Input:
  profile_id: str
Output:
  accepted: bool
  connection_name: str
Errors:
  RateLimitExceeded - 20/day cap hit (FR-040)
```

### `search_profiles`
```
Input:
  query: str
  filters:
    industry: str | None
    location: str | None
    company: str | None
    connection_degree: int | None  # 1 | 2 | 3
  max_results: int (default: 20)
Output:
  SearchResults:
    profiles: list[ProfileSummary]
      profile_id: str
      name: str
      headline: str
      connection_degree: int
      location: str | None
    total_found: int
```

### `save_post`
```
Input:
  post_id: str
Output:
  saved: bool
  post_url: str  (logged to vault for reference)
```

---

## DM Tools (dm_server.py) — GATED

All tools below raise `LinkedInDMUnavailable` if `LINKEDIN_MESSAGING_API_KEY` not set.

### `list_conversations`
```
Input:
  max_results: int (default: 20)
Output:
  ConversationList:
    conversations: list[ConversationSummary]
      conversation_id: str
      participant_name: str
      last_message_preview: str  (max 50 chars)
      unread: bool
      dm_intent: str | None  # classified by dm_classifier
```

### `send_dm`
```
Input:
  profile_id: str
  message: str
Output:
  message_id: str
Errors:
  RateLimitExceeded - 5/day cap hit (FR-025)
  LinkedInDMUnavailable - API key not set
Notes:
  Requires HITL approval before execution.
```

### `classify_dm_intent`
```
Input:
  message_text: str (metadata/snippet only, max 200 chars)
Output:
  intent: str  # job_inquiry | networking | spam | sales | other
  confidence: float
  suggested_reply_tone: str | None  # professional | friendly | decline
Notes:
  Uses Tier 0 (keyword) first; Tier 1 if confidence < 0.8.
  Never sends full message to Tier 1 model (FR-043).
```
