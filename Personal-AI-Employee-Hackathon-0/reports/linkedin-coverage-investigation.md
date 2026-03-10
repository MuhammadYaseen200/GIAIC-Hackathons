# LinkedIn Module Coverage Investigation Report

**Date**: 2026-03-10
**Investigator**: linkedin-coverage-team (Research Agent)
**Scope**: orchestrator/linkedin_poster.py, mcp_servers/linkedin/auth.py, mcp_servers/linkedin/server.py

---

## Executive Summary

This report identifies **3 trivial items**, **6 HIGH-Risk untested paths**, and **7 weak tests** across the LinkedIn module. Tests exist but have significant gaps in coverage and behavioral verification.

---

## Part 1: orchestrator/linkedin_poster.py — Missing Line Analysis

### Project Root Guard (Lines 32-33)

**Function**: Project root validation (module-level guard)
**Code Path**: Checks if `PROJECT_ROOT` matches required directory; exits if not
**Risk Level**: **HIGH**
**Why Not Covered**:
- Test environment initializes the module normally, so this guard never triggers
- Would require intentionally running from wrong directory or mocking `Path.resolve()` to trigger
- No test verifies the exit behavior

---

### Load Topics (Lines 93-104)

**Function**: `_count_today_posts()` — JSONL parsing loop
**Code Path**:
- Line 93-94: Returns 0 if POSTS_JSONL doesn't exist
- Line 97-103: Loop through lines, parse JSON, count published posts by date
- Line 102-103: `json.JSONDecodeError` exception handling — skip malformed lines

**Risk Level**: **HIGH**
**Why Not Covered**:
- Tests mock `_count_today_posts()` directly; never call the real function
- Real function's JSON parsing and error handling never tested
- Malformed JSONL entry (e.g., `{"invalid json}`) would skip silently — untested behavior

---

### _load_topics() — Default Return (Lines 109-118)

**Function**: `_load_topics()`
**Code Path**:
- Line 109-111: If TOPICS_FILE missing, log warning + return fallback topic
- Line 114-117: Parse markdown bullets, filter non-empty + non-comment lines
- Line 118: Return fallback if topics list is empty after parsing

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- `_load_topics()` is mocked in tests (`run_auto_mode`)
- Edge case: topics file with ONLY comment lines or empty lines would trigger fallback — untested
- No test verifies fallback content or logging

---

### draft_post_content() — LLM Response (Lines 123-138)

**Function**: `_draft_post_content(topic: str)`
**Code Path**:
- Line 132-137: Calls `client.messages.create()` with async client
- Line 138: Extracts `.content[0].text.strip()`

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- Mocked in tests; real async call never executed
- Edge case: response with no `.content[0]` or empty `.text` — untested
- Timeouts or network errors not tested at this layer

---

### _send_hitl_notification() — WhatsApp Send (Lines 143-158)

**Function**: `_send_hitl_notification()`
**Code Path**:
- Line 143: Truncates preview to 300 chars
- Line 144: Extracts short ID (last 12 chars)
- Line 157-158: Creates GoBridge and sends message

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- Mocked in `test_draft_workflow_creates_vault_file`
- Real WhatsApp send never tested
- Exception handling in line 257-259 is tested, but the success path is mocked

---

### _move_to_rejected() (Lines 187-189)

**Function**: `_move_to_rejected(draft_path: Path)`
**Code Path**:
- Line 187: Creates VAULT_REJECTED directory
- Line 189: Renames file from source to destination

**Risk Level**: **LOW**
**Why Not Covered**:
- File move is mocked; real rename never tested
- Edge case: destination file already exists (`.rename()` would fail) — untested

---

### _call_post_update() (Line 194)

**Function**: `_call_post_update(post_text: str)`
**Code Path**:
- Single line: delegates to `post_to_linkedin(post_text, "PUBLIC")`

**Risk Level**: **LOW**
**Why Not Covered**:
- Mocked as `AsyncMock` in tests
- No test verifies the "PUBLIC" hardcoding

---

### publish_approved() — Frontmatter Parsing (Lines 258-259)

**Function**: `publish_approved(draft_path: Path)`
**Code Path**:
- Line 258: Error logging when WhatsApp notification fails
- Line 259: Logs draft path but continues (non-fatal)

**Risk Level**: **LOW**
**Why Not Covered**:
- WhatsApp failure is mocked; no test triggers real exception
- See `draft_and_notify()` lines 256-259 for actual code

