# Test Coverage Review: LinkedIn Auto-Poster (Phase 5.5)

**Date**: 2026-03-09
**Branch**: `009-linkedin-cron-silver`
**Reviewer**: Claude Sonnet 4.6 (automated coverage audit)
**Reported coverage**: 85.94%
**Spec requirement**: SC-008 — >80% coverage

---

## Files Under Review

### Test Files
- `tests/unit/test_linkedin_poster.py` — 9 test functions
- `tests/unit/test_linkedin_mcp.py` — 23 test functions (contract + auth + client)
- `tests/test_cron_scripts.sh` — bash smoke tests (5 assertions in WSL mode, 5 in native Linux mode)

### Source Files Audited
- `orchestrator/linkedin_poster.py` — 450 lines
- `mcp_servers/linkedin/server.py` — 123 lines
- `mcp_servers/linkedin/client.py` — 105 lines
- `mcp_servers/linkedin/auth.py` — 120 lines
- `mcp_servers/linkedin/models.py` — 43 lines

---

## TESTED: Code Paths with Adequate Coverage

### orchestrator/linkedin_poster.py

| Function | Tested Path | Test(s) |
|----------|-------------|---------|
| `draft_and_notify()` | Privacy gate blocks topic | `test_privacy_gate_blocks_topic` |
| `draft_and_notify()` | Rate limit (today_count >= 1) | `test_rate_limit_queues_for_tomorrow` |
| `draft_and_notify()` | Happy path: drafts, writes vault file | `test_draft_workflow_creates_vault_file` |
| `publish_approved()` | Success path: published, returns post_id | `test_publish_approved_post` |
| `publish_approved()` | LinkedInAPIError → api_error, draft preserved | `test_linkedin_api_error_graceful_degradation` |
| `handle_rejected()` | Happy path: moves file, logs rejected | `test_rejected_post_moves_to_rejected` |
| `run_auto_mode()` | Picks random topic from loaded topics | `test_auto_mode_picks_random_topic` |
| `process_linkedin_vault_triggers()` | type=linkedin_post → draft_and_notify called, file moved (T029) | `test_vault_item_type_linkedin_triggers_draft` |
| `process_linkedin_vault_triggers()` | #linkedin tag → same routing (T031) | `test_vault_item_hashtag_linkedin_triggers_draft` |

### mcp_servers/linkedin/server.py

| Tool | Tested Path | Test(s) |
|------|-------------|---------|
| `post_update()` | Success → returns post_id | `test_post_update_success` |
| `post_update()` | Empty text → validation error | `test_post_update_empty_text_rejected` |
| `post_update()` | Text > 3000 chars → validation error | `test_post_update_text_too_long_rejected` |
| `post_update()` | AuthRequiredError → isError | `test_post_update_auth_required` |
| `post_update()` | LinkedInAPIError → isError | `test_post_update_api_error` |
| `post_update()` | Auto-refresh path (mock) | `test_post_update_auto_refresh_on_401` |
| `get_profile()` | Success → person_urn built from id/sub | `test_get_profile_success` |
| `get_profile()` | AuthRequiredError → isError | `test_get_profile_auth_required` |
| `get_profile()` | LinkedInAPIError → isError | `test_get_profile_api_error` |
| `health_check()` | Healthy: token valid + API reachable | `test_health_check_all_healthy` |
| `health_check()` | API unreachable | `test_health_check_api_unreachable` |
| `health_check()` | No token → token_valid=False | `test_health_check_no_token` |
| `health_check()` | Catastrophic error → graceful | `test_health_check_graceful_on_network_error` |

### mcp_servers/linkedin/auth.py

| Function | Tested Path | Test(s) |
|----------|-------------|---------|
| `_load_token_file()` | File missing → AuthRequiredError | `test_auth_load_token_missing` |
| `_load_token_file()` | File present → returns credentials | `test_auth_load_token_present` |
| `_save_token_file()` | Writes JSON via atomic_write | `test_auth_save_token_file` |
| `get_linkedin_credentials()` | Singleton: returns same object | `test_auth_get_credentials_singleton` |
| `get_person_urn()` | Returns URN from token file | `test_auth_get_person_urn_from_creds` |
| `get_person_urn()` | No URN set → AuthRequiredError | `test_auth_get_person_urn_raises_if_missing` |
| `_refresh_token()` | No refresh_token → AuthRequiredError | `test_auth_refresh_no_refresh_token` |
| `_refresh_token()` | Missing env vars → AuthRequiredError | `test_auth_refresh_no_client_credentials` |

