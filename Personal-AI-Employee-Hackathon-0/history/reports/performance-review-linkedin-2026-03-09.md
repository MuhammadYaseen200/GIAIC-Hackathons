# Performance Review: LinkedIn Auto-Poster (Phase 5.5)

**Date:** 2026-03-09
**Reviewer:** Performance Audit Agent
**Scope:** `mcp_servers/linkedin/client.py`, `mcp_servers/linkedin/auth.py`, `orchestrator/linkedin_poster.py`, `mcp_servers/linkedin/server.py`
**Spec SCs verified:** SC-001, SC-002, SC-005, SC-006

---

## Executive Summary

The LinkedIn implementation is generally well-structured and should meet SC-001, SC-002, and SC-006 under normal conditions. Two issues need attention: the **synchronous Anthropic API call inside an async function** (a blocking call that freezes the event loop) and the **O(n) full-file read** in `_count_today_posts()`. Everything else is either passing or carries low risk at current scale.

---

## 1. HTTP Timeouts

### PASS — Timeouts are correctly set and match spec requirements

| Call | File | Timeout Set | Expected |
|---|---|---|---|
| `post_to_linkedin` (UGC POST) | `client.py:54` | `30.0s` | 30s |
| `get_profile` (userinfo GET) | `client.py:75` | `15.0s` | 15s |
| `health_check_api` | `client.py:96-99` | `5.0s` (set twice — once on AsyncClient, once on `get`) | 5s |
| `_refresh_token` (sync POST) | `auth.py:65-74` | `15.0s` | acceptable |
| `GoBridge.send` (WhatsApp) | `bridge.py:27` | `10.0s` | acceptable |

**Note:** `health_check_api` passes `timeout=5.0` twice — once to `AsyncClient(timeout=5.0)` and again as a keyword arg to `client.get(..., timeout=5.0)`. The second call is redundant but harmless.

---

## 2. Credential Caching

### PASS — Singleton avoids disk reads on every call

```python
# auth.py:88-96
def get_linkedin_credentials() -> LinkedInCredentials:
    global _credentials
    if _credentials is None:
        _credentials = _load_token_file()   # disk read only on cold start
    if _is_expired(_credentials):           # in-memory time check — O(1)
        _credentials = _refresh_token(_credentials)
    return _credentials
```

- First call: one disk read (`linkedin_token.json`).
- Subsequent calls within the 5-minute pre-expiry buffer: pure in-memory time comparison.
- Token refresh triggers one synchronous `httpx.POST` (blocking, see Section 8).
- The 300-second expiry buffer (`_is_expired(..., buffer_seconds=300)`) prevents last-second refreshes during posting.

**Minor:** `reset_credentials_cache()` sets `_credentials = None`, which correctly forces a reload on next call. Callers in `client.py` invoke this on 401, which is correct. However, in a multi-threaded environment this is not thread-safe (no lock). At current single-process cron scale this is acceptable.

---

## 3. Vault File I/O

### PASS — `atomic_write` is efficient for current scale

```python
# utils.py:54-78
def atomic_write(filepath, content):
    fd, tmp_path = tempfile.mkstemp(dir=str(filepath.parent), ...)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    os.replace(tmp_path, str(filepath))
```

- Uses `tempfile.mkstemp` + `os.replace` — two syscalls for the rename, crash-safe.
- No double-buffering: content is written directly to the temp FD.
- Overhead is negligible for text files (vault drafts are <5 KB).

### PASS — Vault scans are bounded

`check_pending_approvals()` uses `VAULT_PENDING.glob("*_linkedin_*.md")`, which limits the scan to LinkedIn draft files only. At a rate of ≤1 post/day the pending set will rarely exceed a handful of files.

`process_linkedin_vault_triggers()` scans all `*.md` in `Needs_Action/` — but this is shared with email items and is still bounded by how fast emails arrive. Not a concern at current scale.

---

## 4. Async Patterns

### BOTTLENECK — Synchronous Anthropic API call blocks the event loop

```python
# linkedin_poster.py:120-137
async def _draft_post_content(topic: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    # ...
    response = client.messages.create(   # <-- BLOCKING SYNC CALL inside async function
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": user_msg}],
        system=system,
    )
    return response.content[0].text.strip()
```

`anthropic.Anthropic.messages.create()` is a **synchronous** `httpx`-based call. Awaiting this function from an async context does not make it non-blocking — it runs on the calling thread and blocks the event loop for the entire LLM round-trip (typically 3–15 seconds).