---

### Frontmatter Parsing — Topic Extraction (Line 339)

**Function**: `check_pending_approvals()`
**Code Path**:
- Line 338: `if len(parts) < 2: continue`
- Line 339-349: Parses frontmatter to extract status + expires_at

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- Tests create valid vault files with proper frontmatter
- Edge case: file with no frontmatter (no `---` separator) — line 338 catches, but no test
- Malformed expires_at value (line 347-349) — ValueError handling tested implicitly

---

### check_pending_approvals() — Expiry Logic (Line 348-349)

**Function**: `check_pending_approvals()`
**Code Path**:
- Line 348: Try to parse expires_at as float
- Line 349: ValueError silently continues if parse fails

**Risk Level**: **LOW**
**Why Not Covered**:
- Tests use valid float timestamps
- Edge case: expires_at="not_a_number" — silently skipped, no test verifies this

---

### process_linkedin_vault_triggers() — Missing Topic Default (Line 380)

**Function**: `process_linkedin_vault_triggers()`
**Code Path**:
- Line 379: `if not needs_action_dir.exists(): return`
- Line 388: `if len(parts) < 2: continue` — skip files without frontmatter

**Risk Level**: **LOW**
**Why Not Covered**:
- Tests create valid directories
- Edge case: non-existent needs_action_dir — line 379 guards, but no test

---

### process_linkedin_vault_triggers() — Frontmatter Parsing (Lines 389)

**Function**: `process_linkedin_vault_triggers()`
**Code Path**:
- Line 388-389: Skips files without valid YAML frontmatter
- Line 411-412: Default topic to "LinkedIn post" if empty

