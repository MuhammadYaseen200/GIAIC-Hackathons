# H0 Personal AI Employee — Architecture

> **Updated**: 2026-03-15 | **Phase**: 6 Gold Tier Complete
> **Branch**: 010-ceo-briefing-odoo-gold | **SC-012 Exit Criterion**: this file must exist

---

## 1. System Overview

High-level data flow from external sources through the AI employee to actions:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL WORLD                                   │
│  Gmail Inbox  │  Google Calendar  │  WhatsApp  │  Social Platforms  │
└────────┬──────┴──────────┬────────┴──────┬─────┴──────────┬─────────┘
         │                 │               │                 │
         ▼                 ▼               ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP SERVERS (8 custom)                        │
│  gmail_mcp  │  calendar_mcp  │  whatsapp_mcp  │  linkedin_mcp       │
│  odoo_mcp   │  facebook_mcp  │  twitter_mcp   │  obsidian_mcp       │
└─────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         WATCHERS (polling)                           │
│  gmail_watcher.py  │  social_dm_monitor.py (P3)                     │
│  → vault/Inbox/ and vault/Needs_Action/ (JSONL)                     │
└─────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         VAULT (local filesystem)                     │
│  Inbox/ │ Needs_Action/ │ Pending_Approval/ │ Approved/ │ Done/     │
│  CEO_Briefings/ │ Logs/ (JSONL audit) │ Config/ │ Plans/            │
└─────────────────────────────┬───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATORS                                    │
│  orchestrator.py        → 15-min email triage loop                  │
│  ceo_briefing.py        → daily 07:00 briefing                      │
│  weekly_audit.py        → Monday 07:00 deep financial audit          │
│  linkedin_poster.py     → daily LinkedIn auto-post                   │
│  social_poster.py       → cross-platform HITL-gated posting         │
│  run_until_complete.py  → Ralph Wiggum retry loop (ADR-0018)        │
└─────────────────────────────┬───────────────────────────────────────┘
                               │ HITL required (SC-006/SC-008)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    HUMAN-IN-THE-LOOP (HITL)                          │
│  WhatsApp notification (≤500 chars, SC-003)                         │
│  Owner replies APPROVE / REJECT                                      │
│  vault/Pending_Approval/ → vault/Approved/ → action executed        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Agent Team Architecture

Phase 6 was built using a 4-teammate agent team:

```
Lead (main session — CONDUCTOR)
│
├── @loop-controller   → Phase gate enforcer (SDD cycle)
├── @path-warden       → File placement validation
├── @qa-overseer       → Quality gate after MVP
│
├── teammate-1 (backend-builder)  → Phase 1+2: Setup + Odoo MCP (T001–T020)
│   DELIVERABLES: mcp_servers/odoo/ (4 files), 12/12 tests GREEN
│   PATTERN: JSON-RPC httpx, session singleton (ADR-0016)
│
├── teammate-2 (backend-builder)  → Phase 3+4: Social MCPs (T021–T035)
│   DELIVERABLES: mcp_servers/facebook/ + mcp_servers/twitter/ (6 files), 26/26 tests GREEN
│   PATTERN: Meta Graph API (ADR-0017), tweepy OAuth 1.0a
│
├── teammate-3 (backend-builder)  → Phase 5+6+7+8: Orchestrators (T036–T060)
│   DELIVERABLES: ceo_briefing.py, weekly_audit.py, run_until_complete.py, 39/39 tests GREEN
│   PATTERN: Ralph Wiggum loop (ADR-0018), LLM fallback (ADR-0019)
│
└── teammate-4 (backend-builder)  → Phase 9+10: Skills + Polish + QA + PR (T061–T110)
    DELIVERABLES: 4 agent skills, social_dm_monitor.py, docs, coverage gate, PR
```

### Governance agents (invoked per-phase):
- **loop-controller**: SDD cycle gate — SPEC → PLAN → TASKS → IMPLEMENT → TEST → QA → DEPLOY
- **path-warden**: after every file write — validates placement against project structure
- **qa-overseer**: after each phase — validates acceptance criteria from spec.md

---

## 3. MCP Server Registry

All custom MCP servers registered in `~/.claude.json` under `mcpServers`:

