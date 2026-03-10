# Data Model: LinkedIn Auto-Poster + Cron Scheduling

**Feature**: `009-linkedin-cron-silver` | **Date**: 2026-03-05

---

## Entities

### LinkedInDraft (vault/Pending_Approval/*.md)

Vault markdown file with YAML frontmatter. Written by `linkedin_poster.py` after Privacy Gate passes.

```yaml
---
type: linkedin_post
topic: "Building AI agents with Claude"
visibility: PUBLIC
status: pending          # pending | approved | rejected | expired
created: "2026-03-05T09:00:00Z"
expires: "2026-03-06T09:00:00Z"   # 24 hours after creation
content_hash: "sha256:abc123..."  # hash of full post text
agent: linkedin_poster
---

# LinkedIn Draft: Building AI agents with Claude

**Preview** (first 300 chars):
Excited to share what I've been working on this week — building autonomous AI agents using Claude Code...

**Full content**:
[full post text here]

**Referenced links**: None
**Visibility**: PUBLIC
**Word count**: 187

---
Reply "approve" to publish to LinkedIn, "reject" to discard.
Full draft: vault/Pending_Approval/2026-03-05_linkedin_building-ai-agents.md
```

**Validation rules**:
- `type` MUST be `linkedin_post`
- `status` transitions: `pending` → `approved` | `rejected` | `expired`
- `expires` MUST be exactly 24h after `created`
- `content_hash` MUST be SHA-256 of full post text (for audit log integrity)
- `visibility` MUST be `PUBLIC` or `CONNECTIONS`

---

### LinkedInPost (vault/Logs/linkedin_posts.jsonl)

JSONL audit log entry. One line per post event (draft, approved, rejected, published, failed).

```json
{
  "event_id": "uuid4",
  "event": "published",
  "topic": "Building AI agents with Claude",
  "post_urn": "urn:li:ugcPost:7123456789012345678",
  "content_hash": "sha256:abc123...",
  "word_count": 187,
  "visibility": "PUBLIC",
  "timestamp": "2026-03-05T09:01:34Z",
  "status": "published",
  "draft_file": "vault/Pending_Approval/2026-03-05_linkedin_building-ai-agents.md"
}
```

**Event types**:
- `drafted` — post content created, sent for approval
- `approved` — owner replied "approve"
- `rejected` — owner replied "reject"
- `expired` — 24h elapsed without response
- `published` — successfully posted to LinkedIn API
- `failed` — LinkedIn API error during publish
- `rate_limited` — daily limit already hit, queued to next day
- `privacy_blocked` — Privacy Gate blocked content, draft discarded

**Validation rules**:
- `event_id`: UUID4, unique per event
- `post_urn`: present only for `published` events
- `timestamp`: ISO 8601 UTC
- All events for a given post share the same `content_hash`

---

### CronEntry (conceptual — not stored in vault)

Represents a crontab entry managed by `setup_cron.sh`. Not persisted in vault — source of truth is `crontab -l`.

```
Fields:
  job_name:     "h0_orchestrator" | "h0_linkedin_drafter"
  schedule:     "*/15 * * * *" | "${CRON_MINUTE} ${CRON_HOUR} * * *"
  command:      absolute path python3 invocation
  log_target:   vault/Logs/cron.log
  env_source:   .env (sourced before command)
```

**Idempotency marker**: `setup_cron.sh` uses `# H0_CRON_MANAGED` comment suffix to identify managed entries for deduplication and removal.

---

### ApprovalRequest (subset of LinkedInDraft)

The vault/Pending_Approval/ file IS the approval request. No separate entity needed — HITLManager reads the YAML frontmatter directly.

Key fields read by HITLManager:
- `type` — routes to LinkedIn workflow
- `status` — checked by `check_approval_status()`
- `expires` — expiry enforcement
- `content_hash` — included in audit log

---

## State Transitions

```
[trigger: manual/cron/vault]
        │
        ▼
  Privacy Gate check
    ├─ BLOCKED → event=privacy_blocked, STOP
    └─ PASS
        │
        ▼
  AI Draft Generated
        │
        ▼
  vault/Pending_Approval/*.md  (status=pending)
  WhatsApp notification sent   (event=drafted)
        │
   ┌────┴────┐
   │         │
"approve"  "reject" or 24h timeout
   │         │
   ▼         ▼
status=    status=rejected/expired
approved   vault/Rejected/
   │        event=rejected/expired
   │
   ▼
Rate limit check (1/day)
   ├─ EXCEEDED → event=rate_limited, queue tomorrow, notify
   └─ OK
       │
       ▼
  linkedin_mcp.post_update()
   ├─ SUCCESS → vault/Done/, event=published, post_urn logged
   └─ FAILURE → event=failed, WhatsApp error notification
```

---

## File Naming Convention

| File | Pattern | Example |
|------|---------|---------|
| Draft approval request | `vault/Pending_Approval/<date>_linkedin_<slug>.md` | `2026-03-05_linkedin_building-ai-agents.md` |
| Rejected draft | `vault/Rejected/<date>_linkedin_<slug>.md` | same name, moved |
| Published post | `vault/Done/<date>_linkedin_<slug>.md` | same name, moved |
| Topic config | `vault/Config/linkedin_topics.md` | fixed name |
| Audit log | `vault/Logs/linkedin_posts.jsonl` | fixed name, append-only |
| Cron log | `vault/Logs/cron.log` | fixed name, append-only |
| Auth token | `linkedin_token.json` | project root, gitignored |
