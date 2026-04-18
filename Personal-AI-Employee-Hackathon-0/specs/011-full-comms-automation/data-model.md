# Data Model: Full Communication Automation (Phase 6.5)

**Branch**: `011-full-comms-automation` | **Date**: 2026-04-11

---

## Entities

### CommunicationAction

Represents a single outbound action pending HITL approval or in execution.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY, UUID | Generated on enqueue |
| platform | TEXT | NOT NULL | whatsapp \| gmail \| linkedin \| facebook \| instagram \| twitter \| calendar |
| action_type | TEXT | NOT NULL | send_message \| send_media \| post \| reply_comment \| reply_dm \| draft_email \| send_email \| create_event \| update_event \| delete_event \| accept_connection \| react_post \| comment_post |
| target | TEXT | NOT NULL | Recipient JID / email / post_id / event_id |
| summary | TEXT | NOT NULL, MAX 500 chars | HITL display text (SC-002) — NO PII |
| content_ref | TEXT | NOT NULL | JSON blob stored locally; contains full content |
| status | TEXT | NOT NULL, DEFAULT 'pending' | pending \| approved \| declined \| executed \| failed |
| sent_at | TIMESTAMP | NOT NULL | When HITL WhatsApp message was sent |
| responded_at | TIMESTAMP | NULL | When CEO replied |
| executed_at | TIMESTAMP | NULL | When action was carried out |
| retry_count | INTEGER | DEFAULT 0 | Times execute was attempted |
| error_msg | TEXT | NULL | Last error if status = failed |

**State transitions**:
```
pending -> approved -> executed
pending -> declined
approved -> failed (on execute error, retry_count++)
```

**Indexes**: `(status, sent_at)` for fetching pending items for briefing reminders.

---

### ContactRecord

A contact with all known identifiers across platforms. Linked across platforms only on explicit CEO request.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY, UUID | |
| full_name | TEXT | NOT NULL | Canonical display name |
| phone_number | TEXT | NULL | E.164 format (+923001234567) |
| email_address | TEXT | NULL | Lowercase, normalized |
| whatsapp_jid | TEXT | NULL | JID format (923001234567@s.whatsapp.net) |
| linkedin_url | TEXT | NULL | Public profile URL |
| twitter_handle | TEXT | NULL | Without @ |
| facebook_id | TEXT | NULL | |
| instagram_handle | TEXT | NULL | Without @ |
| ceo_verified | BOOLEAN | NOT NULL, DEFAULT FALSE | Set TRUE after CEO confirms identity |
| created_at | TIMESTAMP | NOT NULL | |
| last_interaction | TIMESTAMP | NULL | Updated on any platform interaction |
| notes | TEXT | NULL | CEO-authored notes about contact |

**Rules**:
- Two contacts with same `full_name` are distinguished by `phone_number` or `email_address`
- Cross-platform linking: update individual platform fields on CEO explicit command only
- `ceo_verified = FALSE` contacts cannot be targets of outbound actions

---

### ContentDraft

A draft message/post before HITL approval.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY, UUID | |
| action_id | TEXT | FOREIGN KEY → CommunicationAction.id | |
| platform | TEXT | NOT NULL | |
| content | TEXT | NOT NULL | Full draft text |
| attachments | TEXT | NULL | JSON array of local file paths |
| target | TEXT | NOT NULL | Recipient/audience |
| model_tier | TEXT | NOT NULL | tier0 \| tier1 \| tier2 (ADR-0020) |
| drafted_at | TIMESTAMP | NOT NULL | |
| hitl_status | TEXT | NOT NULL, DEFAULT 'pending' | pending \| approved \| declined \| sent |

---

### EmailClassification

Result of classifying an email through the Tier 0 + Tier 1 classifier.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| message_id | TEXT | PRIMARY KEY | Gmail message ID |
| category | TEXT | NOT NULL | urgent \| opportunity \| promotional \| spam \| otc \| routine |
| confidence | FLOAT | NOT NULL, 0.0–1.0 | Rule-based = 1.0; model = 0.0–1.0 |
| classifier_tier | TEXT | NOT NULL | tier0 \| tier1 |
| is_auto_reply_candidate | BOOLEAN | NOT NULL | TRUE if greeting/thanks detected |
| template_key | TEXT | NULL | Key in auto_reply_templates.yaml |
| has_sensitive_attachment | BOOLEAN | NOT NULL | OTP, password, legal doc, fraud link |
| classified_at | TIMESTAMP | NOT NULL | |
| label_applied | TEXT | NULL | Gmail label applied |