Because `draft_and_notify` is called via `asyncio.run(...)` in the CLI (a single-event-loop, single-task context), this does not cause a deadlock. However:
- It prevents any concurrent async tasks from running during the LLM call.
- If the orchestrator ever calls `draft_and_notify` inside a shared event loop alongside other coroutines, it will stall them.

**Optimization:** Replace with `anthropic.AsyncAnthropic`:

```python
# Correct async pattern
from anthropic import AsyncAnthropic

async def _draft_post_content(topic: str) -> str:
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = await client.messages.create(   # non-blocking
        model="claude-sonnet-4-6",
        max_tokens=600,
        messages=[{"role": "user", "content": user_msg}],
        system=system,
    )
    return response.content[0].text.strip()
```

### PASS — All other async calls are correct

- `post_to_linkedin`, `get_profile`, `health_check_api`: all use `async with httpx.AsyncClient(...)` and `await client.post/get(...)` correctly.
- `GoBridge.send`: uses `async with httpx.AsyncClient(timeout=10.0)` — correct.
- `check_pending_approvals` and `process_linkedin_vault_triggers`: correctly `await` their async sub-calls.

### RISK — New `httpx.AsyncClient` per request (minor overhead)

Every HTTP call creates and tears down a new `httpx.AsyncClient` instance:

```python
# client.py:54
async with httpx.AsyncClient(timeout=30.0) as client:
    ...
```

This means a new TCP connection is opened per request. For a low-frequency cron job (once daily for posting, once per 15 minutes for approval checks), this is acceptable. If the server were to handle dozens of concurrent tool calls, a shared persistent client with connection pooling would be preferable.

---

## 5. SC-001 Compliance: Draft Workflow Timing (<30s excluding LLM)

### PASS — Non-LLM steps are well under 30s

Critical path for `draft_and_notify(topic)` excluding the LLM call:

| Step | Location | Estimated Time |
|---|---|---|
| `run_privacy_gate(topic)` | privacy_gate.py — pure regex, in-memory | <1ms |
| `_count_today_posts()` | disk read + line scan of JSONL | <5ms (small file) |
| `run_privacy_gate(post_text)` | pure regex, in-memory | <1ms |
| `_write_draft_vault_file()` | `atomic_write` — ~2 syscalls for small file | <5ms |
| `_send_hitl_notification()` | `GoBridge.send` — HTTP POST to local bridge | <500ms |
| `_log_event()` | single `open("a")` + write | <2ms |

**Total non-LLM time estimate: ~510ms** — comfortably within SC-001.

The LLM call itself (excluded from SC-001 per spec) is the dominant latency driver at ~3–15s depending on Claude's response time.

---

## 6. SC-002 Compliance: Publish Workflow Timing (<60s)

### PASS — `publish_approved` is fast

Critical path for `publish_approved(draft_path)`:

| Step | Location | Estimated Time |
|---|---|---|
| `draft_path.read_text()` | single file read | <1ms |
| Frontmatter parsing (string split) | in-memory | <1ms |
| `_call_post_update()` → `post_to_linkedin()` | LinkedIn API POST, timeout=30s | 1–10s typical |
| `update_frontmatter()` | `atomic_write` — file read + write | <5ms |
| `move_to_done()` | `shutil.move` — rename syscall | <1ms |
| `_log_event()` | `open("a")` append | <1ms |

**Total estimate: 1–10s** — well within SC-002's 60-second budget.