| # | Server | Path | Tools | Status | ADR |
|---|--------|------|-------|--------|-----|
| 1 | `gmail_mcp` | `mcp_servers/gmail/server.py` | list_emails, read_email, send_email, search_emails, health_check | ✅ Live | ADR-0006 |
| 2 | `obsidian_mcp` | `mcp_servers/obsidian/server.py` | read_note, write_note, list_notes, search_notes, health_check, append_note | ✅ Live | ADR-0003 |
| 3 | `whatsapp_mcp` | `mcp_servers/whatsapp/server.py` | send_message, get_recent_messages, health_check | ✅ Live | ADR-0012 |
| 4 | `calendar_mcp` | `mcp_servers/calendar/server.py` | list_events, create_event, check_availability, health_check | ✅ Live | ADR-0006 |
| 5 | `linkedin_mcp` | `mcp_servers/linkedin/server.py` | create_post, get_recent_posts, get_profile, get_analytics, health_check | ✅ Live | ADR-0014 |
| 6 | `odoo_mcp` | `mcp_servers/odoo/server.py` | get_gl_summary, get_ar_aging, get_invoices_due, health_check | ✅ Live | ADR-0016 |
| 7 | `facebook_mcp` | `mcp_servers/facebook/server.py` | post_update, post_facebook_only, post_instagram_only, get_recent_posts, health_check | ✅ Live | ADR-0017 |
| 8 | `twitter_mcp` | `mcp_servers/twitter/server.py` | post_tweet, get_recent_tweets, health_check | ✅ Live | ADR-0017 |

**Shared utilities** (consumed by multiple MCP servers):
- `mcp_servers/hitl_utils.py` — HITL approval guard; imported by `facebook_mcp` and `twitter_mcp`. Requires `H0_HITL_APPROVED=1` env var to permit social posting. Directory-existence checks intentionally excluded (trivially bypassable).

**FastMCP pattern** (all servers mirror `mcp_servers/linkedin/server.py`):
```python
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("service-name")

@mcp.tool()
async def tool_name(param: str) -> dict:
    try:
        result = await client_function(param)
        return {"content": json.dumps(result)}
    except SpecificError as e:
        return {"isError": True, "content": json.dumps({"error": str(e)})}
```

---

## 4. Data Flow — CEO Briefing Pipeline

```
07:00 cron → orchestrator/ceo_briefing.py --now
│
├── run_until_complete("daily_briefing", steps=[...], max_retries=3)  [ADR-0018]
│   ├── step: collect_odoo_section    → odoo_mcp.get_invoices_due(days_ahead=7)
│   ├── step: collect_calendar_section → calendar_mcp.list_events(period="daily")
│   ├── step: collect_email_summary   → vault/Logs/ JSONL files
│   ├── step: collect_social_section  → vault/Logs/social_posts.jsonl
│   ├── step: draft_briefing          → _llm_draft() OR _template_draft() [ADR-0019]
│   ├── step: write_briefing_vault    → vault/CEO_Briefings/YYYY-MM-DD.md (atomic write)
│   └── step: send_hitl_notification  → GoBridge.send(≤500 chars)
│
├── Owner receives WhatsApp: "Briefing ready at vault/CEO_Briefings/..."
├── Owner replies APPROVE → check_approval_and_email() detects file in Pending_Approval/
└── gmail_mcp.send_email(to=owner, subject="Daily Briefing", body=briefing_content)

All 7 briefing sections always present even if source fails:
  1. Email Triage (24h)    4. Social Media Activity
  2. Financial Alert       5. LinkedIn Activity
  3. Calendar (48h)        6. Pending HITL Actions
                           7. System Health

Vault file format: vault/CEO_Briefings/YYYY-MM-DD.md with YAML frontmatter:
  type: ceo_briefing | period: daily | status: pending_approval → delivered
```

---

## 5. ADR Index

All architectural decisions documented in `history/adr/`:

