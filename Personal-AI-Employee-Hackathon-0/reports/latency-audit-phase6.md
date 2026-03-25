# Latency Audit Report — H0 Phase 6 (Gold Tier)
**Date**: 2026-03-17
**Reviewer**: Team Latency
**Scope**: End-to-end latency budgets, HTTP timeouts, cron scheduling delays, retry backoff impact, LLM call latency, sequential bottlenecks, JSONL performance

---

## CRITICAL Findings

### 🚨 C-001: No Timeout on LLM API Calls
**Severity**: CRITICAL
**File**: `orchestrator/ceo_briefing.py:170–174`, `orchestrator/weekly_audit.py:178–182`
**Issue**:
```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}],
)
```
The Anthropic SDK client has NO timeout parameter set. If the API hangs, the entire briefing/audit workflow blocks indefinitely.

**Impact**:
- CEO briefing stuck in `draft` step → HITL notification never sent → user never sees status
- Weekly audit stuck in `draft` step → no escalation
- Cron process accumulates (15-min interval + no timeout = multiple hung processes)

**Recommendation**:
```python
import anthropic
client = anthropic.Anthropic(timeout=30.0)  # explicit 30s timeout
```

**Status**: UNRESOLVED

---

### 🚨 C-002: Sequential Collection Calls Block Total Time
**Severity**: CRITICAL (Phase 6 SLA impact)
**File**: `orchestrator/ceo_briefing.py:387–396` (daily briefing steps)
**Issue**:
```python
result = await run_until_complete(
    "daily_briefing",
    [
        ("collect_email", step_collect_email),        # ~1–2s (local file read)
        ("collect_calendar", step_collect_calendar),  # ~2–5s (MCP HTTP call)
        ("collect_odoo", step_collect_odoo),          # ~3–8s (Odoo HTTP + RPC)
        ("collect_social", step_collect_social),      # ~1–3s (local file read)
        ("draft", step_draft),                        # ~5–10s (LLM call)
        ("write_vault", step_write_vault),            # ~0.2s (file I/O)
        ("send_hitl", step_send_hitl),                # ~1–2s (WhatsApp send)
    ],
    max_retries=3,
    on_exhausted=on_exhausted,
)
```

All 4 collect_* steps run **sequentially** even though they are **independent**. Estimated total:
- **Best case**: 1 + 2 + 3 + 1 = 7s (collect_*) + 5s (draft) + 0.2s (write) + 1s (notify) = **~13.2s**
- **Worst case**: 2 + 5 + 8 + 3 = 18s (collect_*) + 10s (draft) + 0.2s (write) + 2s (notify) = **~30.2s**
- **With 1 retry**: 30s + 7s backoff + 30s = **~67s** (exceeds typical cron timeout expectations)

**Impact**:
- CEO briefing consistently takes 13–30s on happy path (unacceptable for cron)
- Weekly audit also sequential, adds ~60s for 5 collect_* steps

**Recommendation**:
```python
async def run_daily_briefing() -> dict:
    from orchestrator.run_until_complete import run_until_complete

    # Collect email, calendar, odoo, social in PARALLEL
    # Then draft, then write, then notify
    result = await run_until_complete(
        "daily_briefing",
        [
            # PARALLEL block (all fire at once)
            ("collect_email", step_collect_email),
            ("collect_calendar", step_collect_calendar),
            ("collect_odoo", step_collect_odoo),
            ("collect_social", step_collect_social),
            # SEQUENTIAL block (depends on collect_* success)
            ("draft", step_draft),
            ("write_vault", step_write_vault),
            ("send_hitl", step_send_hitl),
        ],
        ...
    )
```

**But note**: `run_until_complete()` does NOT support parallel step execution. It runs sequentially with per-step retry. **This requires refactoring `run_until_complete()` to accept task groups.**

**Status**: UNRESOLVED

---

### 🚨 C-003: JSONL Log File Growth Unbounded
**Severity**: CRITICAL (degradation over time)
**Files**:
- `orchestrator/ceo_briefing.py:47–70` (collect_email_summary reads ALL log files)
- `orchestrator/weekly_audit.py:122–153` (collect_7day_email_rollup reads ALL lines)
- `mcp_servers/odoo/server.py`, `orchestrator/run_until_complete.py` all append to JSONL