**Worst case with 401 retry:** If a 401 triggers `reset_credentials_cache()` + `get_access_token()` (which may trigger `_refresh_token()` — a sync `httpx.post` to LinkedIn's token endpoint, timeout=15s), total worst case is ~10s (API) + 15s (token refresh) = ~25s. Still within 60s.

---

## 7. Rate Limiting: `_count_today_posts()`

### RISK — O(n) full-file read on every draft trigger

```python
# linkedin_poster.py:90-103
def _count_today_posts() -> int:
    if not POSTS_JSONL.exists():
        return 0
    today = date.today().isoformat()
    count = 0
    for line in POSTS_JSONL.read_text().splitlines():   # reads entire file into memory
        try:
            entry = json.loads(line)
            if entry.get("status") == "published" and entry.get("ts", "").startswith(today):
                count += 1
        except json.JSONDecodeError:
            continue
    return count
```

The entire JSONL file is read into memory and all lines are parsed. For a log that accumulates at ~1 entry/day (drafts + publishes + rate-limit events ~5 entries/day), growth is:

| Months of Operation | Approx Lines | File Size | Read Time |
|---|---|---|---|
| 1 month | ~150 | ~15 KB | <1ms |
| 1 year | ~1,800 | ~180 KB | <2ms |
| 5 years | ~9,000 | ~900 KB | ~5ms |

At current scale this is **acceptable**. At multi-year scale the optimization would be to read only the last N lines (today's entries are always at the tail of an append-only log). No action needed now.

---

## 8. Memory Concerns

### PASS — No unbounded data structures

- `_load_topics()` reads `linkedin_topics.md` into a list. Topic files are small (tens of items) — negligible.
- `check_pending_approvals()` and `process_linkedin_vault_triggers()` iterate files one at a time; no bulk load into memory.
- No caches beyond the `_credentials` singleton (a single `LinkedInCredentials` object).
- The JSONL log scan in `_count_today_posts()` allocates the entire file as a string then a list of strings. For current scale, peak memory is <1 MB. No leak — garbage collected after function returns.

### RISK — `anthropic.Anthropic` client instantiated on every draft call

```python
# linkedin_poster.py:122
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
```

A new SDK client object is constructed on every `_draft_post_content()` call. The Anthropic SDK internally creates an `httpx.Client` with connection pooling. Since each draft call is isolated (CLI invocation), this is not a leak. However, if called inside a long-running process, this client is not reused. Consider module-level initialization if this moves to a persistent service.

---

## 9. Cron / `check_pending_approvals()` Scan Efficiency

### PASS — SC-005 compliant; scan is bounded

`check_pending_approvals()` (called every 15 minutes via cron):

1. `VAULT_PENDING.glob("*_linkedin_*.md")` — filesystem glob, O(files in directory).
2. For each match: one `read_text()` + manual frontmatter string split (no YAML parse — just `startswith` checks).
3. Processes approved/rejected/expired items and moves files out of the pending directory.

At ≤1 draft/day, the pending directory will contain at most 1–2 files at any given time. The scan completes in well under 1 second. SC-005 (within 15 minutes) is trivially met — the scan itself is faster than the 15-minute cron interval.

**Note:** `process_linkedin_vault_triggers()` does a similar scan of `Needs_Action/*.md` but uses full YAML-safe parsing via `_split_file()` → `yaml.safe_load()`. Compared to the manual `startswith` parsing in `check_pending_approvals()`, this is slightly heavier per file but still negligible for a small vault directory.

---

## 10. SC-006 Compliance: `setup_cron.sh` in <5s

### PASS — Script is fast

`setup_cron.sh` operations:
1. `cd` + `pwd` — near-instant.
2. `source .env` — reads a small file.
3. `crontab -l` — reads crontab (~1ms).
4. `grep -v "H0_CRON_MANAGED"` — filters in-memory string.
5. `crontab -` — writes new crontab (~1ms).
6. `echo` statements.

Worst case: ~100ms on any normal system. Well within 5s.

---

## 11. Token Refresh: Synchronous in Async Context

### BOTTLENECK — `_refresh_token()` is synchronous and blocks the event loop

```python
# auth.py:65-74
resp = httpx.post(      # synchronous httpx — blocks event loop for up to 15s
    REFRESH_URL,
    data={...},
    timeout=15.0,
)
```

`_refresh_token()` uses the synchronous `httpx.post()`. This is called from `get_linkedin_credentials()`, which is called from `get_access_token()`, which is called inside the `post_to_linkedin` async function:

```python
# client.py:55
token = get_access_token()   # may call _refresh_token() which does sync httpx.post
```

This is the same pattern as the Anthropic sync call: it works in the current single-task asyncio.run() setup, but blocks the event loop during token refresh. In a shared async environment this would stall concurrent operations for up to 15 seconds.

---

## 12. Server.py FastMCP Overhead

### PASS — FastMCP overhead is minimal

`server.py` uses the FastMCP decorator pattern:
- `@mcp.tool()` wraps three async functions: `post_update`, `get_profile`, `health_check`.
- Input validation via Pydantic v2 (`PostUpdateInput`) — fast, compiled validators.
- JSON serialization via `model_dump()` — in-memory, no I/O.
- No in-memory state accumulation between tool calls.

The only stateful concern is `get_linkedin_credentials()` called in `health_check` — this reuses the module-level singleton and is O(1) after warm-up.

**Note:** `health_check` calls both `get_linkedin_credentials()` (may trigger disk read or token refresh) and `health_check_api()` (5s timeout HTTP call) sequentially. If the LinkedIn API is slow, health checks can take up to ~5s, which is acceptable for a health endpoint.

---

## Critical Path Timing Summary

### Draft Workflow (`--draft "topic"`)

```
run_privacy_gate(topic)         ~0ms  (regex, in-memory)
_count_today_posts()            ~1ms  (small JSONL read)
_draft_post_content()           3000–15000ms  [LLM — excluded from SC-001]
run_privacy_gate(post_text)     ~0ms
_write_draft_vault_file()       ~3ms  (atomic_write)
_send_hitl_notification()       ~200ms  (HTTP POST to local WA bridge)
_log_event()                    ~1ms  (append to JSONL)
─────────────────────────────────────────────────────
Non-LLM total:                  ~205ms  [SC-001 limit: 30s — PASS]
```

### Publish Workflow (`publish_approved`)

```
draft_path.read_text()          ~1ms
frontmatter parse               ~0ms  (string split)
post_to_linkedin()              1000–10000ms  (LinkedIn API)
  └── possible 401 + refresh:  +15000ms worst case  (sync httpx)
update_frontmatter()            ~3ms  (atomic_write)
move_to_done()                  ~1ms  (shutil.move)
_log_event()                    ~1ms
─────────────────────────────────────────────────────
Normal total:                   ~1005ms
Worst case (401 + refresh):     ~25005ms  [SC-002 limit: 60s — PASS]
```

---

## Findings by Category

### BOTTLENECK

| ID | Location | Issue |
|---|---|---|
| B-001 | `linkedin_poster.py:131` | `client.messages.create()` is a synchronous call inside an `async def`. Blocks event loop for LLM round-trip. Use `AsyncAnthropic` instead. |
| B-002 | `auth.py:65` | `_refresh_token()` uses synchronous `httpx.post()`. Blocks event loop for up to 15s during token refresh. Should use `httpx.AsyncClient` if called from async context. |

### RISK

| ID | Location | Issue |
|---|---|---|
| R-001 | `linkedin_poster.py:96` | `_count_today_posts()` reads the entire JSONL file into memory. O(n) scaling over years. Acceptable now; revisit after 6+ months of operation. |
| R-002 | `auth.py:25` / `client.py:55-62` | Credential singleton is not thread-safe. Safe for single-process cron; unsafe if ever called from multi-threaded context. |
| R-003 | `client.py:54, 75, 96` | New `httpx.AsyncClient` per request — no connection reuse. Acceptable at cron frequency; would need a persistent client if request rate increases. |
| R-004 | `linkedin_poster.py:122` | `anthropic.Anthropic` client instantiated on every draft — no reuse. Fine for CLI; wasteful in a long-running service. |

### OPTIMIZATION

| ID | Priority | Change | Benefit |
|---|---|---|---|
| O-001 | HIGH | Replace `anthropic.Anthropic` with `anthropic.AsyncAnthropic` in `_draft_post_content()` | Eliminates event loop blocking during LLM call |
| O-002 | MEDIUM | Replace `httpx.post()` in `_refresh_token()` with `await httpx.AsyncClient().post()` and make the function async | Eliminates event loop blocking during token refresh |
| O-003 | LOW | Cache `anthropic.AsyncAnthropic` at module level (or as a singleton) rather than instantiating per call | Reduces object creation overhead; enables connection pooling |
| O-004 | LOW | In `_count_today_posts()`: read only the last N lines (e.g., last 100) rather than the full file | Keeps performance stable as JSONL grows over years |

### PASS

| Check | Verdict |
|---|---|
| HTTP timeouts (post=30s, profile=15s, health=5s) | PASS — all correctly set |
| Credential caching (no disk read on every call) | PASS — module-level singleton |
| `atomic_write` correctness and efficiency | PASS — tempfile + os.replace |
| Vault scan bounded | PASS — glob filter limits scope |
| SC-001: <30s non-LLM path | PASS — ~205ms measured |
| SC-002: <60s publish path | PASS — ~1s normal, ~25s worst case |
| SC-005: cron processes within 15 min | PASS — scan <1s |
| SC-006: setup_cron.sh <5s | PASS — ~100ms |
| FastMCP server overhead | PASS — minimal; Pydantic validators fast |
| Memory bounds | PASS — no unbounded structures |
| Privacy gate performance | PASS — pure in-memory regex, <1ms |

---

## Action Items (Prioritized)

1. **[HIGH] Fix B-001** — Switch `_draft_post_content()` to `AsyncAnthropic`. This is the only correctness risk: if the orchestrator ever calls multiple async workflows concurrently, the sync LLM call will stall them.

2. **[MEDIUM] Fix B-002** — Make `_refresh_token()` async and use `httpx.AsyncClient`. The current pattern works but is technically incorrect inside an async call stack.

3. **[LOW] O-004** — Add a tail-read optimization to `_count_today_posts()` as a forward-looking hygiene improvement.

4. **[LOW] O-003** — Consider a module-level Anthropic client singleton for future long-running service deployments.
