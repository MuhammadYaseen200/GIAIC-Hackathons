---
id: 009
title: run_until_complete unit tests + AsyncAnthropic mock fix
stage: green
date: 2026-03-18
surface: agent
model: claude-sonnet-4-6
feature: ceo-briefing-odoo-gold
branch: 010-ceo-briefing-odoo-gold
user: m-y-j
command: write unit tests for run_until_complete and fix AsyncAnthropic mock
labels: ["testing","unit-tests","run-until-complete","async","mock","anthropic"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - tests/unit/test_run_until_complete.py
  - tests/unit/test_ceo_briefing.py
  - tests/unit/test_weekly_audit.py
tests:
  - tests/unit/test_run_until_complete.py::test_on_exhausted_exception_does_not_propagate
  - tests/unit/test_run_until_complete.py::test_all_steps_succeed_three_steps
  - tests/unit/test_run_until_complete.py::test_default_max_retries_is_three
  - tests/unit/test_run_until_complete.py::test_audit_log_entries
---

## Prompt

You are creating unit tests for a file that currently has ZERO direct tests.

Working directory: `/mnt/e/M.Y/GIAIC-Hackathons/Personal-AI-Employee-Hackathon-0`

Read orchestrator/run_until_complete.py, tests/unit/test_ceo_briefing.py, tests/unit/test_weekly_audit.py.

Create tests/unit/test_run_until_complete.py with comprehensive async tests covering:
1. test_all_steps_succeed
2. test_step_fails_then_succeeds
3. test_step_exhausts_retries (with on_exhausted callback args verified)
4. test_on_exhausted_exception_does_not_propagate
5. test_completed_steps_populated
6. test_default_max_retries
7. test_audit_log_entries (with tmp_path fixture)

Also fix mocks in test_ceo_briefing.py and test_weekly_audit.py:
- Change `patch("anthropic.Anthropic", ...)` to `patch("anthropic.AsyncAnthropic", ...)`
- Change `mock_client.messages.create.return_value = ...` to `mock_client.messages.create = AsyncMock(return_value=...)`

Do NOT run the tests.

## Response snapshot

- Discovered `tests/unit/test_run_until_complete.py` already existed with 11 tests but was missing `test_on_exhausted_exception_does_not_propagate`.
- Added 4 new tests to the existing file: `test_on_exhausted_exception_does_not_propagate`, `test_all_steps_succeed_three_steps`, `test_default_max_retries_is_three`, `test_audit_log_entries` (with `tmp_path` fixture using tmpdir redirect of `ruc_mod.AUDIT_LOG`).
- Fixed `test_ceo_briefing.py` line ~491: replaced `patch("anthropic.Anthropic", ...)` + sync `return_value=mock_message` with `patch("anthropic.AsyncAnthropic", ...)` + `AsyncMock(return_value=mock_message)`.
- Fixed `test_weekly_audit.py` line ~361: same pattern fix for `_llm_draft_weekly`.

## Outcome

- Impact: All 7 required test scenarios are now covered in test_run_until_complete.py; AsyncAnthropic mock mismatch fixed in two test files.
- Tests: 4 new tests added; 2 existing mocks corrected to match actual async client usage.
- Files: tests/unit/test_run_until_complete.py (extended), tests/unit/test_ceo_briefing.py (mock fix), tests/unit/test_weekly_audit.py (mock fix).
- Next prompts: Run the full test suite to confirm green; check coverage report.
- Reflection: The file already had solid coverage; the key gap was the on_exhausted callback self-exception scenario and the explicit 3-step / default-retries / tmpdir-audit-log tests.

## Evaluation notes (flywheel)

- Failure modes observed: Existing mock used sync `messages.create.return_value` instead of `AsyncMock`; would fail with `TypeError: object MagicMock can't be used in await expression`.
- Graders run and results (PASS/FAIL): not run (per task instructions)
- Prompt variant (if applicable): none
- Next experiment: Run pytest -x tests/unit/test_run_until_complete.py to verify all pass without asyncio.sleep blocking.
