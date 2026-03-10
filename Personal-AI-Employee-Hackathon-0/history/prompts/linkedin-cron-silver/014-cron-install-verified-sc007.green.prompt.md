---
id: "014"
title: Cron Install Verified SC-007 PASS
stage: green
date: 2026-03-09
surface: agent
model: claude-sonnet-4-6
feature: linkedin-cron-silver
branch: 009-linkedin-cron-silver
user: m-y-j
command: manual
labels: ["cron","sc-007","bug-fix","scheduling","silver-complete"]
links:
  spec: specs/009-linkedin-cron-silver/spec.md
  ticket: specs/009-linkedin-cron-silver/tasks.md
  adr: history/adr/0015-cron-scheduling-strategy.md
  pr: null
files:
  - scripts/setup_cron.sh
tests:
  - tests/test_cron_scripts.sh (5/5 PASS)
  - SC-007: 3x run → exactly 2 entries PASS
---

## Prompt

start working on it — cron not installed yet (79/80 score gap)
Have we tested and verified it and scheduling test manually?
Basic scheduling via cron — scripts/setup_cron.sh idempotent, SC-007 verified

## Response snapshot

Installed and fully verified cron scheduling. Fixed 2 bugs in setup_cron.sh:

**Bug 1: `set -o allexport` + `source .env` corrupted crontab binary's env lookup (WSL2/systemd)**
- `allexport` exported .env vars including ANTHROPIC_API_KEY, LINKEDIN_CLIENT_SECRET, etc.
- This polluted the crontab binary's environment and caused `crontab -l` to return empty
- Fix: replaced `source .env` with `grep -m1 "^CRON_LINKEDIN_TIME=" .env | cut -d'=' -f2-`

**Bug 2: `grep -v "H0_CRON_MANAGED"` exits 1 when ALL lines match + `set -e` kills subshell**
- When all existing crontab lines are H0_CRON_MANAGED, `grep -v` returns exit code 1
- With `set -e`, this killed the `(...)` subshell before echo entries could run
- `crontab -` received empty stdin → wiped the crontab
- Fix: `{ crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED" || true; echo ...; echo ...; } | crontab -`

**Verified:**
- Cron fire proof: CRON_FIRED at 20:32:01 and 20:33:01 (1-min test entry, 2 fires confirmed)
- SC-007: 3x run → exactly 2 H0_CRON_MANAGED entries PASS ✅
- test_cron_scripts.sh: 5/5 PASS (syntax + idempotency checks)
- LinkedIn health_check: healthy=True, api_reachable=True, token_expires_in_seconds=5118752
- linkedin_poster --check: Exit 0 ✅

**Final installed crontab:**
```
*/15 * * * * cd <PROJECT_ROOT> && export $(grep -v '^#' .env | xargs) && python3 orchestrator/orchestrator.py >> cron.log 2>&1 # H0_CRON_MANAGED
0 9 * * * cd <PROJECT_ROOT> && export $(grep -v '^#' .env | xargs) && python3 orchestrator/linkedin_poster.py --auto >> cron.log 2>&1 # H0_CRON_MANAGED
```

## Outcome

- ✅ Impact: Silver Tier = 80/80 (100%) — cron installed, SC-007 PASS, scheduling verified live
- 🧪 Tests: test_cron_scripts.sh 5/5 PASS; cron fire confirmed 20:32+20:33; SC-007 idempotency PASS
- 📁 Files: scripts/setup_cron.sh (2 bug fixes)
- 🔁 Next prompts: Phase 6 — CEO Briefing + Odoo Gold tier
- 🧠 Reflection: `set -e` + `grep -v` is a classic trap. `grep -v` exits 1 when the input only contains matching lines (nothing passes through). Always use `|| true` with grep inside `set -e` scripts when the empty-output case is valid. Also: never use `allexport` to source .env when crontab is used in the same process — it corrupts the binary's environment.

## Evaluation notes (flywheel)

- Failure modes observed: WSL2 crontab display bug (journalctl showed daemon reloading, but crontab -l showed empty); set -e + grep -v kills subshell on full-match input
- Graders run and results (PASS/FAIL): SC-007 PASS; test_cron_scripts.sh 5/5 PASS; cron fire confirmed
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Monitor vault/Logs/cron.log after next */15 boundary to confirm orchestrator poll cycle fires live