### mcp_servers/linkedin/client.py

| Function | Tested Path | Test(s) |
|----------|-------------|---------|
| `post_to_linkedin()` | 201 response → post_id from header | `test_client_post_to_linkedin_success` |
| `post_to_linkedin()` | 500 response → LinkedInAPIError | `test_client_post_to_linkedin_api_error` |
| `get_profile()` | 200 response → returns JSON | `test_client_get_profile_success` |
| `health_check_api()` | Network error → returns False | `test_client_health_check_network_error` |
| `LinkedInAPIError` | str representation | `test_linkedin_api_error_str` |

### tests/test_cron_scripts.sh (WSL mode)

- Syntax validation of `setup_cron.sh` and `remove_cron.sh`
- Presence of `H0_CRON_MANAGED` marker in setup script
- Directory guard (project path present)
- Idempotency logic (`grep -v H0_CRON_MANAGED` pattern)

---

## UNTESTED: Code Paths With No Tests (Ranked by Risk)

### Risk Level: HIGH

**1. `publish_approved()` — `AuthRequiredError` branch (lines 287-291)**
- The `except AuthRequiredError` block in `publish_approved()` is completely untested.
- There is a test for `LinkedInAPIError` but nothing for the auth error path.
- Risk: token expiry during the publish step is a realistic production scenario (SC-010), and the error handling (update frontmatter to `auth_error`, log event) could be broken silently.

**2. `publish_approved()` — file not found branch (lines 264-266)**
- The guard `if not draft_path.exists(): return {"status": "error", "reason": "file_not_found"}` has no test.
- The task list specifically lists this as an edge case to test.
- Risk: if the vault file is deleted between approval and processing, this silent error goes undetected.

**3. `draft_and_notify()` — LLM draft failure branch (lines 230-235)**
- The `except Exception` around `_draft_post_content()` returns `{"status": "error"}` but has no test.
- Risk: API key missing or Claude unavailable causes this path; the status key differs (`error` vs all other statuses) — callers may not handle it.

**4. `draft_and_notify()` — privacy gate on generated CONTENT (lines 238-242)**
- Step 4 of `draft_and_notify()` runs PrivacyGate on the LLM-generated post text (not just the topic). This branch (`content_check.media_blocked = True`) is not tested.
- The existing test `test_privacy_gate_blocks_topic` only tests blocking on the topic (Step 1). The content-gate path returns `{"status": "privacy_blocked", "reason": "content_blocked"}` and is a distinct branch.
- Spec SC-004 requires 100% PII blocking before approval. This gap undermines that guarantee.

**5. `check_pending_approvals()` — expiry path (lines 347-350)**
- The expiry logic (`status == "pending_approval" and expires_at and time.time() > expires_at`) is not tested.
- The specific scenario `test_check_pending_approvals_expires_draft` mentioned in the audit brief does NOT exist.
- Risk: expired drafts pile up in `vault/Pending_Approval/` indefinitely if this path is broken.

**6. `check_pending_approvals()` — approved/rejected file scan (lines 343-346)**
- The entire `check_pending_approvals()` function has no direct test. T027 wires it to the orchestrator, but there is no unit test for its scan loop.

### Risk Level: MEDIUM

**7. `_count_today_posts()` — file does not exist (line 92-93)**
- The `if not POSTS_JSONL.exists(): return 0` branch is not tested.
- The `test_count_today_posts_zero_when_no_file` scenario mentioned in the audit brief does NOT exist.
- Risk: low because the guard is trivially simple, but the spec mentions this as a testable case.

**8. `_count_today_posts()` — malformed JSON line (line 101-102)**
- The `except json.JSONDecodeError: continue` branch is not tested.
- Risk: if `linkedin_posts.jsonl` gets a corrupted line, the count silently skips it — acceptable behavior, but not verified.

