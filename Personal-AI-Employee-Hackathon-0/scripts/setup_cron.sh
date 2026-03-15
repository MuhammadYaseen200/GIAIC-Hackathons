#!/bin/bash
# setup_cron.sh — Install H0 cron entries (idempotent). ADR-0015.
# SC-010: Run 3x → exactly 4 H0_CRON_MANAGED entries (Phase 6 update).
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$(which python3)"
CRON_LOG="$PROJECT_ROOT/vault/Logs/cron.log"

# Verify correct project directory
if [[ "$PROJECT_ROOT" != *"Personal-AI-Employee-Hackathon-0"* ]]; then
    echo "WRONG DIRECTORY: $PROJECT_ROOT — STOP"
    exit 1
fi

# Load CRON_LINKEDIN_TIME from .env — use grep/cut, NOT allexport.
# allexport + source .env corrupts crontab binary's env lookup in WSL2/systemd.
# grep || true prevents set -e from exiting when key is absent (defaults to "0 9").
CRON_LINKEDIN_TIME_RAW=$(grep -m1 "^CRON_LINKEDIN_TIME=" "$PROJECT_ROOT/.env" 2>/dev/null | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
CRON_TIME="${CRON_LINKEDIN_TIME_RAW:-0 9}"
CRON_MINUTE=$(echo "$CRON_TIME" | cut -d' ' -f1)
CRON_HOUR=$(echo "$CRON_TIME" | cut -d' ' -f2)

mkdir -p "$PROJECT_ROOT/vault/Logs"

ORCH_ENTRY="*/15 * * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/orchestrator.py >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
LINKEDIN_ENTRY="$CRON_MINUTE $CRON_HOUR * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/linkedin_poster.py --auto >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
BRIEFING_ENTRY="0 7 * * * cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/ceo_briefing.py --now >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"
WEEKLY_ENTRY="0 7 * * 1 cd $PROJECT_ROOT && export \$(grep -v '^#' .env | xargs) && $PYTHON orchestrator/weekly_audit.py --weekly >> $CRON_LOG 2>&1 # H0_CRON_MANAGED"

# Idempotency: strip ALL H0_CRON_MANAGED lines then re-add exactly 4.
# grep -v exits 1 when ALL lines match (nothing left after filtering) — || true prevents
# set -e from killing the subshell and passing empty stdin to crontab -.
{ crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED" || true; echo "$ORCH_ENTRY"; echo "$LINKEDIN_ENTRY"; echo "$BRIEFING_ENTRY"; echo "$WEEKLY_ENTRY"; } | crontab -

echo "Cron entries installed (4 total)."
echo "   Orchestrator: every 15 minutes"
echo "   LinkedIn poster: daily at ${CRON_HOUR}:${CRON_MINUTE}"
echo "   CEO Briefing: daily at 07:00"
echo "   Weekly Audit: every Monday at 07:00"
echo ""
echo "Verify with: crontab -l | grep H0_CRON_MANAGED | wc -l  (expected: 4)"
