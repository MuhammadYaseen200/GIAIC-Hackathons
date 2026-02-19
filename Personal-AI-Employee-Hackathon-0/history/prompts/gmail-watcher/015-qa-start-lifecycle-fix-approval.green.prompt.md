---
id: 015
title: QA Overseer — start() Lifecycle Fix Approval
stage: green
date: 2026-02-19
surface: agent
model: claude-sonnet-4-6
feature: gmail-watcher
branch: 005-gmail-watcher
user: qa-overseer
command: qa-review start-lifecycle-fix
labels: ["qa","regression","lifecycle","authentication","bug-fix"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - watchers/gmail_watcher.py
  - watchers/base_watcher.py
  - tests/unit/test_gmail_watcher.py
tests:
  - tests/unit/test_gmail_watcher.py::TestStartLifecycleCallsAuthenticate::test_start_authenticates_before_poll_loop
---

## Prompt

You are acting as QA OVERSEER for the Gmail Watcher project at /mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0/.

A critical bug was just fixed. The previous QA rejection was:
"GmailWatcher._authenticate() is never called in start() lifecycle — self._service remains None causing AttributeError on first poll()"

The fix applied was:
```python
# In watchers/gmail_watcher.py, added start() override:
async def start(self) -> None:
    """Override to authenticate with Gmail before entering the poll loop."""
    self._resolve_paths()
    self._authenticate()
    await super().start()
```

A regression test was also added in tests/unit/test_gmail_watcher.py:
- Class: TestStartLifecycleCallsAuthenticate
- Method: test_start_authenticates_before_poll_loop
- Verifies: _authenticate() is called during start(), self._service is not None after start()

Test results: 119/119 unit tests PASS, 6/6 integration tests PASS, 89% coverage

Your task:
1. Read watchers/gmail_watcher.py (lines 120-175)
2. Read watchers/base_watcher.py (lines 57-90)
3. Verify the fix: Does GmailWatcher.start() now call _authenticate() before super().start() enters the poll loop?
4. Verify the test: Does TestStartLifecycleCallsAuthenticate actually test the right thing?
5. Check the call chain: GmailWatcher.start() → _resolve_paths() → _authenticate() → super().start() → validate_prerequisites() → _load_state() → poll loop

Report: APPROVED or still REJECTED.

## Response snapshot

STATUS: APPROVED

Fix verification confirmed. Call chain in GmailWatcher.start() (lines 133-141, watchers/gmail_watcher.py):

1. self._resolve_paths() — resolves credential/token paths from .env before auth needs them
2. self._authenticate() — sets self._service to a live Gmail API client
3. await super().start() — BaseWatcher.start() then runs validate_prerequisites() → _load_state() → _acquire_lock() → poll loop

self._service is guaranteed non-None before the first _run_poll_cycle() → poll() → _fetch_unread_emails_sync() call. The AttributeError path is closed.

Regression test (lines 668-699) is valid: tracks auth_calls list, simulates real _authenticate() side effects by setting _service = MagicMock(), uses stop_immediately coroutine to let start() run to completion, and patches validate_prerequisites to isolate the lifecycle concern. Both assertions (call presence + state mutation) are correct and would fail against the unfixed code.

## Outcome

- Impact: Critical lifecycle bug closed — GmailWatcher.start() now correctly initialises self._service before the poll loop executes
- Tests: 1 regression test added and passing; 119/119 unit + 6/6 integration all green; 89% coverage
- Files: watchers/gmail_watcher.py (start() override added), tests/unit/test_gmail_watcher.py (TestStartLifecycleCallsAuthenticate added)
- Next prompts: /sp.phr for any further phase work; proceed to deployment or next feature phase
- Reflection: The fix is minimal and correctly ordered. _resolve_paths() idempotency (double-call with validate_prerequisites()) is harmless. No new blockers introduced.

## Evaluation notes (flywheel)

- Failure modes observed: Original code had no start() override in subclass — base class never injected authentication into the lifecycle
- Graders run and results (PASS/FAIL): File inspection PASS, call-chain trace PASS, test logic review PASS
- Prompt variant (if applicable): qa-overseer-lifecycle-review-v1
- Next experiment: Add integration test that exercises real OAuth token refresh path to catch future _authenticate() regressions at the I/O boundary
