# Implementation Plan: LinkedIn Auto-Poster + Cron Scheduling

**Branch**: `009-linkedin-cron-silver` | **Date**: 2026-03-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/009-linkedin-cron-silver/spec.md`

---

## Summary

Implement the two remaining Silver tier requirements: (1) LinkedIn Auto-Poster — an MCP server that posts to LinkedIn via OAuth2 with HITL WhatsApp approval and Privacy Gate filtering; (2) Cron Scheduling — system crontab entries for 15-minute orchestrator polling and daily LinkedIn post drafting. All new components reuse the FastMCP + Pydantic v2 + httpx pattern (ADR-0005), the vault-based HITL state machine (ADR-0011), and the singleton OAuth2 pattern (ADR-0006/0014).

---

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: FastMCP, Pydantic v2, httpx, python-dotenv (all existing in requirements.txt)
**Storage**: Obsidian vault (markdown + JSONL) — no new database
**Testing**: pytest, pytest-asyncio, unittest.mock (existing test stack)
**Target Platform**: WSL2 Ubuntu + Linux (Phase 7: Oracle VM)
**Performance Goals**: Draft created in <30s (SC-001), post published in <60s (SC-002)
**Constraints**: 1 post/day max (LinkedIn API), no hardcoded credentials, 80% test coverage (SC-008)
**Scale/Scope**: Single owner account, ~365 posts/year maximum

---

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Spec-Driven | spec.md approved, clarifications done, ADRs documented | ✅ PASS |
| II. Local-First Privacy | `linkedin_token.json` gitignored, credentials in `.env` only | ✅ PASS |
| III. HITL for Sensitive Actions | Every post → vault/Pending_Approval/ → WhatsApp → approve → publish (FR-001) | ✅ PASS |
| IV. MCP-First External Actions | LinkedIn API called ONLY through `linkedin_mcp` server tools | ✅ PASS |
| V. Test-Driven Quality | Contract tests for all 3 MCP tools; unit tests for poster workflow; SC-008 >80% | ✅ PASS |
| VI. Watcher Architecture | `linkedin_poster.py` is not a watcher — it's a workflow script invoked by cron/vault; no BaseWatcher needed | ✅ PASS |
| VII. Phase-Gated Delivery | Phase 5.5 — Phase 5 exit criteria met 2026-03-05 | ✅ PASS |
| IX. Security by Default | No credentials in logs/vault (FR-009); `offline_access` token in gitignored file | ✅ PASS |
| X. Graceful Degradation | API unreachable → draft/approval continues, fail only at publish (FR-008); lock file prevents cron overlap | ✅ PASS |

---

## Project Structure

### Documentation (this feature)

```text
specs/009-linkedin-cron-silver/
├── spec.md              # Feature requirements (complete)
├── plan.md              # This file
├── research.md          # Phase 0: API decisions, OAuth2, cron format
├── data-model.md        # Phase 1: Entity schemas, state transitions
├── quickstart.md        # Phase 1: Setup walkthrough
├── contracts/
│   └── linkedin_mcp_tools.md  # Phase 1: MCP tool contracts
└── tasks.md             # Phase 2: Task list (/sp.tasks — NOT created here)
```

### Source Code

```text
mcp_servers/linkedin/
├── __init__.py
├── server.py            # FastMCP entry point (post_update, get_profile, health_check)
├── auth.py              # OAuth2 token lifecycle (offline_access, auto-refresh, singleton)
├── client.py            # LinkedIn API v2 adapter (httpx, UGC Posts endpoint)
└── models.py            # Pydantic v2 models (PostUpdateInput/Result, ProfileResult, HealthCheckResult)

orchestrator/
└── linkedin_poster.py   # LinkedIn posting workflow (draft → HITL → publish)

scripts/
├── linkedin_auth.py     # One-time OAuth2 Authorization Code flow
├── setup_cron.sh        # Install cron entries (idempotent)
└── remove_cron.sh       # Remove cron entries (clean)

vault/
└── Config/
    └── linkedin_topics.md   # Owner-maintained topic pool