**9. `_load_topics()` — topics file missing → fallback default (lines 108-110)**
- `_load_topics()` returns a fallback string `["AI agent development and automation"]` when the file is absent.
- The test `test_auto_mode_picks_random_topic` mocks `_load_topics()` entirely — it never calls the real function.
- The fallback-default branch (file missing) and the empty-list fallback (line 117: `return topics or [...]`) have no test that exercises the real `_load_topics()` code.

**10. `_load_topics()` — all lines are headers/blank (line 117)**
- If the topics file exists but contains only `# comment` lines, `topics` will be `[]` and the function returns `["AI learning and development"]`.
- This edge case has no test.

**11. `draft_and_notify()` — WhatsApp notification failure (non-fatal, lines 248-251)**
- The `except Exception` around `_send_hitl_notification()` logs an error but does not abort.
- There is no test confirming that a WhatsApp failure leaves the draft intact (the draft path exists and `status == "drafted"` is still returned).
- This is the "WhatsApp bridge offline" edge case from the spec.

**12. `_write_draft_vault_file()` — atomic_write failure**
- If `atomic_write()` raises (e.g., disk full, permission error), `_write_draft_vault_file()` has no try/except and will propagate the exception to `draft_and_notify()`, which also has no handler for a write failure.
- No test exercises this failure scenario.

**13. `process_linkedin_vault_triggers()` — no trigger files exist**
- When `needs_action_dir` is empty or contains no `.md` files, the function should return silently.
- No dedicated test for this empty-directory scenario.

**14. `process_linkedin_vault_triggers()` — trigger file has no `topic` field (line 403-404)**
- When `topic` is empty string, it falls back to `"LinkedIn post"`.
- No test exercises this fallback.

### Risk Level: LOW

**15. `client.py` — `post_to_linkedin()` 401 → auto-refresh → retry path (lines 58-63)**
- The 401 handling in the real HTTP client (`reset_credentials_cache()` + retry) is not tested at the `client.py` level.
- `test_post_update_auto_refresh_on_401` in `test_linkedin_mcp.py` mocks `post_to_linkedin()` wholesale — it never exercises the actual retry logic in `client.py`.

**16. `client.py` — `get_profile()` 401 → refresh → retry (lines 81-87)**
- Same issue as above — the 401-refresh-retry branch in `get_profile()` client is untested.

**17. `auth.py` — `get_linkedin_credentials()` triggers auto-refresh on near-expiry (lines 93-95)**
- The `_is_expired()` check inside `get_linkedin_credentials()` that triggers `_refresh_token()` is not exercised by any test.
- `test_auth_get_credentials_singleton` uses a token with `expires_at = now + 7200` (not expired), so `_is_expired()` always returns False in that test.

**18. `auth.py` — `_refresh_token()` — successful HTTP refresh path**
- The success path of `_refresh_token()` (HTTP POST succeeds, new credentials returned and saved) has no test.
- Only the two error paths (no refresh_token, missing env vars) are tested.

**19. `server.py` — `post_update()` unexpected exception branch (lines 58-60)**
- The `except Exception` catch-all in `post_update()` is not tested.

**20. `server.py` — `get_profile()` OIDC `sub` field path (line 68)**
- `test_get_profile_success` uses the legacy `id` field. The OIDC `sub` field path in `get_profile()` (line 68: `data.get("sub", data.get("id", ""))`) is not tested for the `sub` present case.

---

## WEAK: Tests That Exist But Assert Insufficiently

### 1. `test_draft_workflow_creates_vault_file` — mock bypass of PrivacyGate on content

```python
with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
    pg.return_value = MagicMock(media_blocked=False)
```

The mock patches `run_privacy_gate` globally, so both the topic-gate (Step 1) AND the content-gate (Step 4) return `media_blocked=False`. This means Step 4 never fires. The test does not distinguish which call to `run_privacy_gate` is being exercised. A more precise test would use `side_effect` to return different values on the first and second call.

### 2. `test_publish_approved_post` — no assertion on `move_to_done` called

```python
with patch("orchestrator.linkedin_poster.move_to_done"):
    result = await publish_approved(draft_path)
    assert result["status"] == "published"
```

The test asserts status but does not verify that `move_to_done` was actually called (i.e., `mock_move_to_done.assert_called_once_with(...)`). The draft could remain in Pending_Approval silently.