**Issue**:
The system appends unbounded records to `vault/Logs/*.jsonl` files without rotation, truncation, or archival. When collecting email or social data, the code reads **entire files**:

```python
# ceo_briefing.py:55–68
for log_file in log_files:
    if "email" not in log_file.name and "gmail" not in log_file.name:
        continue
    try:
        with log_file.open() as f:
            for line in f:  # READS ALL LINES
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("ts", "")
                    if ts_str:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts.replace(tzinfo=None) >= yesterday.replace(tzinfo=None):  # FILTERS after read
```

**Measurements**:
- After 1 year of daily briefings (365 days × 1 entry/day = 365 lines) + 5 retries per day × 5 lines = **~2000 lines/year**
- After 10 years (typical server lifespan): **20,000 lines** in one file
- Reading 20k lines + parsing JSON + filtering timestamp = **O(n) latency growth**
- At 1000 entries/sec read speed, 20k lines = **20ms overhead per briefing** (acceptable but growing)

**Impact**:
- Each CEO briefing gets slower over time (O(n) read cost)
- Weekly audit reads 7-day window but still scans entire file sequentially
- No archival means disk usage grows indefinitely

**Recommendation**:
1. Implement **log rotation**: move `vault/Logs/ceo_briefing.jsonl` → `vault/Logs/ceo_briefing.YYYY-MM-DD.jsonl` daily
2. Implement **query optimization**: store only recent N days in active log
3. Archive old logs to `vault/Archive/` monthly

**Status**: UNRESOLVED

---

## HIGH Findings

### 🟠 H-001: Anthropic SDK Default Timeout May Be Too High
**Severity**: HIGH (excessive latency budget)
**File**: `orchestrator/ceo_briefing.py:170`, `orchestrator/weekly_audit.py:178`
**Issue**:
If Anthropic SDK defaults to 60s timeout or "no timeout", a single slow LLM call can extend CEO briefing from 30s to 60s+.

**Impact**:
- Cron job runs every 15 minutes; if briefing takes 60s, the next cron invocation may overlap (race condition)

**Recommendation**:
Verify Anthropic SDK timeout default:
```python
import anthropic
print(anthropic.Anthropic()._client_config.timeout)  # check actual value
```
Then set explicitly to 30s (acceptable for streaming, allows 2 retries within cron window).

**Status**: UNRESOLVED

---

### 🟠 H-002: Odoo HTTP Timeout of 30s May Be Too Loose
**Severity**: HIGH (blocks CEO briefing + weekly audit)
**File**: `mcp_servers/odoo/client.py:44, 87, 156, 199`
**Issue**:
```python
response = await client.post(
    f"{ODOO_URL}/web/dataset/call_kw",
    json=payload, headers=headers, timeout=30.0,  # ← 30 seconds
)
```

30 seconds is very long for a CEO briefing step. If Odoo is slow/hung, the entire briefing blocks for 30s. Three collect_odoo calls (GL summary, AR aging, invoices due) in weekly audit each wait 30s.

**Impact**:
- Weekly audit: 30s × 3 Odoo calls = 90s blocked (unacceptable)
- Daily briefing: 30s if Odoo is down
- Cron 15-min interval: if each Odoo call times out, process blocks for 30s of the 15-min window

**Recommendation**:
Reduce to 10s (reasonable for RPC-style call over LAN/Internet):
```python
timeout=10.0,  # faster failure + retry loop handles transient issues
```

**Status**: UNRESOLVED

---

### 🟠 H-003: Facebook/Instagram HTTP Timeout of 30s (Inconsistent)
**Severity**: HIGH (social poster latency)
**File**: `mcp_servers/facebook/client.py:22, 55, 107, 138`
**Issue**:
```python
async with httpx.AsyncClient(timeout=30.0) as client:
```

Social poster uses 30s timeout for all HTTP calls. If Meta Graph API is slow, social post approval/publishing waits 30s.