| ADR | Title | Decision |
|-----|-------|----------|
| 0001 | Watcher Base Class Design | Abstract BaseWatcher with poll()/process_item() |
| 0002 | Async Integration Pattern for Sync SDKs | run_in_executor for blocking libs |
| 0003 | Local File-Based Data Persistence | Obsidian vault markdown + JSONL logs |
| 0004 | Keyword Heuristic Email Classification | Regex keyword tiers for email priority |
| 0005 | MCP Server Framework Stack | FastMCP (mcp library) for all servers |
| 0006 | Gmail OAuth2 Architecture + MCP Context | google-auth-oauthlib, token.json storage |
| 0007 | MCP Fallback Protocol (Orchestrator Wiring) | Direct import fallback when MCP unavailable |
| 0008 | Typed MCP Error Contract | `{"isError": True, "content": json.dumps({"error": "..."})}` |
| 0009 | Vault Operations Reuse Strategy | Centralized vault_ops.py + atomic_write |
| 0010 | Privacy Gate as Mandatory Pre-Processing Layer | privacy_gate.py before every external write |
| 0011 | HITL Approval Workflow and Draft State Machine | vault/Pending_Approval → Approved → Done |
| 0012 | WhatsApp Backend Strategy | Go bridge on :8080 as primary, pywa as fallback |
| 0013 | Three-Layer Email Priority Classifier | URGENT / ACTION_NEEDED / FYI tiers |
| 0014 | LinkedIn OAuth2 Token Lifecycle | 60-day access token, manual re-auth via script |
| 0015 | Cron Scheduling Strategy | H0_CRON_MANAGED idempotent strip+re-add pattern |
| 0016 | Odoo API Protocol Selection | JSON-RPC 2.0 via plain httpx (no odoorpc) |
| 0017 | Social Media MCP Architecture | Separate servers per platform; same token for FB+IG |
| 0018 | Ralph Wiggum Loop Implementation | run_until_complete: per-step retry + 2^n backoff |
| 0019 | CEO Briefing LLM Fallback Strategy | try Anthropic SDK → catch ANY → template fallback |

---

## 6. Known Weaknesses and Mitigations

| Weakness | Severity | Mitigation |
|----------|----------|-----------|
| Facebook token expires ~60 days | HIGH | `[TOKEN_EXPIRED]` structured error + HITL alert; re-run `scripts/facebook_auth.py` |
| Instagram not linked (HT-015 deferred) | MEDIUM | All IG tools return `{"status":"skipped","reason":"no_ig_account"}` gracefully |
| Odoo auth not TTL-aware | MEDIUM | `reset_session_cache()` called on 401; recovers on next request |
| Twitter DM search needs elevated access | MEDIUM | `check_twitter_dms()` returns `[]` with warning; posting (OAuth 1.0a) unaffected |
| Social DM Monitor is P3 | LOW | Not in MVP; polls but does not block briefing delivery |
| LLM credits can deplete | MEDIUM | `_template_draft()` fallback with `[TEMPLATE MODE]` flag (ADR-0019) |
| No graph/chart output in briefings | LOW | Text-only per spec; visual charts out of scope |
| Concurrent cron runs | HIGH | `FileLock` in orchestrator.py prevents simultaneous execution |
| All 7 briefing sections fail simultaneously | HIGH | Each section has empty-state handler (SC-005, SC-007) |

---

## 7. Lessons Learned (Phases 0–6 Retrospective)

### What worked well:
- **FastMCP pattern consistency**: All 8 MCP servers mirror `mcp_servers/linkedin/server.py`. Zero boilerplate divergence across 3 new servers (Odoo, Facebook, Twitter) in Phase 6.
- **TDD RED-first mandate**: Constitution Principle V enforced across all teammates. Every test written RED before implementation — caught 3 design issues early in Phase 3+4.
- **Graceful degradation everywhere**: HITL never blocked even when Odoo down, Instagram not linked, LLM credits low. `[TEMPLATE MODE]` briefings delivered on time.
- **Agent team parallelism**: teammate-2 and teammate-3 ran in parallel after T020 checkpoint. Phase 3+4+5+6 completed in a single Day 2 session.
- **Auth singleton pattern**: Session-level caching (Odoo, LinkedIn) with `reset_on_401` prevented flapping errors in long-running workflows.

### What to improve next time:
- **Context management**: Sessions hit 65–80% by end of day. Future phases should spawn teammates earlier to avoid context exhaustion before all checkpoints.
- **MCP registration format**: Confirmed correct format is `"server_name": {"type": "stdio", ...}` not `{"name": "...", "command": "..."}`. Document in onboarding.
- **Instagram setup**: Defer integration to when Business account is properly linked — HT-015 consumed 30 min of Day 1 before deferral decision.
- **Twitter Free tier limits**: Bearer Token cannot search; OAuth 1.0a can only post. Plan for this in architecture from Day 0.

### Phase patterns:
- Each phase took ~1 session (Day 1 = Phases 1–2, Day 2 = Phases 3–8, Day 3 = Phases 9–10)
- Fresh session = 100% context; spawn teammates before 60% to avoid mid-task cutoff
- `claude mcp add` always requires human; document in HUMAN-TASKS.md before starting phase