### 3. `test_auto_mode_picks_random_topic` — `_load_topics` is entirely mocked

```python
with patch("orchestrator.linkedin_poster._load_topics", return_value=["Topic A", "Topic B", "Topic C"]):
```

The real `_load_topics()` function (which reads a file, parses bullet lines, handles missing file) is never exercised. This test provides 0% coverage of `_load_topics()` itself.

### 4. `test_vault_item_type_linkedin_triggers_draft` — does not test the exception handler

The `process_linkedin_vault_triggers()` function wraps each file processing in `try/except Exception`. The test only exercises the success path. There is no test where processing a trigger raises an exception, to verify the error is logged and the next file is still processed.

### 5. `test_post_update_auto_refresh_on_401` — does not actually test 401 handling

```python
with patch(
    "mcp_servers.linkedin.server.post_to_linkedin",
    new_callable=AsyncMock,
    return_value={"post_id": "urn:li:share:789", "raw": {}},
):
```

This test patches `post_to_linkedin` to succeed immediately. It does not simulate a 401, retry, or token refresh. The test name is misleading — it tests a normal success path, not auto-refresh behavior. The actual 401 retry logic in `client.py` is entirely untested.

### 6. `test_health_check_all_healthy` — `token_expires_in_seconds` not verified

```python
assert data["healthy"] is True
assert data["token_valid"] is True
assert data["api_reachable"] is True
```

The `token_expires_in_seconds` field is computed and present in `HealthCheckResult` but never asserted in any test. If this computation breaks (e.g., returns None when it should return a positive int), no test would catch it.

### 7. `test_rejected_post_moves_to_rejected` — `_move_to_rejected` is mocked

```python
with patch("orchestrator.linkedin_poster._move_to_rejected"):
    result = await handle_rejected(draft_path)
    assert result["status"] == "rejected"
```

`_move_to_rejected` is patched away without asserting it was called. File movement is the core side effect of `handle_rejected()` — omitting the call assertion makes this test incomplete.

---

## RECOMMENDED: Specific New Test Cases

The following test function signatures and scenarios are recommended additions, ordered by spec risk priority.

### High Priority (spec invariants and production failure modes)

```python
@pytest.mark.asyncio
async def test_publish_approved_auth_error(mock_env, tmp_path):
    """AuthRequiredError during publish → status=auth_error, frontmatter updated."""
    from mcp_servers.linkedin.auth import AuthRequiredError
    from orchestrator.linkedin_poster import publish_approved

    draft_path = tmp_path / "2026-03-05T090000_linkedin_test.md"
    draft_path.write_text("---\nstatus: approved\ntopic: test\n---\nHello LinkedIn\n")
    with patch(
        "orchestrator.linkedin_poster._call_post_update",
        side_effect=AuthRequiredError("Token expired"),
    ):
        with patch("orchestrator.linkedin_poster._log_event"):
            with patch("orchestrator.linkedin_poster.update_frontmatter") as mock_fm:
                result = await publish_approved(draft_path)
                assert result["status"] == "auth_error"
                mock_fm.assert_called_once()
                call_kwargs = mock_fm.call_args[0][1]
                assert call_kwargs.get("status") == "auth_error"
```

```python
@pytest.mark.asyncio
async def test_publish_approved_file_not_found(mock_env, tmp_path):
    """publish_approved with non-existent file → status=error, reason=file_not_found."""
    from orchestrator.linkedin_poster import publish_approved

    missing_path = tmp_path / "nonexistent_linkedin_draft.md"
    result = await publish_approved(missing_path)
    assert result["status"] == "error"
    assert result["reason"] == "file_not_found"
```

```python
@pytest.mark.asyncio
async def test_draft_workflow_privacy_gate_on_content(mock_env, tmp_path):
    """PrivacyGate passes on topic but blocks AI-generated content → privacy_blocked content_blocked."""
    from orchestrator.linkedin_poster import draft_and_notify

    # First call (topic) passes, second call (content) blocks
    gate_responses = [MagicMock(media_blocked=False), MagicMock(media_blocked=True)]
    with patch("orchestrator.linkedin_poster.run_privacy_gate", side_effect=gate_responses):
        with patch(
            "orchestrator.linkedin_poster._draft_post_content",
            new_callable=AsyncMock,
            return_value="Sensitive content with PII",
        ):
            with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
                result = await draft_and_notify("safe topic")
                assert result["status"] == "privacy_blocked"
                assert result["reason"] == "content_blocked"
```