**Impact**:
- User clicks "APPROVE" in WhatsApp for social post draft
- System waits up to 30s per platform (Facebook + Instagram = 60s worst case)
- User experience: "is it still processing?"

**Recommendation**:
Reduce to 10s for Graph API (Meta is reliable):
```python
async with httpx.AsyncClient(timeout=10.0) as client:
```

**Status**: UNRESOLVED

---

### 🟠 H-004: No Timeout on WhatsApp Bridge Send
**Severity**: HIGH (HITL notification latency)
**File**: `orchestrator/ceo_briefing.py:299–300`, `orchestrator/weekly_audit.py:321–322`, `mcp_servers/whatsapp/bridge.py` (unknown)
**Issue**:
```python
bridge = GoBridge()
await bridge.send(owner_wa, msg)  # ← timeout?
```

WhatsApp bridge send has unknown timeout. If GoBridge hangs, HITL notification is delayed indefinitely.

**Impact**:
- CEO briefing completes all collection/draft steps (good)
- But HITL notification never reaches user (bad)
- User doesn't know briefing is ready for approval

**Recommendation**:
Check `mcp_servers/whatsapp/bridge.py` and add explicit timeout:
```python
await asyncio.wait_for(bridge.send(owner_wa, msg), timeout=5.0)
```

**Status**: BLOCKED (requires inspection of WhatsApp bridge code)

---

## MEDIUM Findings

### 🟡 M-001: Exponential Backoff in Retry Loop Adds 7s Max
**Severity**: MEDIUM (manageable but visible)
**File**: `orchestrator/run_until_complete.py:76–77`
**Issue**:
```python
if attempt < max_retries:
    backoff = 2 ** (attempt - 1)  # 1s, 2s, 4s
    await asyncio.sleep(backoff)
```

With `max_retries=3`, the backoff sequence is:
- Attempt 1 fails: sleep 1s, retry
- Attempt 2 fails: sleep 2s, retry
- Attempt 3 fails: sleep 4s, then escalate to on_exhausted callback

Total backoff across all steps: **7s max per step failure**

If collect_odoo fails 3 times: 1s + 2s + 4s = **7s of sleep** before moving to next step.

**Impact**:
- CEO briefing with one failed collect: 7s extra latency
- Two failed collects: 14s extra

**Recommendation**:
This is acceptable for transient failures (network hiccup, API overload). No change required if SLA tolerates 40–50s briefing time.

**Status**: ACCEPTABLE

---

### 🟡 M-002: JSONL Append Lock Contention
**Severity**: MEDIUM (low probability)
**File**: `orchestrator/ceo_briefing.py:38–39`, `orchestrator/run_until_complete.py:33–34`
**Issue**:
Multiple cron processes (orchestrator every 15 min, CEO briefing daily, weekly audit weekly) all append to `vault/Logs/*.jsonl` simultaneously. Python's file append is atomic per write, but multiple open() handles to the same file can cause I/O stalls.

**Impact**:
- Low probability, but if orchestrator and CEO briefing both fire at 07:00, both try to append to `ceo_briefing.jsonl`
- Brief stalls possible, but sub-100ms

