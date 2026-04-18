# MCP Tool Contracts: Social (Facebook / Instagram / Twitter — Phase 6.5 Extensions)

**MCP Servers**: `mcp_servers/facebook/server.py`, `mcp_servers/twitter/server.py`
**Date**: 2026-04-11

---

## Facebook / Instagram Extensions

### `list_comments`
```
Input:
  post_id: str
  platform: str  # facebook | instagram
  max_results: int (default: 50)
Output:
  CommentList:
    comments: list[CommentSummary]
      comment_id: str
      author_name: str
      text_preview: str  (max 100 chars)
      is_spam: bool  (Tier 0 classifier result)
      posted_at: str
```

### `reply_comment`
```
Input:
  comment_id: str
  platform: str
  text: str
Output:
  reply_id: str
Notes:
  Requires HITL approval.
```

### `hide_comment`
```
Input:
  comment_id: str
  platform: str
Output:
  hidden: bool
Notes:
  Preferred over delete — reversible, less aggressive.
  Auto-triggered by Tier 0 spam classifier (FR-035).
  CEO notified in daily briefing.
```

### `list_dms`
```
Input:
  platform: str  # facebook | instagram
  max_results: int (default: 20)
Output:
  DMList:
    conversations: list[DMSummary]
      conversation_id: str
      participant_name: str
      message_preview: str (max 50 chars)
      unread: bool
      intent: str | None  # Tier 0/1 classification
```

### `reply_dm`
```
Input:
  conversation_id: str
  platform: str
  message: str
Output:
  message_id: str
Notes:
  Requires HITL approval.
```

### `get_page_analytics`
```
Input:
  platform: str  # facebook | instagram
  period: str  # 1d | 7d | 30d (default: 7d)
Output:
  PageAnalytics:
    reach: int
    impressions: int
    new_followers: int
    post_count: int
    top_post_id: str | None
    top_post_reach: int | None
    dms_received: int
    period: str
```

---

## Twitter / X Extensions

### `reply_tweet`
```
Input:
  tweet_id: str
  text: str  (max 280 chars)
Output:
  reply_id: str
Notes:
  Requires HITL approval.
```

### `like_tweet`
```
Input:
  tweet_id: str
Output:
  liked: bool
Notes:
  Low-stakes action — HITL optional (configurable in model_routing.yaml).
```

### `follow_user`
```
Input:
  user_id: str
Output:
  following: bool
  username: str
```

### `list_dms`
```
Input:
  max_results: int (default: 20)
Output:
  DMList
Errors:
  TwitterBasicTierRequired - Twitter DMs require Basic tier subscription
```

### `get_tweet_analytics`
```
Input:
  period: str  # 1d | 7d | 30d (default: 7d)
Output:
  TweetAnalytics:
    impressions: int
    engagements: int
    likes: int
    reposts: int
    new_followers: int
    top_tweet_id: str | None
    top_tweet_impressions: int | None
    period: str
```
