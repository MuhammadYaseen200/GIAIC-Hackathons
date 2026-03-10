# Research: LinkedIn Auto-Poster + Cron Scheduling

**Feature**: `009-linkedin-cron-silver` | **Date**: 2026-03-05 | **Phase**: 0

---

## D1 — LinkedIn API v2: UGC Posts vs Share API

**Decision**: Use **UGC Posts API** (`POST /v2/ugcPosts`)

**Rationale**: LinkedIn deprecated the Share API v1 in 2022. UGC (User-Generated Content) Posts is the current supported endpoint for creating text posts on behalf of a member. The `w_member_social` OAuth scope grants write access to UGC posts.

**Endpoint**:
```
POST https://api.linkedin.com/v2/ugcPosts
Authorization: Bearer <access_token>
Content-Type: application/json
X-Restli-Protocol-Version: 2.0.0

{
  "author": "urn:li:person:<LINKEDIN_PERSON_URN>",
  "lifecycleState": "PUBLISHED",
  "specificContent": {
    "com.linkedin.ugc.ShareContent": {
      "shareCommentary": {
        "text": "<post_text>"
      },
      "shareMediaCategory": "NONE"
    }
  },
  "visibility": {
    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"  // or "CONNECTIONS"
  }
}
```

**Response** (201 Created): `X-RestLi-Id` header contains the post URN (e.g., `urn:li:ugcPost:7123456789`)

**Profile endpoint**: `GET https://api.linkedin.com/v2/me` — returns `id` field = LINKEDIN_PERSON_URN

**Alternatives considered**:
- Share API v1 (`/v1/people/~/shares`) — deprecated, rejected
- Community Management API — requires LinkedIn Partner Program approval, overkill for personal posting

---

## D2 — OAuth2 Scopes Required

**Decision**: Request `r_liteprofile w_member_social offline_access`

**Rationale** (confirmed in clarification session Q1, 2026-03-05):
- `r_liteprofile` — read profile (get LINKEDIN_PERSON_URN)
- `w_member_social` — write UGC posts
- `offline_access` — obtain refresh token for SC-010 auto-refresh (without this, only 60-day access token, no auto-renewal)

**Token lifecycle**:
- Access token: 60-day expiry
- Refresh token: no documented expiry (LinkedIn does not expire refresh tokens unless app is deauthorized)
- Refresh endpoint: `POST https://www.linkedin.com/oauth/v2/accessToken` with `grant_type=refresh_token`

**Token file format** (`linkedin_token.json`):
```json
{
  "access_token": "AQX...",
  "refresh_token": "AQX...",
  "expires_at": 1756000000,
  "token_type": "Bearer",
  "scope": "r_liteprofile w_member_social offline_access"
}
```

---

## D3 — HTTP Client: httpx (async)

**Decision**: Use **httpx** with async/await

**Rationale**: Constitution requires async I/O in watchers and MCP servers. `httpx` is already the project standard (ADR-0005, ADR-0012). LinkedIn API calls are straightforward HTTP — no SDK needed. Direct httpx calls give full control over headers and retry logic.

**Dependencies to add to requirements.txt**:
```
httpx>=0.27.0          # async HTTP client (likely already present)
```

---

## D4 — Daily Post Topic Selection

**Decision**: Random pick from `vault/Config/linkedin_topics.md` (clarification Q2, 2026-03-05)

**Format** (`vault/Config/linkedin_topics.md`):
```markdown
# LinkedIn Post Topics

- AI learning progress and experiments
- Web development projects and milestones
- Freelance availability and service offerings
- Hackathon milestones and achievements
- Python and automation insights
- Agent development patterns
```

**Fallback**: If file missing → use 4 built-in defaults (FR-017). Topics are plain text lines starting with `-`.

**AI drafting**: Claude (via orchestrator's existing LLM call pattern) receives the topic + owner persona and drafts a professional 150-300 word LinkedIn post. No additional AI library needed.

---

## D5 — Cron Lock File Strategy

**Decision**: Lock file at `/tmp/h0_orchestrator.lock`

**Rationale**: `/tmp` is writable without permissions; lock file survives Python crashes (PID-based check); cleared on reboot automatically. Pattern: write PID to lock file on start, check if PID still running on next invocation, release on clean exit.

**Implementation**:
```python
import fcntl, os, sys
LOCK_FILE = "/tmp/h0_orchestrator.lock"
lock_fd = open(LOCK_FILE, "w")
try:
    fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    sys.exit(0)  # Another instance running — exit cleanly
```
`fcntl.LOCK_EX | LOCK_NB` is non-blocking exclusive lock — perfect for cron double-invocation prevention.

---

## D6 — Cron Entry Format

**Decision**: Absolute paths + source .env + timestamp wrapper

```bash
# Orchestrator — every 15 minutes
*/15 * * * * cd /abs/path && export $(grep -v '^#' .env | xargs) && python3 orchestrator/orchestrator.py >> vault/Logs/cron.log 2>&1

# LinkedIn drafter — daily (default 09:00, configurable via CRON_LINKEDIN_TIME=0 9)
0 9 * * * cd /abs/path && export $(grep -v '^#' .env | xargs) && python3 orchestrator/linkedin_poster.py --auto >> vault/Logs/cron.log 2>&1
```

`CRON_LINKEDIN_TIME` in `.env` stores the cron time as two fields: `"0 9"` → minute=0, hour=9. `setup_cron.sh` substitutes these into the crontab entry.

---

## D7 — HITL State Transitions for LinkedIn Posts

**Decision**: Extend existing HITLManager pattern with LinkedIn-specific vault paths

Vault state machine:
```
orchestrator/linkedin_poster.py --draft "topic"
  → Privacy Gate check
  → AI drafts post content
  → write vault/Pending_Approval/<timestamp>_linkedin_<topic_slug>.md
  → WhatsApp notification (enriched format: topic, type, 300-char preview, links, path)
  ↓
  owner replies "approve" → HITLManager moves file to vault/Approved/
    → linkedin_poster reads approved file
    → calls linkedin_mcp.post_update()
    → logs to vault/Logs/linkedin_posts.jsonl
    → moves to vault/Done/
  ↓
  owner replies "reject" or 24h timeout → vault/Rejected/
    → logs with status=rejected/expired
```

No new state machine needed — HITLManager already handles file moves. LinkedIn poster calls `hitl_manager.create_approval_request()` and `hitl_manager.check_approval_status()`.

---

## D8 — Rate Limit: 1 Post Per Day

**Decision**: Day-boundary check against `vault/Logs/linkedin_posts.jsonl`

On each potential publish attempt: read `linkedin_posts.jsonl`, count entries where `status=published` AND `date == today (UTC)`. If count >= 1 → queue to tomorrow's slot, notify owner via WhatsApp.

No LinkedIn API call needed for this check — vault log is the source of truth.