**Risk Level**: **LOW**
**Why Not Covered**:
- Tests verify both cases (type=linkedin_post and #linkedin tag)
- Edge case: file with no topic field — line 412 provides default, tested implicitly

---

### Exception Handling in Loop (Lines 422-423)

**Function**: `process_linkedin_vault_triggers()`
**Code Path**:
- Line 422-423: Catches all exceptions in the trigger processing loop
- Logs error with full traceback, continues to next file

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- No test deliberately raises an exception during trigger processing
- Behavior: error logged, processing continues — untested

---

### run_auto_mode() & main() (Lines 439-453, 457)

**Function**: `run_auto_mode()` and `main()`
**Code Path**:
- Line 428-431: `run_auto_mode()` loads topics, picks random, drafts
- Line 438-453: `main()` parses CLI args, dispatches to functions
- Line 456-457: `if __name__ == "__main__"` entry point

**Risk Level**: **LOW-MEDIUM**
**Why Not Covered**:
- `main()` not called in any unit test
- `if __name__ == "__main__"` never executes in test environment
- CLI argument parsing not tested

---

## Part 2: mcp_servers/linkedin/auth.py — Missing Line Analysis

### _refresh_token() — HTTP Request (Lines 65-85)

**Function**: `_refresh_token(creds: LinkedInCredentials)`
**Code Path**:
- Line 65-74: Constructs POST request to LinkedIn OAuth endpoint
- Line 75: `resp.raise_for_status()` — raises on non-2xx
- Line 76-82: Parses response JSON, creates new credentials
- Line 83-84: Saves token file, logs success

**Risk Level**: **HIGH**
**Why Not Covered**:
- Tests mock `httpx.post()` or test only the non-refresh paths
- Real HTTP request never made in tests
- Retry logic at HTTP level not tested
- Malformed response JSON (missing "access_token" key) not tested

---

### get_access_token() & get_person_urn() (Lines 94-95)

**Function**: `get_access_token()` and `get_person_urn()`
**Code Path**:
- Line 105-107: `get_access_token()` — single-line wrapper, returns `get_linkedin_credentials().access_token`
- Line 110-119: `get_person_urn()` — checks creds URN + env fallback, raises if not set

**Risk Level**: **LOW**
**Why Not Covered**:
- Both are wrappers tested indirectly via their dependencies
- `get_access_token()` used in client.py and tested via integration
- `get_person_urn()` has dedicated tests (test_auth_get_person_urn_from_creds, test_auth_get_person_urn_raises_if_missing)

---

## Part 3: mcp_servers/linkedin/server.py — Missing Line Analysis

### post_update() — Error Handler (Lines 58-60)

**Function**: `post_update(text: str, visibility: str = "PUBLIC")`
**Code Path**:
- Line 58-60: Generic exception handler (not LinkedInAPIError, not AuthRequiredError)
- Catches unexpected errors, logs, returns error dict

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- Tests cover LinkedInAPIError and AuthRequiredError
- Generic exception path (e.g., AttributeError in result parsing) not tested
- Test line 59 logs `exc_info=True` but no test verifies logging

---

### get_profile() — Error Handler (Lines 84-86)

**Function**: `get_profile()`
**Code Path**:
- Line 84-86: Generic exception handler
- Same pattern as post_update

**Risk Level**: **MEDIUM**
**Why Not Covered**:
- Same as above; generic exception not tested

---

### health_check() — Triple Exception Path (Lines 105-106)

**Function**: `health_check()`
**Code Path**:
- Line 103-106: Try to call `health_check_api()`, catch Exception
- Line 105: Sets api_reachable = False on any exception

**Risk Level**: **LOW**
**Why Not Covered**:
- Test `test_health_check_graceful_on_network_error` verifies this path
- All exceptions collapse to `api_reachable=False` — tested

---

### health_check() — Logging (Line 122)

**Function**: Module entry point
**Code Path**:
- Line 122: `mcp.run()` — starts FastMCP server

**Risk Level**: **LOW**
**Why Not Covered**:
- Not unit-testable; requires MCP runtime

---

## Part 4: Trivial Items (3 Found)

### 1. Deprecated datetime.utcnow() — Lines 79, 167

**File**: orchestrator/linkedin_poster.py
**Lines**: 79, 167
**Issue**: `datetime.utcnow()` is deprecated (Python 3.12+); should use `datetime.now(timezone.utc)`
**Fix**:
```python
# Line 79: OLD
"ts": datetime.utcnow().isoformat() + "Z",

# NEW
"ts": datetime.now(timezone.utc).isoformat() + "Z",

# Line 167: OLD
ts = datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")

# NEW
ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%S")
```

### 2. Deprecated datetime.utcnow() — Line 178

**File**: orchestrator/linkedin_poster.py
**Line**: 178
**Issue**: Same deprecation
**Fix**:
```python
# OLD
"expires_at": datetime.utcnow().timestamp() + 86400,

# NEW
"expires_at": datetime.now(timezone.utc).timestamp() + 86400,
```

### 3. Unused Import

**File**: mcp_servers/linkedin/server.py or auth.py
**Issue**: Possible unused imports (minor)
**Status**: Low priority

---

## Part 5: HIGH-Risk Untested Paths (6 Found)

### Risk #1: JSON Parsing Failure in _count_today_posts()

**File**: orchestrator/linkedin_poster.py, lines 97-103
**Function**: `_count_today_posts()`
**Code**:
```python
for line in POSTS_JSONL.read_text().splitlines():
    try:
        entry = json.loads(line)
        if entry.get("status") == "published" and entry.get("ts", "").startswith(today):
            count += 1
    except json.JSONDecodeError:
        continue  # ← UNTESTED: Malformed JSONL silently skipped
```

**Scenario**: POSTS_JSONL contains malformed JSON (e.g., `{"status": "published"`).
**Expected**: Silently skip the line, continue counting.
**Risk**: If JSONL corruption occurs in production, count would be wrong without warning.
**Test Coverage**: 0%
**Mitigation**: Add test with intentionally malformed JSONL line.

---

### Risk #2: OAuth Token Refresh HTTP Call

**File**: mcp_servers/linkedin/auth.py, lines 65-75
**Function**: `_refresh_token()`
**Code**:
```python
resp = httpx.post(
    REFRESH_URL,
    data={...},
    timeout=15.0,
)
resp.raise_for_status()  # ← UNTESTED: Real HTTP call never made
```

**Scenario**: Token refresh fails (network error, LinkedIn returns 500, timeout).
**Expected**: httpx exception or LinkedInAPIError.
**Risk**: Token refresh never tested end-to-end; production failure mode unknown.
**Test Coverage**: 0% (only auth-required and no-refresh-token paths tested)
**Mitigation**: Add integration test with real OAuth endpoint or mock httpx more thoroughly.

---

### Risk #3: Frontmatter Parsing Without YAML Library

**File**: orchestrator/linkedin_poster.py, lines 276-284
**Function**: `publish_approved()`
**Code**:
```python
parts = content.split("---", 2)
post_text = parts[2].strip() if len(parts) >= 3 else content.strip()
...
for line in (parts[1].splitlines() if len(parts) >= 3 else []):
    if line.startswith("topic:"):
        topic = line.split(":", 1)[1].strip()  # ← UNTESTED: Raw string parsing
        break
```

**Scenario**: Vault file has malformed YAML (e.g., `topic: "value with : colons"`).
**Expected**: Partial/incorrect topic extraction.
**Risk**: No YAML library used; raw string parsing fragile.
**Test Coverage**: Tests create valid frontmatter; edge cases untested.
**Mitigation**: Use `yaml.safe_load()` consistently (as done in test fixtures).

---

### Risk #4: Exception in process_linkedin_vault_triggers() Loop

**File**: orchestrator/linkedin_poster.py, lines 422-423
**Function**: `process_linkedin_vault_triggers()`
**Code**:
```python
for path in sorted(needs_action_dir.glob("*.md")):
    try:
        ...
    except Exception as e:
        logger.error(f"Error processing linkedin vault trigger {path.name}: {e}", exc_info=True)
        # ← UNTESTED: Exception swallowed, processing continues
```

**Scenario**: A trigger file causes an unexpected exception (e.g., permission denied reading file).
**Expected**: Error logged, next file processed.
**Risk**: Silent failure mode; difficult to debug in production.
**Test Coverage**: 0% (no test deliberately raises exception)
**Mitigation**: Add test case that raises exception in trigger processing.

---

### Risk #5: WhatsApp Bridge Failure (Non-Fatal)

**File**: orchestrator/linkedin_poster.py, lines 256-259
**Function**: `draft_and_notify()`
**Code**:
```python
try:
    await _send_hitl_notification(topic, post_text, draft_path, draft_id)
except Exception as e:
    logger.error(f"WhatsApp notification failed: {e}. Draft saved at {draft_path}.")
    # ← Draft continues despite notification failure
```

**Scenario**: GoBridge.send() fails (WhatsApp API unreachable).
**Expected**: Draft saved, notification skipped, error logged.
**Risk**: User never notified of HITL approval needed; draft orphaned.
**Test Coverage**: Exception caught, but success-path (notification sent) is mocked.
**Mitigation**: Add test verifying notification failure doesn't delete draft.

---

### Risk #6: Rate Limit Check with Missing OWNER_WA

**File**: orchestrator/linkedin_poster.py, lines 224-233
**Function**: `draft_and_notify()`
**Code**:
```python
if today_count >= 1:
    ...
    if OWNER_WA:
        try:
            bridge = GoBridge()
            await bridge.send(OWNER_WA, f"LinkedIn rate limit...")  # ← Untested if OWNER_WA empty
        except Exception as e:
            logger.warning(f"WhatsApp rate-limit notice failed: {e}")
    _log_event("rate_limited", topic, "rate_limited")
```

**Scenario**: OWNER_WA env var not set (empty string).
**Expected**: Rate limit logged, no WhatsApp attempt.
**Risk**: If OWNER_WA missing, user gets no notification of rate limit.
**Test Coverage**: Tests set OWNER_WA; empty-string case untested.
**Mitigation**: Add test with OWNER_WA="" to verify fallback behavior.

---

## Part 6: Weak Tests (7 Found)

### Weak Test #1: test_draft_workflow_creates_vault_file

**File**: tests/unit/test_linkedin_poster.py, lines 18-47
**Problem**:
- Mocks `_draft_post_content`, `_send_hitl_notification`, `run_privacy_gate`, `_count_today_posts`
- Only verifies vault file exists; doesn't verify content (frontmatter, body)
- Doesn't verify `_send_hitl_notification` was actually called

**Assertion**: `assert len(files) == 1` — too weak, doesn't check content
**Better**:
```python
assert path.exists()
fm = yaml.safe_load(path.read_text().split("---", 2)[1])
assert fm["type"] == "linkedin_post"
assert fm["topic"] == "test topic"
assert fm["status"] == "pending_approval"
content = path.read_text()
assert "AI is transforming development..." in content
```

---

### Weak Test #2: test_privacy_gate_blocks_topic

**File**: tests/unit/test_linkedin_poster.py, lines 50-58
**Problem**:
- Only checks result["status"] == "privacy_blocked"
- Doesn't verify no vault file was created
- Doesn't verify _log_event was called

**Assertion**: `assert result["status"] == "privacy_blocked"` — incomplete
**Better**:
```python
assert result["status"] == "privacy_blocked"
assert result["reason"] == "topic_blocked"
assert not (VAULT_PENDING / "*.md").glob("*")  # No files created
```

---

### Weak Test #3: test_rate_limit_queues_for_tomorrow

**File**: tests/unit/test_linkedin_poster.py, lines 62-70
**Problem**:
- Only checks status
- Doesn't verify no vault file, no LLM draft called, rate limit notification sent

**Assertion**: `assert result["status"] == "rate_limited"` — incomplete
**Better**:
```python
assert result["status"] == "rate_limited"
# Verify WhatsApp notification was sent (if OWNER_WA set)
# Verify _log_event called with correct status
```

---

### Weak Test #4: test_publish_approved_post

**File**: tests/unit/test_linkedin_poster.py, lines 74-92
**Problem**:
- Mocks too heavily: `_call_post_update`, `_log_event`, `update_frontmatter`, `move_to_done`
- Only checks that `move_to_done` was called once
- Doesn't verify frontmatter was updated with post_id

**Assertion**: `mock_move_done.assert_called_once()` — checks wrong thing
**Better**:
```python
# Verify update_frontmatter was called with post_id
assert mock_fm.call_args[0][1]["status"] == "published"
assert mock_fm.call_args[0][1]["linkedin_post_id"] == "urn:li:share:123"
# Verify move_to_done called
assert mock_move_done.assert_called_once()
```

---

### Weak Test #5: test_auto_mode_picks_random_topic

**File**: tests/unit/test_linkedin_poster.py, lines 113-129
**Problem**:
- Mocks `_load_topics` and `draft_and_notify`
- Only checks that `draft_and_notify` was called
- Doesn't verify it was called with one of the provided topics

**Assertion**: `assert topic_used in [...]` — weak logic, doesn't test topic selection
**Better**:
```python
# Mock random.choice to return predictable value
with patch("random.choice", return_value="Topic A"):
    await run_auto_mode()
    mock_draft.assert_called_once_with("Topic A")
```

---

### Weak Test #6: test_vault_item_type_linkedin_triggers_draft

**File**: tests/unit/test_linkedin_poster.py, lines 152-184
**Problem**:
- Only checks that LinkedIn trigger was moved to Done
- Doesn't verify non-matching item stayed in Needs_Action
- Doesn't verify topic was extracted correctly

**Assertion**: Multiple path checks — better, but doesn't verify topic extraction
**Better**:
```python
# Verify draft_and_notify was called with exact topic
mock_draft.assert_called_once_with("milestone reached")
# Verify event logged
mock_log.assert_called()
```

---

### Weak Test #7: test_auth_get_credentials_singleton

**File**: tests/unit/test_linkedin_mcp.py, lines 323-342
**Problem**:
- Only checks `c1 is c2` (object identity)
- Doesn't verify that token file is NOT re-read
- Doesn't verify that modified token file is ignored until cache reset

**Assertion**: `assert c1 is c2` — checks object identity only
**Better**:
```python
c1 = auth_mod.get_linkedin_credentials()
# Modify token file
token_file.write_text(json.dumps({...new token...}))
c2 = auth_mod.get_linkedin_credentials()
# Should still get c1's token (cached), not the new file
assert c1 is c2
assert c2.access_token == "singleton_token"
# Reset cache
auth_mod.reset_credentials_cache()
c3 = auth_mod.get_linkedin_credentials()
# Now should get new token
assert c3.access_token != "singleton_token"
```

---

## Part 7: Module-Level Constants & Test Patching

### Constant: VAULT_PENDING

**Location**: orchestrator/linkedin_poster.py, line 60
**Usage**:
- `_write_draft_vault_file()` — writes vault file here
- `check_pending_approvals()` — reads from here
- All tests that create vault files

**Test Patching**: ✅ Tests patch this constant
**Example**: `patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path / "Pending_Approval")`
**Coverage**: Good — tests isolate this from real vault

---

### Constant: POSTS_JSONL

**Location**: orchestrator/linkedin_poster.py, line 65
**Usage**:
- `_log_event()` — appends to this file
- `_count_today_posts()` — reads from this file

**Test Patching**: ⚠️ Partially patched
**Issue**: Tests don't directly patch POSTS_JSONL; instead mock `_count_today_posts()`
**Coverage**: Weak — real JSONL write/read logic untested
**Risk**: Malformed JSONL or file corruption scenario untested

---

### Constant: TOPICS_FILE

**Location**: orchestrator/linkedin_poster.py, line 64
**Usage**: `_load_topics()` reads markdown topics from here

**Test Patching**: ⚠️ Mocked indirectly
**Issue**: Tests mock `_load_topics()` in `run_auto_mode()`; actual file parsing untested
**Coverage**: Weak — fallback topic and empty-topics cases untested

---

### Constant: OWNER_WA

**Location**: orchestrator/linkedin_poster.py, line 66
**Usage**:
- `_send_hitl_notification()` — recipient for WhatsApp
- `draft_and_notify()` — rate limit notification

**Test Patching**: ✅ Set via monkeypatch
**Example**: `monkeypatch.setenv("OWNER_WHATSAPP_NUMBER", "+921234567890")`
**Coverage**: Good — tests set this, but empty-string case untested

---

### Constant: VAULT_REJECTED

**Location**: orchestrator/linkedin_poster.py, line 62
**Usage**: `_move_to_rejected()` — destination for rejected drafts

**Test Patching**: ⚠️ Created via `_ensure_dirs()` but not patched in tests
**Issue**: Tests mock the actual move operation; VAULT_REJECTED logic untested
**Coverage**: Weak — file move to rejected never tested end-to-end

---

## Part 8: Summary of Findings

### Coverage Metrics

| Category | Count | Status |
|----------|-------|--------|
| **Trivial Items** (deprecations) | 3 | ⚠️ Low priority |
| **HIGH-Risk Untested Paths** | 6 | 🔴 Critical |
| **Weak Tests** (mock too much) | 7 | 🟡 Medium priority |
| **Total Missing Coverage** | ~16 major issues | Needs fixing |

---

### Recommended Remediation (Priority Order)

#### 🔴 CRITICAL (HIGH-Risk Paths)

1. **Risk #1 & #2**: Add real HTTP/JSONL tests
   - Test malformed JSONL in `_count_today_posts()`
   - Test OAuth token refresh with mock httpx responses

2. **Risk #3**: Use YAML library for frontmatter
   - Replace string parsing in `publish_approved()` with `yaml.safe_load()`

3. **Risk #4 & #6**: Add exception handling tests
   - Test exception in trigger loop
   - Test missing OWNER_WA environment variable

4. **Risk #5**: Add WhatsApp failure test
   - Verify draft is saved despite notification failure

#### 🟡 MEDIUM (Weak Tests)

5. **Tests 1-3**: Strengthen vault file assertions
   - Verify frontmatter content (not just existence)
   - Verify no orphaned drafts on privacy gate block

6. **Tests 4-6**: Add mock call verification
   - Verify functions were called with correct arguments
   - Verify logging calls

7. **Test 7**: Add cache invalidation test
   - Test that reset_credentials_cache() truly reloads

#### ⚠️ LOW (Trivial)

8. **Deprecations**: Replace `datetime.utcnow()` with `datetime.now(timezone.utc)`

---

## Appendix: Module Dependency Map

```
orchestrator/linkedin_poster.py
├── mcp_servers/linkedin/auth.py (AuthRequiredError)
├── mcp_servers/linkedin/client.py (post_to_linkedin, LinkedInAPIError)
├── mcp_servers/whatsapp/bridge.py (GoBridge)
├── orchestrator/hitl_manager.py (_generate_draft_id)
├── orchestrator/vault_ops.py (move_to_done, update_frontmatter)
├── watchers/privacy_gate.py (run_privacy_gate)
└── watchers/utils.py (atomic_write, render_yaml_frontmatter, sanitize_filename)

mcp_servers/linkedin/auth.py
├── mcp_servers/linkedin/models.py (LinkedInCredentials)
└── watchers/utils.py (atomic_write)

mcp_servers/linkedin/server.py
├── mcp_servers/linkedin/auth.py (get_linkedin_credentials, AuthRequiredError)
├── mcp_servers/linkedin/client.py (post_to_linkedin, get_profile, health_check_api)
└── mcp_servers/linkedin/models.py (all models)
```

---

## Conclusion

The LinkedIn module has **good architectural patterns** (HITL approval, rate limiting, error handling) but **significant test coverage gaps**:

1. Real HTTP, file I/O, and exception paths are mocked away
2. Tests verify happy paths but miss edge cases (malformed data, missing env vars, network failures)
3. Weak assertions allow bugs to pass silently

**Priority**: Fix HIGH-Risk paths #1, #2, #4, #5, #6 before production use.
