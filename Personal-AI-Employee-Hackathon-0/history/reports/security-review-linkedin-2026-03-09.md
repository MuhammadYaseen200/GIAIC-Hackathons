# Security Review: LinkedIn Auto-Poster (Phase 5.5)

**Date:** 2026-03-09
**Reviewer:** Security Audit Agent
**Branch:** 009-linkedin-cron-silver
**Scope:** `mcp_servers/linkedin/`, `orchestrator/linkedin_poster.py`, `scripts/linkedin_auth.py`, `.gitignore`, `mcp_servers/linkedin/models.py`

---

## Executive Summary

The LinkedIn Auto-Poster implementation demonstrates a generally solid security posture for a single-user personal automation tool. Credentials are never hardcoded, token storage is excluded from git, and HITL enforcement is implemented correctly. Two medium-severity issues are identified along with one low-severity observation. No critical or high-severity vulnerabilities were found.

**Overall Security Grade: B+**

---

## Findings

---

### PASS — No Hardcoded Credentials

**Files:** `mcp_servers/linkedin/auth.py`, `scripts/linkedin_auth.py`

All OAuth2 credentials are loaded exclusively from environment variables:

```python
# auth.py:60-61
client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
```

```python
# scripts/linkedin_auth.py:58-59
client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
```

No hardcoded API keys, tokens, or secrets were found anywhere in the LinkedIn module files. The `.env` file is correctly excluded from git via `.gitignore` line 2.

---

### PASS — Token Storage Excluded from Git

**File:** `.gitignore` line 7

```
linkedin_token.json
```

`linkedin_token.json` is explicitly listed in `.gitignore` under the `# Secrets - NEVER commit` section. Additional token files (`token.json`, `calendar_token.json`, `credentials.json`) are also excluded. The `.env` and `.env.*` patterns cover environment secrets.

---

### PASS — AuthRequiredError Raised (Not Silently Logged) on Missing Token

**File:** `mcp_servers/linkedin/auth.py` lines 34-41

```python
def _load_token_file() -> LinkedInCredentials:
    if not TOKEN_FILE.exists():
        raise AuthRequiredError(
            f"linkedin_token.json not found at {TOKEN_FILE}. "
            "Run: python3 scripts/linkedin_auth.py"
        )
```

When the token file is missing, `AuthRequiredError` is raised immediately with actionable guidance. It is not silently swallowed or merely logged. The `_refresh_token` function also raises `AuthRequiredError` (not logs) when `LINKEDIN_CLIENT_ID` or `LINKEDIN_CLIENT_SECRET` are absent (lines 62-63).

---

### PASS — No Token Values in Log Statements

**Files:** `mcp_servers/linkedin/auth.py`, `mcp_servers/linkedin/client.py`

The three log statements involving token operations contain no token values:

```python
# auth.py:84
logger.info("LinkedIn token refreshed successfully.")

# auth.py:94
logger.info("LinkedIn token near expiry — refreshing.")

# client.py:60
logger.info("LinkedIn 401 — forcing token refresh and retrying.")
```

The `scripts/linkedin_auth.py` terminal output (line 143) correctly masks the refresh token value with `'PRESENT' if refresh_token else 'MISSING'` rather than printing the actual token.

---

### PASS — Input Validation on PostUpdateInput

**File:** `mcp_servers/linkedin/models.py` lines 8-10

```python
class PostUpdateInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=3000, description="Post text content")
    visibility: Literal["PUBLIC", "CONNECTIONS"] = Field("PUBLIC", description="Post visibility")
```

