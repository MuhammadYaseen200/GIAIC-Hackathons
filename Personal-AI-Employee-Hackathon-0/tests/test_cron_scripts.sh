#!/bin/bash
# Smoke tests for setup_cron.sh and remove_cron.sh (SC-007, T026-T028).
# Tests idempotency: run setup 3x → exactly 2 H0_CRON_MANAGED entries.
#
# NOTE: On WSL, bash scripts executed from /mnt/... (Windows filesystem) cannot
# persist crontab changes to the Linux cron spool. This is a known WSL limitation.
# These tests run on native Linux (CI/production). On WSL, script syntax is validated only.

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0

run_test() {
    local name="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo "  PASS: $name (expected=$expected, actual=$actual)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (expected=$expected, actual=$actual)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Cron smoke tests (SC-007) ==="
echo "Project root: $PROJECT_ROOT"

# ── WSL detection ─────────────────────────────────────────────────────────────
IS_WSL=0
if grep -qi microsoft /proc/version 2>/dev/null; then
    IS_WSL=1
fi

if [ "$IS_WSL" -eq 1 ]; then
    echo ""
    echo "  WSL detected. Crontab persistence tests are skipped (known WSL/mnt limitation)."
    echo "  Running syntax-only validation instead."
    echo ""

    # T1: setup_cron.sh is valid bash
    if bash -n "$PROJECT_ROOT/scripts/setup_cron.sh" 2>/dev/null; then
        echo "  PASS: setup_cron.sh has valid bash syntax"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: setup_cron.sh has syntax errors"
        FAIL=$((FAIL + 1))
    fi

    # T2: remove_cron.sh is valid bash
    if bash -n "$PROJECT_ROOT/scripts/remove_cron.sh" 2>/dev/null; then
        echo "  PASS: remove_cron.sh has valid bash syntax"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: remove_cron.sh has syntax errors"
        FAIL=$((FAIL + 1))
    fi

    # T3: setup_cron.sh contains H0_CRON_MANAGED marker
    if grep -q "H0_CRON_MANAGED" "$PROJECT_ROOT/scripts/setup_cron.sh"; then
        echo "  PASS: setup_cron.sh contains H0_CRON_MANAGED marker"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: H0_CRON_MANAGED marker missing from setup_cron.sh"
        FAIL=$((FAIL + 1))
    fi

    # T4: setup_cron.sh contains directory guard
    if grep -q "Personal-AI-Employee-Hackathon-0" "$PROJECT_ROOT/scripts/setup_cron.sh"; then
        echo "  PASS: setup_cron.sh has directory guard"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: setup_cron.sh missing directory guard"
        FAIL=$((FAIL + 1))
    fi

    # T5: setup_cron.sh idempotency logic present (grep -v H0_CRON_MANAGED)
    if grep -q "grep -v.*H0_CRON_MANAGED" "$PROJECT_ROOT/scripts/setup_cron.sh"; then
        echo "  PASS: setup_cron.sh has idempotency guard (SC-007)"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: setup_cron.sh missing idempotency guard"
        FAIL=$((FAIL + 1))
    fi

else
    # ── Native Linux: full crontab integration tests ───────────────────────────

    # Clean slate
    crontab -l 2>/dev/null | grep -v "H0_CRON_MANAGED" | crontab - 2>/dev/null || true

    # T1: Run setup_cron.sh 3x → exactly 2 entries (idempotency, SC-007)
    bash "$PROJECT_ROOT/scripts/setup_cron.sh" > /dev/null 2>&1
    bash "$PROJECT_ROOT/scripts/setup_cron.sh" > /dev/null 2>&1
    bash "$PROJECT_ROOT/scripts/setup_cron.sh" > /dev/null 2>&1
    count=$(crontab -l 2>/dev/null | grep -c "H0_CRON_MANAGED" || echo 0)
    run_test "setup_cron.sh 3x → exactly 2 entries (SC-007)" 2 "$count"

    # T2: Entry contains absolute project path
    if crontab -l 2>/dev/null | grep "H0_CRON_MANAGED" | grep -q "Personal-AI-Employee-Hackathon-0"; then
        echo "  PASS: Entry contains absolute project path"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: Entry missing absolute project path"
        FAIL=$((FAIL + 1))
    fi

    # T3: Orchestrator runs every 15 minutes
    if crontab -l 2>/dev/null | grep "H0_CRON_MANAGED" | grep -q "\*/15"; then
        echo "  PASS: Orchestrator scheduled every 15 minutes"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: Orchestrator 15-minute schedule not found"
        FAIL=$((FAIL + 1))
    fi

    # T4: LinkedIn poster entry present
    if crontab -l 2>/dev/null | grep "H0_CRON_MANAGED" | grep -q "linkedin_poster"; then
        echo "  PASS: LinkedIn poster cron entry present"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: LinkedIn poster entry missing"
        FAIL=$((FAIL + 1))
    fi

    # T5: remove_cron.sh → 0 entries
    bash "$PROJECT_ROOT/scripts/remove_cron.sh" > /dev/null 2>&1
    count=$(crontab -l 2>/dev/null | grep -c "H0_CRON_MANAGED" || echo 0)
    run_test "remove_cron.sh → 0 entries" 0 "$count"
fi

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
