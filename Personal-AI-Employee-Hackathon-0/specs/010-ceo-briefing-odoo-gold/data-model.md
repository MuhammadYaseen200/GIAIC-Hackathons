# Data Model — CEO Briefing + Odoo Gold Tier

**Feature**: CEO Briefing + Odoo Gold Tier
**Branch**: `010-ceo-briefing-odoo-gold`
**Date**: 2026-03-13

---

## Odoo Financial Data

### GL Account Types

| Type | Code Range | Normal Balance |
|------|-----------|----------------|
| Assets | 1000–1999 | Debit |
| Liabilities | 2000–2999 | Credit |
| Equity | 3000–3999 | Credit |
| Income | 4000–4999 | Credit |
| Expenses | 5000–5999 | Debit |

**Zero balance detection**: When all GL accounts have zero balances, `collect_odoo_section()` appends the note "Demo data detected — verify with real accounts before acting" to the financial section.

### AR Aging Buckets

| Bucket | Days Overdue | Model Field |
|--------|-------------|-------------|
| Current | 0–30 | `amount_0_30` |
| 31–60 days | 31–60 | `amount_31_60` |
| 61–90 days | 61–90 | `amount_61_90` |
| Bad debt | >90 | `amount_over_90` |

All four buckets are always present in `ARAgingResult`. A bucket with no overdue invoices shows `0.0`.

### Invoice Lifecycle States

```
draft → posted → paid
              ↘ cancelled
```

Orchestrator queries filter: `state=posted AND payment_state!=paid`
Daily briefing shows only invoices where `days_remaining < 0` (overdue only).
Weekly audit shows all invoices due within the next 7 days.

### Odoo Session Auth Flow

```
1. POST /web/session/authenticate
   Body: {"jsonrpc":"2.0","method":"call","params":{"db":ODOO_DB,"login":ODOO_USER,"password":ODOO_PASSWORD}}
   → Response: {"result":{"session_id":"<sid>","uid":<N>,...}}

2. Include Cookie: session_id=<sid> in all subsequent requests to /web/dataset/call_kw

3. On 401 response:
   → reset_session_cache()  (clears in-memory singleton)
   → retry authenticate once
   → on second 401: raise OdooConnectionError

4. Session lifetime: ~1h (Odoo default)
   → No persistent session file (in-memory singleton only)
```

**Error types**:
- `OdooAuthError`: credentials rejected (wrong password / user)
- `OdooConnectionError`: network failure, container not running

---

## CEO Briefing Vault Schema

### Daily Briefing File

**Path**: `vault/CEO_Briefings/YYYY-MM-DD.md`

```yaml
---
type: ceo_briefing
period: daily
date: YYYY-MM-DD
status: pending_approval | approved | delivered | rejected
sections_generated: 7
sections_failed: []
llm_mode: llm | template
created_at: ISO8601
---
```

### Weekly Audit File

**Path**: `vault/CEO_Briefings/week-YYYY-WNN.md`

```yaml
---
type: weekly_audit
period: weekly
date: YYYY-MM-DD
iso_week: WNN
status: pending_approval | approved | delivered | rejected
sections_generated: 7
sections_failed: []
llm_mode: llm | template
created_at: ISO8601
---
```

**Idempotency**: Both files are overwritten if re-run on the same date/week. The `created_at` field preserves the original creation time; `updated_at` is added on overwrite.

### 7 Mandatory Sections

| # | Section | Source | Daily | Weekly |
|---|---------|--------|-------|--------|
| 1 | Email Triage | `vault/Logs/` orchestrator decisions | 24h counts by priority | 7-day counts |
| 2 | Financial Alert | Odoo MCP `get_invoices_due` | Overdue invoices only | Full GL + AR + invoices due 7d |
| 3 | Calendar | Calendar MCP `list_events` | Next 48h events | Full week events |
| 4 | Social Media Activity | `vault/Logs/social_posts.jsonl` | Posts last 24h | Posts last 7d |
| 5 | LinkedIn Activity | `vault/Logs/linkedin_posts.jsonl` | Posts last 24h | Posts last 7d |
| 6 | Pending HITL Actions | `vault/Pending_Approval/` count | Count | Count |
| 7 | System Health | MCP health checks | All MCP status | All MCP status |

**Graceful degradation**: Any section that raises an exception returns `{"status": "unavailable", "note": "<reason>"}`. The briefing is still generated with the remaining sections.

---

## Audit Log Schema

### File: `vault/Logs/audit.jsonl`

Written by `run_until_complete._log_audit()` after each workflow step attempt.

```json
{"ts": "ISO8601Z", "workflow": "daily_briefing", "step": "collect_odoo", "attempt": 1, "outcome": "success|failed", "error": ""}
```

### File: `vault/Logs/ceo_briefing.jsonl`

Written by `ceo_briefing._log_event()` and `weekly_audit._log_event()` after each run.

```json
{"ts": "ISO8601Z", "event": "briefing_generated", "period": "daily", "status": "pending_approval", "duration_s": 12.3, "completed_steps": ["collect_email", "collect_calendar", "collect_odoo", "collect_social", "draft", "write_vault", "send_hitl"], "errors": []}
```

### File: `vault/Logs/social_posts.jsonl`

Written by `social_poster.py` after each post attempt.

```json
{"ts": "ISO8601Z", "platform": "facebook|twitter|instagram|linkedin", "action": "published|draft_created|failed", "post_id": "...", "success": true, "error": ""}
```

---

## Pydantic Models Reference

### Odoo MCP (`mcp_servers/odoo/models.py`)

```python
class GLSummary(BaseModel):
    by_type: dict[str, float]  # {"income": 0.0, "expense": 0.0, ...}

class ARPartner(BaseModel):
    name: str
    amount: float
    days_overdue: int

class ARAgingResult(BaseModel):
    current: float
    overdue_30_60: float
    overdue_61_90: float
    bad_debt_90plus: float
    partners: list[ARPartner]

class InvoiceResult(BaseModel):
    invoice_id: int
    partner_name: str
    amount: float
    due_date: str
    days_remaining: int  # negative = overdue

class OdooHealthResult(BaseModel):
    healthy: bool
    odoo_version: str
    db_name: str
    error: str | None
```

### Facebook/Instagram MCP (`mcp_servers/facebook/models.py`)

```python
class PostResult(BaseModel):
    success: bool
    post_id: str | None
    url: str | None
    platform: str  # "facebook" | "instagram"
    error: str | None

class FacebookHealthResult(BaseModel):
    healthy: bool
    page_reachable: bool
    token_valid: bool
    error: str | None
```

### Twitter/X MCP (`mcp_servers/twitter/models.py`)

```python
class TweetInput(BaseModel):
    text: str
    @validator('text')
    def text_max_280(cls, v):
        assert len(v) <= 280, "Tweet exceeds 280 characters"
        return v

class TweetResult(BaseModel):
    success: bool
    tweet_id: str | None
    url: str | None
    error: str | None

class TwitterHealthResult(BaseModel):
    healthy: bool
    token_valid: bool
    api_reachable: bool
    error: str | None
```
