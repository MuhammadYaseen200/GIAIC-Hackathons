---
id: 009
title: LinkedIn Auto-Poster Performance Audit
stage: misc
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: performance review of LinkedIn Auto-Poster codebase
labels: ["performance","review","linkedin","async","bottleneck"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - history/reports/performance-review-linkedin-2026-03-09.md
tests:
  - none
---

## Prompt

You are a **performance reviewer** for the H0 Personal AI Employee project. Review the LinkedIn Auto-Poster codebase for performance issues and bottlenecks.

Working directory: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`

## Your mission: Performance audit of Phase 5.5 LinkedIn implementation

### Files to review:
1. `mcp_servers/linkedin/client.py` — HTTP client, timeouts, retry logic
2. `mcp_servers/linkedin/auth.py` — Singleton pattern, credential caching
3. `orchestrator/linkedin_poster.py` — Workflow, file I/O patterns
4. `mcp_servers/linkedin/server.py` — FastMCP server overhead

### Performance checks:

1. **HTTP timeouts**: Are timeouts appropriate? (post: 30s, profile: 15s, health: 5s — verify these)
2. **Credential caching**: Does `get_linkedin_credentials()` avoid disk reads on every call?
3. **Vault file I/O**: Is `atomic_write` efficient? Are vault scans bounded?
4. **Async patterns**: Are async/await used correctly? Any blocking calls in async context?
5. **SC-001 compliance**: Can `--draft` complete in <30s? (excluding LLM call)
6. **SC-002 compliance**: Can `publish_approved()` complete in <60s?
7. **Rate limiting**: Is `_count_today_posts()` O(n) on log file? Acceptable for current scale?
8. **Memory**: Any unbounded data structures or memory leaks?
9. **Cron overhead**: Does `check_pending_approvals()` scan efficiently?
10. **LLM call**: Is the Anthropic API call async-safe? (It uses sync `client.messages.create`)

### Spec SCs to verify against:
- SC-001: Draft created in <30 seconds (excluding LLM)
- SC-002: Approved post published in <60 seconds
- SC-005: Cron processes pending approvals within 15 minutes
- SC-006: `setup_cron.sh` runs in <5 seconds

### Output format:
Produce a performance report with:
- **BOTTLENECK**: Code paths that could exceed spec timings
- **RISK**: Patterns that degrade under load
- **OPTIMIZATION**: Quick wins (with code snippets where applicable)
- **PASS**: Items meeting performance requirements
- **Timing estimates** for the critical path (draft workflow, publish workflow)

Write your findings to: `history/reports/performance-review-linkedin-2026-03-09.md`

## Response snapshot

Full performance audit completed. Two bottlenecks identified:

**B-001 (HIGH):** `_draft_post_content()` in `linkedin_poster.py:131` calls `anthropic.Anthropic().messages.create()` — a synchronous blocking call inside an `async def`. This blocks the event loop for the LLM round-trip (3–15s). Fix: switch to `AsyncAnthropic` and `await client.messages.create(...)`.

**B-002 (MEDIUM):** `_refresh_token()` in `auth.py:65` uses synchronous `httpx.post()` inside the call chain that flows through `get_access_token()` into async functions. Blocks event loop for up to 15s during token refresh. Fix: make async and use `httpx.AsyncClient`.

All spec SCs pass:
- SC-001: non-LLM draft path ~205ms (limit 30s)
- SC-002: publish path ~1s normal, ~25s worst case (limit 60s)
- SC-005: pending scan completes in <1s (limit 15min)
- SC-006: setup_cron.sh ~100ms (limit 5s)

HTTP timeouts verified: post=30s, profile=15s, health=5s — all correct. Credential caching is a proper module-level singleton with no disk reads after warm-up. `atomic_write` is efficient (tempfile + os.replace). Vault scans are bounded by glob filters. `_count_today_posts()` is O(n) on JSONL but acceptable for years at current posting rate.

## Outcome

- Impact: Performance audit documented with 2 bottlenecks, 4 risks, 4 optimizations, and 12 passing items
- Tests: none run (audit/review task)
- Files: history/reports/performance-review-linkedin-2026-03-09.md created
- Next prompts: Fix B-001 (AsyncAnthropic), Fix B-002 (async token refresh)
- Reflection: The synchronous-in-async pattern (both Anthropic SDK and httpx refresh) is a common gotcha when migrating sync code into async workflows. The current single-event-loop CLI usage masks the issue but would surface in any concurrent orchestrator environment.

## Evaluation notes (flywheel)

- Failure modes observed: None — audit task completed cleanly
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add `AsyncAnthropic` and verify LLM call becomes non-blocking with a simple asyncio test