tests/
├── test_linkedin_mcp.py         # Contract tests (3 tools × all error paths)
├── test_linkedin_poster.py      # Unit tests (workflow state transitions)
└── test_cron_scripts.sh         # Bash smoke tests (idempotency, entry format)
```

---

## Implementation Phases

### Phase A — LinkedIn MCP Foundation (T001–T008)

**Goal**: LinkedIn MCP server with auth, API adapter, and all 3 tools passing contract tests.

Files: `mcp_servers/linkedin/__init__.py`, `auth.py`, `client.py`, `models.py`, `server.py`

Key decisions:
- `auth.py` follows ADR-0014: singleton `_linkedin_credentials`, auto-refresh on 401, `atomic_write` for token save
- `client.py` wraps httpx with `Authorization: Bearer` header injection; raises `LinkedInAPIError` on non-2xx
- `server.py` follows ADR-0005 FastMCP pattern identical to `mcp_servers/calendar/server.py`
- `models.py`: `PostUpdateInput(text: str, visibility: Literal["PUBLIC","CONNECTIONS"] = "PUBLIC")`

**Acceptance gate**: `pytest tests/test_linkedin_mcp.py` — all contract test cases PASS (mocked httpx)

---

### Phase B — LinkedIn Auth Script (T009–T011)

**Goal**: `scripts/linkedin_auth.py` generates `linkedin_token.json` with `offline_access` scope.

OAuth2 flow:
```
1. Build auth URL: https://www.linkedin.com/oauth/v2/authorization
   params: client_id, redirect_uri=http://localhost:8765/callback, scope, state, response_type=code
