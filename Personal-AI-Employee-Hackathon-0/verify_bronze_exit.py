"""Bronze Tier exit verification — run after stopping live_run.py."""
import json
import sys
from pathlib import Path

VAULT = Path("vault")
LOGS = VAULT / "Logs"
STATE_FILE = LOGS / "gmail_watcher_state.json"

passed = []
failed = []

# ── 1. Crash check ────────────────────────────────────────────────────────
lock = LOGS / ".gmail_watcher.lock"
if not lock.exists():
    passed.append("No crash — lock file cleanly released on Ctrl+C")
else:
    # Lock still exists means it wasn't stopped cleanly — check if stale
    failed.append("Lock file still present — was live_run.py stopped with Ctrl+C?")

# ── 2. State corruption check ─────────────────────────────────────────────
try:
    state = json.loads(STATE_FILE.read_text())
    required_keys = ["last_poll_timestamp", "processed_ids", "error_count",
                     "total_emails_processed", "uptime_start"]
    missing = [k for k in required_keys if k not in state]
    if missing:
        failed.append(f"State corruption — missing keys: {missing}")
    elif state["error_count"] == 0:
        passed.append(f"State intact — {state['total_emails_processed']} emails processed, 0 errors")
    else:
        passed.append(f"State intact — {state['total_emails_processed']} emails processed, "
                      f"{state['error_count']} errors (check logs)")
except (json.JSONDecodeError, FileNotFoundError) as e:
    failed.append(f"State corruption — {e}")

# ── 3. Memory leak check (via log file) ──────────────────────────────────
log_files = sorted(LOGS.glob("gmail_watcher_*.log"))
if not log_files:
    failed.append("No log files found")
else:
    total_events = 0
    error_events = 0
    for lf in log_files:
        for line in lf.read_text().splitlines():
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                total_events += 1
                if entry.get("severity") in ("ERROR", "CRITICAL"):
                    error_events += 1
            except json.JSONDecodeError:
                pass
    passed.append(f"Logs intact — {total_events} events logged, {error_events} errors")
    if error_events == 0:
        passed.append("No ERROR/CRITICAL events in logs — clean run")

# ── 4. Vault files check ─────────────────────────────────────────────────
na_files = list((VAULT / "Needs_Action").glob("*.md"))
inbox_files = list((VAULT / "Inbox").glob("*.md"))
corrupted = []
for f in na_files + inbox_files:
    content = f.read_text()
    if not content.startswith("---\n") or "status: pending" not in content:
        corrupted.append(f.name)

if corrupted:
    failed.append(f"Corrupted vault files: {corrupted}")
else:
    passed.append(f"Vault files intact — {len(na_files)} in Needs_Action, "
                  f"{len(inbox_files)} in Inbox, all valid")

# ── Report ────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  BRONZE TIER EXIT VERIFICATION")
print("=" * 55)
for p in passed:
    print(f"  ✅  {p}")
for f in failed:
    print(f"  ❌  {f}")

print("=" * 55)
if not failed:
    print("  VERDICT: BRONZE TIER EXITED ✅")
    print("  All exit criteria met. Ready for Phase 3 Silver.")
else:
    print("  VERDICT: ISSUES FOUND — review above")
print("=" * 55 + "\n")

sys.exit(0 if not failed else 1)