```python
@pytest.mark.asyncio
async def test_check_pending_approvals_expires_draft(mock_env, tmp_path):
    """check_pending_approvals expires a draft past its expires_at timestamp."""
    from orchestrator.linkedin_poster import check_pending_approvals
    import time

    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path):
        expired_draft = tmp_path / "2026-03-05T080000_linkedin_expired.md"
        expired_at = time.time() - 3600  # 1 hour ago
        expired_draft.write_text(
            f"---\ntype: linkedin_post\ntopic: old topic\nstatus: pending_approval\nexpires_at: {expired_at}\n---\nContent\n"
        )
        with patch("orchestrator.linkedin_poster.handle_rejected", new_callable=AsyncMock) as mock_reject:
            with patch("orchestrator.linkedin_poster._log_event"):
                await check_pending_approvals()
                mock_reject.assert_called_once_with(expired_draft)
```

```python
@pytest.mark.asyncio
async def test_draft_workflow_llm_error(mock_env, tmp_path):
    """LLM draft failure → status=error, no vault file created."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
            with patch(
                "orchestrator.linkedin_poster._draft_post_content",
                new_callable=AsyncMock,
                side_effect=Exception("Claude API unavailable"),
            ):
                with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path / "Pending_Approval"):
                    (tmp_path / "Pending_Approval").mkdir(parents=True)
                    result = await draft_and_notify("some topic")
                    assert result["status"] == "error"
                    # No vault file should have been created
                    assert len(list((tmp_path / "Pending_Approval").glob("*"))) == 0
```

```python
@pytest.mark.asyncio
async def test_draft_workflow_whatsapp_failure_nonfatal(mock_env, tmp_path):
    """WhatsApp notification failure does not abort draft — vault file still created."""
    from orchestrator.linkedin_poster import draft_and_notify

    with patch("orchestrator.linkedin_poster.run_privacy_gate") as pg:
        pg.return_value = MagicMock(media_blocked=False)
        with patch(
            "orchestrator.linkedin_poster._draft_post_content",
            new_callable=AsyncMock,
            return_value="Great post content",
        ):
            with patch("orchestrator.linkedin_poster._count_today_posts", return_value=0):
                with patch(
                    "orchestrator.linkedin_poster._send_hitl_notification",
                    new_callable=AsyncMock,
                    side_effect=Exception("WhatsApp bridge offline"),
                ):
                    with patch("orchestrator.linkedin_poster.VAULT_PENDING", tmp_path / "Pending_Approval"):
                        (tmp_path / "Pending_Approval").mkdir(parents=True)
                        result = await draft_and_notify("resilience topic")
                        # Draft should still be created despite WA failure
                        assert result["status"] == "drafted"
                        files = list((tmp_path / "Pending_Approval").glob("*_linkedin_*.md"))
                        assert len(files) == 1
```

### Medium Priority (edge cases)

```python
def test_count_today_posts_zero_when_no_file(tmp_path, monkeypatch):
    """_count_today_posts returns 0 when linkedin_posts.jsonl does not exist."""
    import orchestrator.linkedin_poster as poster_mod
    monkeypatch.setattr(poster_mod, "POSTS_JSONL", tmp_path / "linkedin_posts.jsonl")
    assert poster_mod._count_today_posts() == 0
```

```python
def test_load_topics_file_missing_returns_fallback(tmp_path, monkeypatch):
    """_load_topics returns default when topics file missing."""
    import orchestrator.linkedin_poster as poster_mod
    monkeypatch.setattr(poster_mod, "TOPICS_FILE", tmp_path / "nonexistent.md")
    topics = poster_mod._load_topics()
    assert len(topics) == 1
    assert "AI" in topics[0]
```

