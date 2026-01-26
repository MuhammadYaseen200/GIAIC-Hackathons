#!/usr/bin/env bash
# Cache Cleanup Script
# Removes build caches and runtime caches without touching lock files (default).
# Use --full flag to also remove dependencies (requires reinstall after).
#
# Exit codes:
#   0 - Cleanup completed successfully
#   1 - Error during cleanup

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Parse arguments
FULL_CLEANUP=false
if [[ "${1:-}" == "--full" ]]; then
    FULL_CLEANUP=true
    warn "FULL cleanup mode enabled - dependencies will be removed"
    warn "You will need to run 'pnpm install' and 'uv sync' after cleanup"
    echo ""
fi

# Track removed items
REMOVED_COUNT=0

# Main execution
if $FULL_CLEANUP; then
    info "Running FULL cleanup (caches + dependencies)..."
else
    info "Running QUICK cleanup (caches only)..."
fi
echo ""

# Frontend cleanup
info "[Frontend] Cleaning caches..."

# Quick mode: Remove build caches only
safe_remove "$PROJECT_ROOT/phase-3-chatbot/frontend/.next"
REMOVED_COUNT=$((REMOVED_COUNT + 1))

safe_remove "$PROJECT_ROOT/phase-3-chatbot/frontend/node_modules/.cache"
REMOVED_COUNT=$((REMOVED_COUNT + 1))

# Full mode: Also remove node_modules
if $FULL_CLEANUP; then
    safe_remove "$PROJECT_ROOT/phase-3-chatbot/frontend/node_modules"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
    info "pnpm-lock.yaml preserved (for reinstall)"
fi

echo ""

# Backend cleanup
info "[Backend] Cleaning caches..."

# Quick mode: Remove Python caches
# Find and remove all __pycache__ directories recursively
if [ -d "$PROJECT_ROOT/phase-3-chatbot/backend" ]; then
    PYCACHE_DIRS=$(find "$PROJECT_ROOT/phase-3-chatbot/backend" -type d -name "__pycache__" 2>/dev/null || true)
    if [ -n "$PYCACHE_DIRS" ]; then
        echo "$PYCACHE_DIRS" | while read -r dir; do
            if [ -d "$dir" ]; then
                rm -rf "$dir"
                REMOVED_COUNT=$((REMOVED_COUNT + 1))
            fi
        done
        success "Removed __pycache__/ directories"
    else
        info "__pycache__/ directories already clean"
    fi
fi

safe_remove "$PROJECT_ROOT/phase-3-chatbot/backend/.pytest_cache"
REMOVED_COUNT=$((REMOVED_COUNT + 1))

safe_remove "$PROJECT_ROOT/phase-3-chatbot/backend/.uv"
REMOVED_COUNT=$((REMOVED_COUNT + 1))

# Full mode: Also remove .venv
if $FULL_CLEANUP; then
    safe_remove "$PROJECT_ROOT/phase-3-chatbot/backend/.venv"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
    info "uv.lock preserved (for reinstall)"
fi

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
success "Cleanup complete"
echo ""

if $FULL_CLEANUP; then
    echo "Mode: FULL (caches + dependencies removed)"
    echo ""
    echo "Next steps:"
    echo "  1. Reinstall frontend dependencies:"
    echo "     cd phase-3-chatbot/frontend && pnpm install"
    echo ""
    echo "  2. Reinstall backend dependencies:"
    echo "     cd phase-3-chatbot/backend && uv sync"
else
    echo "Mode: QUICK (caches only)"
    echo ""
    echo "Preserved files:"
    echo "  ✓ pnpm-lock.yaml (frontend)"
    echo "  ✓ uv.lock (backend)"
    echo "  ✓ node_modules/ (frontend)"
    echo "  ✓ .venv/ (backend)"
fi

echo ""
echo "Total operations: $REMOVED_COUNT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit 0