`text` is constrained between 1 and 3000 characters (LinkedIn's API limit is 3000 characters). `visibility` is constrained via `Literal` to only two valid values, preventing injection of arbitrary visibility strings. The `server.py` MCP tool correctly validates input before passing to the API client (lines 39-42).

---

### PASS — HITL Enforcement: publish_approved() Only Called After status=approved

**File:** `orchestrator/linkedin_poster.py` lines 320-349

The `check_pending_approvals()` scanner reads vault frontmatter and enforces a hard status gate:

```python
if status == "approved":
    await publish_approved(draft_path)
elif status == "rejected":
    await handle_rejected(draft_path)
elif status == "pending_approval" and expires_at and time.time() > expires_at:
    # expiry path → rejected, NOT published
```

`publish_approved()` is never called directly from the auto or draft paths. The only call sites are `check_pending_approvals()` (line 344) and `--check` CLI entry point (line 445), both of which require the file's frontmatter `status` field to equal `"approved"`. There is no path that bypasses this gate.

---

### PASS — Privacy Gate on Both Topic AND Post Content

**File:** `orchestrator/linkedin_poster.py` lines 206-243

```python
# Step 1: Privacy gate on topic
topic_check = run_privacy_gate(topic, "text")
if topic_check.media_blocked:
    ...
    return {"status": "privacy_blocked", "reason": "topic_blocked"}

# Step 4: Privacy gate on drafted content
content_check = run_privacy_gate(post_text, "text")
if content_check.media_blocked:
    ...
    return {"status": "privacy_blocked", "reason": "content_blocked"}
```

`run_privacy_gate` is called twice in `draft_and_notify()`: once on the raw topic (before LLM call) and once on the LLM-generated post text (after drafting). Both gates must pass before the draft is written to the vault and HITL notification is sent.

---

### MEDIUM — OAuth2 State Parameter Not Verified (CSRF Risk in Auth Script)

**File:** `scripts/linkedin_auth.py` lines 64-71, 37-50
**Severity:** MEDIUM — fix in polish
**Risk:** CSRF attack during the one-time OAuth2 authorization flow

**Finding:** A CSRF `state` parameter is generated but never verified in the callback handler.

```python
# main(): state is generated and included in the authorization URL
state = os.urandom(16).hex()
auth_params = {
    ...
    "state": state,
}

# CallbackHandler.do_GET(): state is never checked against the generated value
if "code" in params:
    _auth_code = params["code"][0]   # ← state param ignored
```

The `CallbackHandler.do_GET()` method (lines 41-45) extracts only `code` from the callback query string; it does not verify that `params["state"][0] == state`.

**Practical Risk Level:** Low in practice. This is a one-time local OAuth flow run manually by the owner. The HTTP server binds to `localhost:8765` only, reducing attack surface significantly. An attacker would need to be able to make requests to `localhost:8765` on the developer machine during the 120-second auth window. However, it is a deviation from RFC 6749 Section 10.12.

**Recommendation:** In the callback handler, compare the returned `state` against the generated value and reject the request if they do not match.

---

### MEDIUM — vault/Pending_Approval Draft Files Not Excluded from Git

**File:** `.gitignore`
**Severity:** MEDIUM — fix in polish
**Risk:** Drafted LinkedIn post content (not yet approved) could be committed to the repository

**Finding:** The `.gitignore` excludes `vault/Approved/*.md` (line 25) and `vault/Rejected/*.md` (line 26), but does NOT exclude `vault/Pending_Approval/*.md` or `vault/Done/*.md`.

Drafted posts in `vault/Pending_Approval/` contain:
- The full post text generated by the LLM
- Topic and timestamp metadata in YAML frontmatter

Published posts moved to `vault/Done/` (via `move_to_done()`) contain the `linkedin_post_id` in their frontmatter.

While not credentials, committing draft content and post IDs could unintentionally expose post planning data or post history.

**Recommendation:** Add the following lines to `.gitignore`:
```
vault/Pending_Approval/*.md
vault/Done/*.md
```

---

### LOW — Token File Written Without Restricted File Permissions

**Files:** `scripts/linkedin_auth.py` line 139, `watchers/utils.py` `atomic_write()`
**Severity:** LOW — informational / defense-in-depth
**Risk:** `linkedin_token.json` is created with default OS file permissions (typically `0o644`) rather than owner-only permissions (`0o600`)

**Finding:** `scripts/linkedin_auth.py` writes the token file using `TOKEN_FILE.write_text(...)` (line 139) and `auth.py` uses `atomic_write()` from `watchers/utils.py`. Neither sets restrictive file permissions on the token file after writing.

```python
# scripts/linkedin_auth.py:139
TOKEN_FILE.write_text(json.dumps(token_obj, indent=2))
# No chmod call follows

# watchers/utils.py:atomic_write() — no chmod after os.replace()
```

On a shared or multi-user system, world-readable permissions (`0o644`) would allow other local users to read the access and refresh tokens.

**Practical Risk Level:** Very low for a personal single-user machine. On a shared Linux server, this would be higher severity.

**Recommendation:** After writing `linkedin_token.json`, set `0o600` permissions:
```python
TOKEN_FILE.chmod(0o600)
```

---

## Summary Table

| Check | Result | Severity | Notes |
|-------|--------|----------|-------|
| Hardcoded credentials | PASS | — | Env vars only |
| linkedin_token.json in .gitignore | PASS | — | Line 7 |
| AuthRequiredError raised on missing token | PASS | — | Not silently logged |
| Token values not in log statements | PASS | — | All log msgs safe |
| Input validation (PostUpdateInput) | PASS | — | min/max + Literal |
| HITL enforcement (approved gate) | PASS | — | Hard status gate in check_pending_approvals |
| Privacy gate on topic AND content | PASS | — | Two separate calls |
| OAuth2 state not verified (CSRF) | MEDIUM | Fix in polish | localhost-only scope reduces risk |
| vault/Pending_Approval not in .gitignore | MEDIUM | Fix in polish | Draft content exposed |
| Token file permissions (0o644 default) | LOW | Informational | Single-user machine risk only |

---

## Overall Security Grade: B+

**Rationale:** No critical or high-severity issues. Core security invariants are correctly implemented — no hardcoded secrets, proper token exclusion from git, correct HITL enforcement, safe logging, and solid input validation. The two medium findings are polish-tier improvements appropriate for production hardening; neither creates an immediate deployment blocker for a single-user personal automation tool. The OAuth state omission is a protocol deviation, and the missing gitignore entries are a data hygiene issue rather than a credential exposure risk.

---

*Review conducted 2026-03-09 by security-reviewer agent on branch 009-linkedin-cron-silver.*
