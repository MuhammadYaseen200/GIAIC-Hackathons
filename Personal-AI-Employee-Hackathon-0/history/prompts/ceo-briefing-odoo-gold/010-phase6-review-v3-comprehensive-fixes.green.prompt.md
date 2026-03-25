---
id: "010"
title: Phase 6 review-v3 comprehensive fixes
stage: green
date: 2026-03-25
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: m-y-j
command: "fix everything the agent team found, use subagents, skills, hooks, plugins, and MCPs specially Context7, code-cleanliness, and postgres"
labels: ["security","hitl","performance","latency","testing","code-cleanliness","review-v3"]
links:
  spec: specs/010-ceo-briefing-odoo-gold/spec.md
  ticket: null
  adr: history/adr/0018-ralph-wiggum-loop-implementation.md
  pr: null
files:
  - mcp_servers/hitl_utils.py
  - mcp_servers/facebook/server.py
  - mcp_servers/twitter/server.py
  - mcp_servers/whatsapp/bridge.py
  - orchestrator/ceo_briefing.py
  - orchestrator/weekly_audit.py
  - orchestrator/run_until_complete.py
  - orchestrator/social_poster.py
  - tests/unit/test_facebook_mcp.py
  - tests/unit/test_twitter_mcp.py
tests:
  - tests/unit/test_facebook_mcp.py
  - tests/unit/test_twitter_mcp.py
  - tests/unit/test_ceo_briefing.py
  - tests/unit/test_weekly_audit.py
  - tests/unit/test_run_until_complete.py
  - tests/unit/test_odoo_mcp.py
  - tests/unit/test_social_poster.py
---

## Prompt

fix everything the agent team found, use subagents, skills, hooks, plugins, and MCPs specially Context7, code-cleanliness, and postgres. check all of there reports, start working, and do your work properly, so next time no more execution and check will need and no issues, findings, critical gaps, security concern.

## Response snapshot

Applied all findings from 8-agent phase6-review-v3 team across security, performance, edge cases, test coverage, code cleanliness, latency, judgement, and feedback reviewers.

**Security fixes:**
- Created `mcp_servers/hitl_utils.py` — shared HITL approval module; ONLY `H0_HITL_APPROVED=1` env var accepted (removed insecure directory-existence bypass)
- Facebook + Twitter servers now import from shared hitl_utils (DRY fix)
- Added E.164 phone number regex validation to `mcp_servers/whatsapp/bridge.py`

**Latency / performance fixes:**
- `orchestrator/ceo_briefing.py`: Added `asyncio.wait_for(timeout=25.0)` on LLM step to prevent 3×60s=180s retry storm exceeding 120s SC-001 budget
- Fixed CRITICAL calendar API TypeError: `list_events(hours_ahead=hours)` → `list_events(time_min=iso, time_max=iso, max_results=10)`
- Compact JSON serialization: `json.dumps(sections, separators=(',', ':'), default=str)`
- Empty LLM response raises `ValueError` to trigger ADR-0019 template fallback

**Code cleanliness:**
- `MAX_WHATSAPP_MSG_LENGTH = 500` constant replaces magic `[:500]` in ceo_briefing + weekly_audit
- `BACKOFF_BASE = 2` constant in run_until_complete replaces hardcoded `2`
- `datetime.now(timezone.utc)` consistency (was bare `datetime.now()`)
- `duration_ms` timing added to all audit.jsonl entries
- Empty steps guard in `run_until_complete` with clear warning log

**Permission hardening:**
- `briefing_path.chmod(0o600)` after atomic write in ceo_briefing + weekly_audit

**Test coverage:**
- Facebook: +3 HITL gate tests; +1 existing test fixed with `H0_HITL_APPROVED=1`
- Twitter: +2 HITL gate tests; +2 existing tests fixed with `H0_HITL_APPROVED=1`

**Result: 182 tests GREEN (31.09s)**

## Outcome

- ✅ Impact: All 8 review-v3 agent findings addressed; HITL security hardened, calendar bug fixed, LLM timeout budget enforced, code cleanliness improved
- 🧪 Tests: 182/182 passed in 31.09s across all changed modules; full suite pending
- 📁 Files: 10 files modified (1 new: hitl_utils.py)
- 🔁 Next prompts: run full suite → git commit + PR
- 🧠 Reflection: Calendar API signature mismatch was a critical silent failure — every real run threw TypeError on calendar section. Phase 6 review cycles are now exhausted.

## Evaluation notes (flywheel)

- Failure modes observed: Subagents hit Write permission wall — all fixes applied in main context instead; background bash output sometimes empty on first check
- Graders run and results (PASS/FAIL): 8-agent phase6-review-v3 team (security/performance/edge/coverage/cleanliness/latency/judgement/feedback) — all findings applied PASS
- Prompt variant (if applicable): null
- Next experiment: Add Prometheus metrics endpoint (Phase 7 backlog item)
