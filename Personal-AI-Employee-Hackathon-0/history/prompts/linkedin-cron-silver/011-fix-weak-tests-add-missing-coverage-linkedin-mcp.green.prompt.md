---
id: 011
title: Fix Weak Tests and Add Missing Coverage to LinkedIn MCP
stage: green
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: fix weak tests and add missing coverage to tests/unit/test_linkedin_mcp.py
labels: ["testing", "linkedin-mcp", "coverage", "401-retry", "auth", "health-check"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: null
  adr: history/adr/0014-linkedin-oauth2-token-lifecycle.md
  pr: null
files:
  - tests/unit/test_linkedin_mcp.py
tests:
  - test_post_update_auto_refresh_on_401 (replaced — now tests both 401-error and 401-then-success paths)
  - test_health_check_all_healthy (strengthened — asserts token_expires_in_seconds present and > 0)
  - test_health_check_token_near_expiry (new — verifies server behavior when credentials return near-expiry ts)
  - test_client_post_to_linkedin_401_triggers_refresh_and_retry (new — verifies HTTP-level retry in client.py)
  - test_client_post_to_linkedin_401_retry_also_fails (new — verifies LinkedInAPIError raised when both attempts 401)
  - test_client_get_profile_401_triggers_refresh_and_retry (new — same retry pattern for get_profile)
  - test_client_health_check_returns_true_on_200 (new — explicit 200 path)
  - test_client_health_check_returns_true_on_401 (new — 401 is reachable per health_check_api contract)
  - test_auth_is_expired_true (new — token already past expiry)
  - test_auth_is_expired_within_buffer_true (new — token within 300s default buffer)
  - test_auth_is_expired_false (new — token has > 300s remaining)
  - test_auth_is_expired_custom_buffer (new — verifies buffer_seconds parameter)
---

## Prompt

You are a test engineer for the H0 Personal AI Employee project. Fix weak tests and add missing coverage to `tests/unit/test_linkedin_mcp.py`.

**Working directory**: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`
**Target file**: `tests/unit/test_linkedin_mcp.py`

## Step 1: Read these files first
1. `tests/unit/test_linkedin_mcp.py` (existing tests)
2. `mcp_servers/linkedin/server.py` (what server.py exposes)
3. `mcp_servers/linkedin/client.py` (client functions to test)
4. `mcp_servers/linkedin/auth.py` (auth module)

## Step 2: Fix WEAK tests
[see weak test specs for test_post_update_auto_refresh_on_401 and test_health_check_all_healthy]

## Step 3: Add NEW tests for missing paths
[new tests for: health_check token_near_expiry, client 401 auto-refresh, auth._is_expired True/False]

## Step 4: Write the updated test file

## Response snapshot

Read all 4 source files before writing any tests. Key findings:

**server.py `post_update`**: Validates text via `PostUpdateInput` (Pydantic), then calls `post_to_linkedin`. Catches `AuthRequiredError`, `LinkedInAPIError`, and generic `Exception`. Returns `{"isError": True, "content": ...}` on any error. Does NOT have its own 401-retry logic — that lives in client.py.

**client.py `post_to_linkedin`**: HTTP-level 401 retry: if first POST returns 401, calls `reset_credentials_cache()`, re-fetches token, retries POST once. If retry also fails non-2xx, raises `LinkedInAPIError`. `get_profile()` has the same retry pattern.

**`health_check_api`**: Returns `True` for status codes 200 or 401 (401 means API is reachable but token expired). Returns `False` on any exception.

**server.py `health_check`**: `token_valid = True` when `get_linkedin_credentials()` returns without raising. `expires_in = max(0, int(creds.expires_at - time.time()))`. No near-expiry buffer in server.py — that buffer is in `auth._is_expired()`.

**auth.py `_is_expired`**: `time.time() >= (creds.expires_at - buffer_seconds)`. Default buffer is 300s. Custom buffer supported via parameter.

**Changes made:**

1. **`test_post_update_auto_refresh_on_401`** — replaced weak stub (which just asserted success on a successful mock) with two-case test: (a) `LinkedInAPIError(401)` raised by client → server returns `isError` with 401/auth in content; (b) client handles 401 internally and returns success → server returns `success=True`.

2. **`test_health_check_all_healthy`** — added assertion: `"token_expires_in_seconds" in data` and `data["token_expires_in_seconds"] > 0`.

3. **`test_health_check_token_near_expiry`** (new) — mocks `get_linkedin_credentials()` returning credentials with `expires_at = time.time() + 60`. Since server.py trusts whatever `get_linkedin_credentials()` returns, `token_valid=True`. Asserts response is a valid dict, `token_valid=True`, `token_expires_in_seconds >= 0`, `healthy=True`.

4. **`test_client_post_to_linkedin_401_triggers_refresh_and_retry`** (new) — uses a stateful `mock_post` that returns 401 on first call and 201 on second. Patches `reset_credentials_cache`. Asserts: result has correct `post_id`, `reset_credentials_cache` called once, HTTP POST called twice.

5. **`test_client_post_to_linkedin_401_retry_also_fails`** (new) — both calls return 401. Asserts `LinkedInAPIError(401)` raised.

6. **`test_client_get_profile_401_triggers_refresh_and_retry`** (new) — same retry pattern for `get_profile()`.

7. **`test_client_health_check_returns_true_on_200`** (new) — 200 response → `True`.

8. **`test_client_health_check_returns_true_on_401`** (new) — 401 response → `True` (per health_check_api contract: `status_code in (200, 401)`).

9. **`test_auth_is_expired_true`** (new) — `expires_at = now - 1` → `True`.

10. **`test_auth_is_expired_within_buffer_true`** (new) — `expires_at = now + 60` (within 300s buffer) → `True`.

11. **`test_auth_is_expired_false`** (new) — `expires_at = now + 3600` → `False`.

12. **`test_auth_is_expired_custom_buffer`** (new) — `expires_at = now + 400`: False with 300s buffer, True with 600s buffer.

## Outcome

- Impact: Replaced 1 misleadingly-named weak test and strengthened 1 partial assertion; added 10 new tests covering 401 retry paths, health_check near-expiry, _is_expired boundary conditions, and health_check_api status codes.
- Tests: 12 tests changed/added across server, client, and auth layers.
- Files: tests/unit/test_linkedin_mcp.py — complete rewrite preserving all existing tests.
- Next prompts: run pytest to verify all 25+ tests pass; check coverage report.
- Reflection: Reading the actual source before writing assertions was critical — server.py health_check has no near-expiry buffer (it trusts auth.py), and health_check_api considers 401 as "reachable". The old test_post_update_auto_refresh_on_401 didn't test 401 at all.

## Evaluation notes (flywheel)

- Failure modes observed: Original weak test was a copy-paste of the success test with a different name — it passed trivially and provided no regression coverage for the 401 path.
- Graders run and results (PASS/FAIL): Syntax check PASS (python3 -m py_compile)
- Prompt variant (if applicable): null
- Next experiment: Run full pytest suite to validate all mocks resolve correctly against the actual httpx.AsyncClient context manager pattern.