2. Open browser (subprocess/webbrowser)
3. Start local HTTP server on port 8765 to capture authorization code
4. Exchange code for tokens: POST /v2/accessToken with grant_type=authorization_code
5. Save linkedin_token.json with access_token + refresh_token + expires_at + person_urn
6. Print: "✅ Authentication successful. person_urn: urn:li:person:..."
```

**Acceptance gate**: Running `scripts/linkedin_auth.py` (manual HT-013b) produces `linkedin_token.json` with `refresh_token` present.

---

### Phase C — LinkedIn Poster Workflow (T012–T018)

**Goal**: `orchestrator/linkedin_poster.py` — full draft → HITL → publish workflow.

Entry points:
- `python3 orchestrator/linkedin_poster.py --draft "topic"` — manual trigger (FR-006)
- `python3 orchestrator/linkedin_poster.py --auto` — cron trigger (drafts from topic file, FR-013)
- Called by orchestrator when `type=linkedin_post` vault item detected (FR-007)

Workflow:
```python
1. Load topic (from --draft arg, or random from vault/Config/linkedin_topics.md)
2. Apply PrivacyGate.check(topic) → if blocked: log privacy_blocked, exit
3. Draft post text via LLM (existing orchestrator LLM call pattern, ~150-300 words)
4. Apply PrivacyGate.check(post_text) → if blocked: log privacy_blocked, exit
5. Check daily rate limit (read linkedin_posts.jsonl, count today's published)
   → if >= 1: log rate_limited, queue for tomorrow, notify WhatsApp, exit
6. Write vault/Pending_Approval/<timestamp>_linkedin_<slug>.md
7. Send enriched WhatsApp notification (FR-005 format: topic, type, preview, links, path)
8. Log event=drafted to linkedin_posts.jsonl
9. (Background / next orchestrator run) Check approval status via HITLManager
   → approved: call linkedin_mcp.post_update() → log published → move to vault/Done/
   → rejected/expired: log → move to vault/Rejected/
```

**Acceptance gate**: Manual test — `python3 orchestrator/linkedin_poster.py --draft "test topic"` → WhatsApp notification received, vault/Pending_Approval/ file created within 30s (SC-001).

---

### Phase D — Cron Scripts (T019–T023)

**Goal**: `scripts/setup_cron.sh` and `scripts/remove_cron.sh` — idempotent install/uninstall.

`setup_cron.sh` logic:
```bash
#!/bin/bash
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(which python3)"
CRON_LOG="$PROJECT_ROOT/vault/Logs/cron.log"

# Load CRON_LINKEDIN_TIME from .env (default: "0 9")
source "$PROJECT_ROOT/.env" 2>/dev/null || true
CRON_TIME="${CRON_LINKEDIN_TIME:-0 9}"
CRON_MINUTE=$(echo $CRON_TIME | cut -d' ' -f1)
CRON_HOUR=$(echo $CRON_TIME | cut -d' ' -f2)

ORCH_ENTRY="*/15 * * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/orchestrator.py >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
LINKEDIN_ENTRY="$CRON_MINUTE $CRON_HOUR * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/linkedin_poster.py --auto >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"

# Idempotency: only add if not already present
(crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED"; echo "$ORCH_ENTRY"; echo "$LINKEDIN_ENTRY") | crontab -
echo "✅ Cron entries installed. Run 'crontab -l' to verify."
```

`remove_cron.sh`: `crontab -l | grep -v "H0_CRON_MANAGED" | crontab -`

Lock file in `orchestrator/orchestrator.py` (existing file — add 3 lines at top):
```python
import fcntl
_lock = open("/tmp/h0_orchestrator.lock", "w")
fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # exits if locked
```

**Acceptance gate**: `./scripts/setup_cron.sh && ./scripts/setup_cron.sh && ./scripts/setup_cron.sh && crontab -l | grep H0_CRON_MANAGED | wc -l` == 2 (SC-007).

---

### Phase E — Vault Config + Topic File (T024)

**Goal**: Create `vault/Config/linkedin_topics.md` with default topics.

Simple file creation with 6 default topics. `linkedin_poster.py --auto` reads this file on each run (no caching needed — file is small and rarely changes).

---

### Phase F — Tests (T025–T029)

**Goal**: Contract tests + unit tests + bash smoke tests hitting SC-008 (>80% coverage).

`tests/test_linkedin_mcp.py` (contract tests):
- Mock `httpx.AsyncClient.post` to return LinkedIn API responses
- Test all 6 `post_update` contract cases + 3 `get_profile` + 4 `health_check`
- Test auto-refresh: mock 401 response → mock refresh response → mock successful post

`tests/test_linkedin_poster.py` (unit tests):
- Mock PrivacyGate, HITLManager, linkedin_mcp tools
- Test all state transitions: drafted, approved, rejected, expired, rate_limited, privacy_blocked

`tests/test_cron_scripts.sh` (bash):
- Run setup_cron.sh 3x → count H0_CRON_MANAGED entries == 2
- Run remove_cron.sh → count == 0

---

### Phase G — Integration Smoke Test (T030–T031)

**Goal**: End-to-end test against real LinkedIn API (staging-safe: use `visibility=CONNECTIONS` to minimize visibility).

- Run `python3 orchestrator/linkedin_poster.py --draft "test post from AI employee"`
- Verify WhatsApp notification received
- Reply "approve" via WhatsApp
- Verify `vault/Logs/linkedin_posts.jsonl` has `status=published` entry
- Verify post appears on LinkedIn profile

**Only runs with real credentials (not in CI)** — documented in quickstart.md as manual smoke test.

---

### Phase H — Polish + MCP Registry Update (T032)

**Goal**: Update `ai-control/MCP.md` to move `linkedin_mcp` from "Needed" to "Project-Custom" table.

Update MCP.md:
- Move row from "Needed MCP Servers" → "Project-Custom MCP Servers"
- Add: `linkedin_mcp | Post to LinkedIn with HITL | post_update, get_profile, health_check | mcp_servers/linkedin/server.py`

---

## Acceptance Criteria (from spec)

- [ ] SC-001: Draft + WhatsApp notification sent within 30s of trigger
- [ ] SC-002: Approved post published within 60s
- [ ] SC-003: Zero posts without explicit "approve" — invariant
- [ ] SC-004: Privacy Gate blocks 100% of sensitive content before approval
- [ ] SC-005: Cron processes vault/Needs_Action/ within 15 min
- [ ] SC-006: setup_cron.sh completes in <5s, entries visible immediately
- [ ] SC-007: setup_cron.sh run 3x → exactly 2 entries
- [ ] SC-008: Test coverage for LinkedIn MCP tools + cron scripts >80%
- [ ] SC-009: All LinkedIn events traceable in linkedin_posts.jsonl
- [ ] SC-010: Token refresh succeeds automatically in 95% of cases

---

## ADR References

- ADR-0005: FastMCP + Pydantic v2 + stdio transport (LinkedIn MCP follows this)
- ADR-0006: Gmail OAuth2 singleton pattern (LinkedIn auth.py mirrors this)
- ADR-0011: HITL approval state machine (LinkedIn poster reuses HITLManager)
- ADR-0014: LinkedIn OAuth2 token lifecycle (offline_access + auto-refresh)
- ADR-0015: Cron scheduling strategy (native cron vs APScheduler decision)