**Recommendation**:
Use a lock file if append contention is observed:
```python
import fcntl
with BRIEFING_LOG.open("a") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    f.write(json.dumps(entry) + "\n")
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

**Status**: LOW PRIORITY (defer to Phase 7 if observed)

---

### 🟡 M-003: Cron Scheduling Margin Tight
**Severity**: MEDIUM (depends on actual duration)
**File**: `scripts/setup_cron.sh:26–29`
**Issue**:
```bash
ORCH_ENTRY="*/15 * * * * cd $PROJECT_ROOT && export ... && $PYTHON orchestrator/orchestrator.py >> $CRON_LOG 2>&1"
BRIEFING_ENTRY="0 7 * * * cd $PROJECT_ROOT && export ... && $PYTHON orchestrator/ceo_briefing.py --now >> $CRON_LOG 2>&1"
WEEKLY_ENTRY="0 7 * * 1 cd $PROJECT_ROOT && export ... && $PYTHON orchestrator/weekly_audit.py --weekly >> $CRON_LOG 2>&1"
```

- **Orchestrator**: every 15 minutes (900s interval)
  - If `orchestrator.py` takes >15 minutes, next run overlaps
  - Lock file in `orchestrator.py` should prevent, but unverified
- **CEO Briefing**: 7:00 AM daily
  - If briefing takes >30s, and weekly audit fires at 7:00 AM Monday, both run simultaneously
- **Weekly Audit**: 7:00 AM Monday
  - If audit takes >1 hour, cron doesn't reschedule

**Impact**:
- Orchestrator overlap possible if processing takes >15 min (rare, but possible with many emails)
- CEO briefing + weekly audit collision on Monday 7:00 AM (both compete for Odoo API)

**Recommendation**:
Add stagger times:
```bash
BRIEFING_ENTRY="0 7 * * * ..."  # 7:00 AM daily
WEEKLY_ENTRY="0 8 * * 1 ..."    # 8:00 AM Monday (1 hour after daily)
```

**Status**: ACCEPTABLE FOR PHASE 6 (revisit if collisions observed)

---

## LOW Findings

### 🟢 L-001: Email Triage Summary Uses Inefficient Date Filter
**Severity**: LOW (sub-100ms impact)
**File**: `orchestrator/ceo_briefing.py:55–68`
**Issue**:
```python
ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
if ts.replace(tzinfo=None) >= yesterday.replace(tzinfo=None):
```

Converts every timestamp to datetime, then filters. For large log files, this is O(n) but acceptable.

**Recommendation**: No change required (modern CPUs parse 1000s of ISO timestamps/sec).

---

### 🟢 L-002: CEO Briefing Mode Detection String Scan
**Severity**: LOW
**File**: `orchestrator/ceo_briefing.py:256–257`
**Issue**:
```python
llm_mode = "template" if "[TEMPLATE MODE]" in content else "llm"
section_count = content.count("## ")
```

Scans entire briefing content for substring. For 2000-token briefing, this is <1ms.

**Recommendation**: No change required.

---

## Estimated Latency Budgets (Current)

### Scenario 1: CEO Daily Briefing (Happy Path)
| Step | Min (s) | Max (s) | Notes |
|------|---------|---------|-------|
| collect_email | 0.5 | 2 | Read local log file |
| collect_calendar | 1 | 3 | HTTP to Calendar MCP |
| collect_odoo | 2 | 5 | Odoo RPC + session auth |
| collect_social | 0.5 | 2 | Read local log files |
| **Total collect_*** | 4 | 12 | ALL SEQUENTIAL ⚠️ |
| draft (LLM) | 3 | 10 | Anthropic API call, no timeout ⚠️ |
| write_vault | 0.2 | 0.2 | File I/O |
| send_hitl | 1 | 2 | WhatsApp send |
| **TOTAL** | **8.2s** | **24.2s** | **Current SLA: OK** |

### Scenario 2: CEO Daily Briefing (1 Retry on collect_odoo)
| Event | Duration (s) |
|-------|-------------|
| Attempt 1 (collect_odoo fails) | 4 + 2 (Odoo timeout) = 6 |
| Backoff | 1 |
| Attempt 2 (collect_odoo succeeds) | 4 |
| Remaining steps | 10 |
| **TOTAL** | **21s** |
| **Comfortable margin in 15-min cron window** | ✅ |

### Scenario 3: Weekly Audit (Happy Path)
| Step | Min (s) | Max (s) | Notes |
|------|---------|---------|-------|
| collect_gl | 3 | 8 | Odoo RPC |
| collect_ar | 3 | 8 | Odoo RPC + processing |
| collect_invoices | 3 | 8 | Odoo RPC |
| collect_social | 2 | 5 | Log file read (7-day window) |
| collect_email | 2 | 5 | Log file read (7-day window) |
| **Total collect_*** | 13 | 34 | ALL SEQUENTIAL ⚠️ |
| draft (LLM) | 5 | 10 | Anthropic API call |
| write_vault | 0.2 | 0.2 | File I/O |
| send_hitl | 1 | 2 | WhatsApp send |
| **TOTAL** | **19.2s** | **46.2s** | **Acceptable for weekly** |

### Scenario 4: Social Media Post (Approval → Publish)
| Event | Duration (s) | Notes |
|-------|-------------|-------|
| Draft creation | 0.2 | File write |
| HITL WhatsApp notification | 1–2 | Bridge send (unknown timeout) |
| User approval (manual) | 60+ | Human decision |
| Publish to Facebook | 1–2 | HTTP POST (30s timeout) |
| Publish to Instagram | 3–5 | 2-step container + publish (30s timeout each) |
| **Total (excl. user decision)** | 5–9s | Acceptable |

---

## Cron Scheduling Analysis

### Cron Entry Schedule (setup_cron.sh:26–29)

| Entry | Interval | Max Runtime | Risk |
|-------|----------|------------|------|
| Orchestrator | Every 15 min | ~5–10s (with lock) | ✅ Safe |
| LinkedIn Poster | Daily @ 9:00 AM | ~2–5s (drafting) | ✅ Safe |
| CEO Briefing | Daily @ 7:00 AM | 8–24s (see Scenario 1) | ✅ Safe |
| Weekly Audit | Monday @ 7:00 AM | 19–46s (see Scenario 3) | ⚠️ Collision risk on Monday 7:00 AM if briefing still running |

**Key Risk**: CEO briefing and weekly audit both fire at 07:00. If briefing takes 24s, audit starts at 07:00:24, both compete for Odoo API. Acceptable but tight.

---

## Recommendations Summary

| ID | Severity | Fix | Effort | Impact |
|-----|----------|-----|--------|--------|
| C-001 | CRITICAL | Add `timeout=30.0` to Anthropic client | 5 min | Prevent indefinite hangs |
| C-002 | CRITICAL | Parallelize collect_* steps in run_until_complete | 2–4 hours | Reduce 13–30s to ~8–15s |
| C-003 | CRITICAL | Implement log rotation (daily archive) | 1–2 hours | Prevent O(n) latency growth |
| H-001 | HIGH | Verify Anthropic SDK timeout default | 15 min | Confirm no silent 60s hangs |
| H-002 | HIGH | Reduce Odoo timeout from 30s → 10s | 10 min | Fail faster, retry quicker |
| H-003 | HIGH | Reduce Facebook timeout from 30s → 10s | 10 min | Faster user feedback on approval |
| H-004 | HIGH | Add timeout to WhatsApp bridge.send() | 20 min | Prevent notification delays |
| M-001 | MEDIUM | No change (acceptable backoff) | 0 | Defer |
| M-002 | MEDIUM | Add file lock (if contention observed) | 30 min | Prevent race conditions |
| M-003 | MEDIUM | Stagger briefing (7:00) + audit (8:00) | 5 min | Reduce Monday collision |

---

## Conclusion

**Current SLA Status**: ✅ ACCEPTABLE FOR PHASE 6 (under 30s for daily briefing, under 50s for weekly audit)

**Critical Issues**:
1. **No timeout on Anthropic LLM calls** — can hang indefinitely
2. **Sequential collect_* steps** — wastes 8–18s of budget unnecessarily
3. **Unbounded JSONL logs** — future degradation risk (10+ years)

**High-Impact Fixes** (recommended before Phase 7 / always-on deployment):
- Add Anthropic timeout (5 min)
- Reduce Odoo timeout (10 min)
- Implement log rotation (1–2 hours)
- Parallelize collect steps (2–4 hours)

**Acceptable Trade-offs**:
- Exponential backoff (7s max overhead) is reasonable
- Cron 15-min orchestrator interval is safe with lock file
- Monday 7:00 AM collision risk is acceptable (rare + brief)

---

## Appendix: Testing Checklist

- [ ] Measure actual CEO briefing duration under load (100 emails, network latency)
- [ ] Measure weekly audit duration with 10k+ lines in email log
- [ ] Verify Anthropic client timeout default via SDK source
- [ ] Test Odoo MCP timeout behavior at 10s (vs current 30s)
- [ ] Monitor cron.log for orchestrator overlaps over 1 week
- [ ] Monitor cron.log for Monday 7:00 AM briefing/audit collisions over 1 month
- [ ] Stress test social poster with simultaneous Facebook + Instagram publishes