```python
def test_load_topics_all_comment_lines_returns_fallback(tmp_path, monkeypatch):
    """_load_topics returns fallback when file has only comment/blank lines."""
    import orchestrator.linkedin_poster as poster_mod
    topics_file = tmp_path / "linkedin_topics.md"
    topics_file.write_text("# Topic File\n# Category A\n\n")
    monkeypatch.setattr(poster_mod, "TOPICS_FILE", topics_file)
    topics = poster_mod._load_topics()
    assert topics == ["AI learning and development"]
```

```python
@pytest.mark.asyncio
async def test_process_linkedin_vault_triggers_empty_dir(tmp_path):
    """process_linkedin_vault_triggers handles empty Needs_Action directory gracefully."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done_dir = tmp_path / "Done"
    needs_action.mkdir()
    done_dir.mkdir()

    # Should complete without error and call no drafts
    with patch(
        "orchestrator.linkedin_poster.draft_and_notify",
        new_callable=AsyncMock,
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done_dir)
        mock_draft.assert_not_called()
```

```python
@pytest.mark.asyncio
async def test_process_linkedin_vault_triggers_nonexistent_dir(tmp_path):
    """process_linkedin_vault_triggers returns silently when needs_action_dir doesn't exist."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Nonexistent_Needs_Action"
    done_dir = tmp_path / "Done"
    # No exception should be raised
    await process_linkedin_vault_triggers(needs_action, done_dir)
```

```python
@pytest.mark.asyncio
async def test_process_linkedin_vault_triggers_missing_topic_fallback(mock_env, tmp_path):
    """Vault trigger with type=linkedin_post but no topic field falls back to 'LinkedIn post'."""
    from orchestrator.linkedin_poster import process_linkedin_vault_triggers

    needs_action = tmp_path / "Needs_Action"
    done_dir = tmp_path / "Done"
    needs_action.mkdir()
    done_dir.mkdir()

    trigger = needs_action / "2026-03-08T090000_notopic.md"
    trigger.write_text("---\ntype: linkedin_post\nstatus: pending\n---\n")

    with patch(
        "orchestrator.linkedin_poster.draft_and_notify",
        new_callable=AsyncMock,
        return_value={"status": "drafted"},
    ) as mock_draft:
        await process_linkedin_vault_triggers(needs_action, done_dir)
        mock_draft.assert_called_once_with("LinkedIn post")
```

### Lower Priority (client-layer retry path)

```python
@pytest.mark.asyncio
async def test_client_post_to_linkedin_401_retry_success():
    """post_to_linkedin retries after 401 and succeeds with refreshed token."""
    import mcp_servers.linkedin.client as client_mod

    mock_resp_401 = MagicMock()
    mock_resp_401.status_code = 401
    mock_resp_401.is_success = False

    mock_resp_201 = MagicMock()
    mock_resp_201.status_code = 201
    mock_resp_201.is_success = True
    mock_resp_201.headers = {"X-RestLi-Id": "urn:li:share:retry_ok"}
    mock_resp_201.content = b'{"id": "urn:li:share:retry_ok"}'
    mock_resp_201.json.return_value = {"id": "urn:li:share:retry_ok"}

    with patch("mcp_servers.linkedin.client.get_access_token", return_value="tok"):
        with patch("mcp_servers.linkedin.client.get_person_urn", return_value="urn:li:person:abc"):
            with patch("mcp_servers.linkedin.client.reset_credentials_cache") as mock_reset:
                with patch("httpx.AsyncClient") as mock_client_cls:
                    mock_client = AsyncMock()
                    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                    mock_client.__aexit__ = AsyncMock(return_value=None)
                    mock_client.post = AsyncMock(side_effect=[mock_resp_401, mock_resp_201])
                    mock_client_cls.return_value = mock_client

                    result = await client_mod.post_to_linkedin("Retry post", "PUBLIC")
                    assert result["post_id"] == "urn:li:share:retry_ok"
                    mock_reset.assert_called_once()
```