---

### PlatformCredential

OAuth token or session reference per platform. Never stores raw tokens — only references `.env` variable names.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | platform name |
| platform | TEXT | NOT NULL, UNIQUE | gmail \| calendar \| linkedin \| facebook \| twitter \| whatsapp |
| env_key | TEXT | NOT NULL | Name of .env variable holding token |
| token_type | TEXT | NOT NULL | oauth2 \| session \| api_key |
| expires_at | TIMESTAMP | NULL | NULL = no expiry (session-based) |
| requires_reauth | BOOLEAN | NOT NULL, DEFAULT FALSE | Set TRUE 7 days before expiry |
| last_verified | TIMESTAMP | NULL | Last successful API call |

---

### RateLimitCounter

Enforces per-day platform action limits (FR-040).

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY | platform + action_type |
| platform | TEXT | NOT NULL | |
| action_type | TEXT | NOT NULL | dm_send \| connection_accept \| bulk_broadcast |
| count_today | INTEGER | NOT NULL, DEFAULT 0 | Reset at midnight UTC |
| daily_limit | INTEGER | NOT NULL | linkedin_dms=5, connection_accept=20, whatsapp_bulk=10 |
| date | DATE | NOT NULL | YYYY-MM-DD of current counter |

---

### InboxSummary

Aggregated daily view per platform for the CEO briefing.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | TEXT | PRIMARY KEY, UUID | |
| platform | TEXT | NOT NULL | |
| date | DATE | NOT NULL | |
| unread_count | INTEGER | NOT NULL, DEFAULT 0 | |
| action_required_count | INTEGER | NOT NULL, DEFAULT 0 | |
| opportunities_count | INTEGER | NOT NULL, DEFAULT 0 | |
| auto_replied_count | INTEGER | NOT NULL, DEFAULT 0 | |
| spam_removed_count | INTEGER | NOT NULL, DEFAULT 0 | |
| generated_at | TIMESTAMP | NOT NULL | |

---

## SQLite Database Layout

All Phase 6.5 data lives in two local SQLite databases:

```text
vault/
├── hitl_queue.db          <- CommunicationAction, ContentDraft
├── contacts.db            <- ContactRecord
└── rate_limits.db         <- RateLimitCounter, PlatformCredential
```

**Why separate DBs**:
- `hitl_queue.db`: high-write, append-heavy, action lifecycle data — benefits from WAL mode
- `contacts.db`: low-write, read-heavy, CEO's contact book
- `rate_limits.db`: very-high-write (every action increments counter), tiny rows

All databases use `aiosqlite` for async access. No ORM — raw SQL for simplicity (Constitution §X: minimal infrastructure; ADR-0003: local file-based persistence).

---

## Configuration Files (not database entities)

### `config/model_routing.yaml`
Defines ADR-0020 three-tier task routing. See plan.md Phase A for schema.

### `config/auto_reply_templates.yaml`
Pre-written templates for FR-012 auto-replies. Structure:
```yaml
templates:
  greeting_universal:
    en: "Thank you for reaching out! I'll get back to you soon."
    ur: "آپ سے رابطہ کرنے کا شکریہ! میں جلد ہی آپ سے رابطہ کروں گا۔"
    ar: "شكراً للتواصل معي! سأرد عليك قريباً."
    hi: "संपर्क करने के लिए धन्यवाद! मैं जल्द ही आपसे मिलूंगा।"
  thanks_universal:
    en: "You're welcome! Happy to help."
  congrats_universal:
    en: "Thank you so much! Really appreciate it."
```

### `config/linkedin_interests.yaml`
Keywords for LinkedIn feed monitoring (FR of Phase G watcher).
```yaml
keywords:
  - AI engineer
  - Python developer
  - hackathon
  - open source
  - machine learning
  - hiring
  - internship
hiring_signals:
  - "we are hiring"
  - "job opening"
  - "looking for"
```