```python
def test_auth_get_credentials_triggers_refresh_when_expired(tmp_path, monkeypatch):
    """get_linkedin_credentials auto-refreshes when token is near expiry."""
    import json
    import time
    import mcp_servers.linkedin.auth as auth_mod

    token_file = tmp_path / "linkedin_token.json"
    token_file.write_text(
        json.dumps({
            "access_token": "expired_token",
            "refresh_token": "valid_refresh",
            "expires_at": time.time() + 60,  # within 5-min buffer → triggers refresh
            "person_urn": "urn:li:person:abc",
            "token_type": "Bearer",
        })
    )
    monkeypatch.setattr(auth_mod, "TOKEN_FILE", token_file)
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "test_id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "test_secret")
    auth_mod.reset_credentials_cache()

    new_creds_data = {
        "access_token": "fresh_token",
        "expires_in": 3600,
    }
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: new_creds_data,
            raise_for_status=lambda: None,
        )
        creds = auth_mod.get_linkedin_credentials()
        assert creds.access_token == "fresh_token"
        mock_post.assert_called_once()
```

---

## Coverage Estimate: Actual vs Reported 85.94%

### Assessment

The reported 85.94% is plausible for **line coverage** but significantly overstates **branch coverage**. Here is the breakdown:

| Module | Estimated Line Coverage | Estimated Branch Coverage | Notes |
|--------|------------------------|--------------------------|-------|
| `orchestrator/linkedin_poster.py` | ~72% | ~52% | `check_pending_approvals()` entirely untested; multiple except branches missing |
| `mcp_servers/linkedin/server.py` | ~90% | ~80% | `post_update` unexpected-exception catch-all untested; OIDC `sub` path untested |
| `mcp_servers/linkedin/client.py` | ~70% | ~50% | 401-retry success path untested; `get_profile` 401 retry untested |
| `mcp_servers/linkedin/auth.py` | ~80% | ~65% | Successful `_refresh_token()` HTTP path untested; `_is_expired()` True branch untested |
| `mcp_servers/linkedin/models.py` | ~95% | ~95% | Model validation exercises most paths via server tests |

**Weighted estimate**: ~78% line coverage, ~60% branch coverage across all four source modules.

### Why the Reported 85.94% May Be Inflated

1. **`pytest-cov` counts lines, not branches by default.** The `--cov-report=term-missing` command in T034 does not use `--cov-branch`. Linear code segments inside functions that are always reached inflate the percentage without testing conditional branches.

2. **`check_pending_approvals()` (lines 320-350 — ~30 lines) is entirely uncovered.** This is approximately 7% of `linkedin_poster.py` alone. Its absence from coverage should depress the poster module score significantly.

3. **Privacy-gate-on-content path (lines 238-242) is uncovered.** The mock in the happy-path test patches `run_privacy_gate` globally, causing it to return False for both calls — the tool call shows as "covered" because the function is called, but the `if content_check.media_blocked:` branch for `True` is never taken.

4. **`_load_topics()` actual code is never exercised** — only mocked. Pytest-cov measures whether lines were executed during a test run. If `_load_topics` is always mocked in `test_linkedin_poster.py`, those lines show as uncovered.

### Conclusion on SC-008

The >80% **line coverage** threshold (SC-008) may technically pass (the 85.94% figure is plausible if `_load_topics`, `check_pending_approvals`, and some client error paths are excluded from the measurement scope). However:

- **Branch coverage is below 80%** — closer to 60%.
- **Three high-risk production paths have zero tests**: `AuthRequiredError` in `publish_approved`, draft file missing in `publish_approved`, and content privacy gate.
- **The 401 auto-refresh feature (SC-010)** — advertised as a key capability — has zero actual coverage in `client.py`.

The test suite is **functionally adequate for a demo** but does not provide production-grade confidence for the HITL invariant (SC-003) and token lifecycle (SC-010) paths.

---

## Summary Table

| Category | Count | Risk |
|----------|-------|------|
| Tested paths (adequate) | 29 | — |
| Untested paths | 20 | HIGH: 6, MEDIUM: 8, LOW: 6 |
| Weak tests | 7 | Varies |
| Recommended new tests | 15 | — |
| Missing test scenarios from brief | 3 of 5 checked | `test_check_pending_approvals_expires_draft`, `test_draft_workflow_privacy_gate_on_content`, `test_count_today_posts_zero_when_no_file` |
| Present test scenarios from brief | 2 of 5 | `test_vault_item_type_linkedin_triggers_draft` (T029 ✅), `test_vault_item_hashtag_linkedin_triggers_draft` (T031 ✅) |

---

*Generated by automated coverage audit. Source revision: branch `009-linkedin-cron-silver`, 2026-03-09.*
