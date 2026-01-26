#!/usr/bin/env bash
# Development Environment Setup - Main Orchestration Script
# Executes all 5 environment readiness operations in mandatory sequence.
#
# Usage:
#   ./scripts/dev-env-setup.sh              # Quick mode (caches only)
#   ./scripts/dev-env-setup.sh --full       # Full mode (caches + dependencies)
#
# Exit codes:
#   0 - All operations successful
#   1 - One or more operations failed
#   2 - Environment validation failed (fail-fast)

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Parse arguments
FULL_FLAG=""
if [[ "${1:-}" == "--full" ]]; then
    FULL_FLAG="--full"
fi

# Track operations
TOTAL_OPERATIONS=5
SUCCESSFUL_OPERATIONS=0
FAILED_OPERATIONS=0

# ============================================================================
# Progress Display
# ============================================================================

show_progress() {
    local step="$1"
    local message="$2"
    echo ""
    echo "🔍 [$step/$TOTAL_OPERATIONS] $message"
}

# ============================================================================
# Operation Execution Functions
# ============================================================================

run_operation() {
    local operation_name="$1"
    local script_path="$2"
    shift 2
    local args=("$@")

    # Run the script with args
    if "${script_path}" "${args[@]}"; then
        SUCCESSFUL_OPERATIONS=$((SUCCESSFUL_OPERATIONS + 1))
        return 0
    else
        local exit_code=$?
        FAILED_OPERATIONS=$((FAILED_OPERATIONS + 1))
        error "$operation_name failed (exit code: $exit_code)"
        return $exit_code
    fi
}

# ============================================================================
# Main Orchestration
# ============================================================================

main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    info "Development Environment Setup"
    if [[ -n "$FULL_FLAG" ]]; then
        warn "Running in FULL mode (dependencies will be removed)"
    else
        info "Running in QUICK mode (caches only)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # ========================================================================
    # Step 1/5: AC-005 Environment Validation (FAIL-FAST)
    # ========================================================================

    show_progress 1 "Running environment validation..."

    if ! run_operation "Environment validation" "$SCRIPT_DIR/verify-env.sh"; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        error "Environment validation failed - fix issues before proceeding (fail-fast)"
        echo ""
        echo "Fix the issues reported above and re-run:"
        echo "  ./scripts/dev-env-setup.sh"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        exit 2
    fi

    # ========================================================================
    # Step 2/5: AC-001 Governance File Synchronization
    # ========================================================================

    show_progress 2 "Checking governance file synchronization..."

    if ! run_operation "Governance sync" "$SCRIPT_DIR/sync-governance.sh"; then
        warn "Governance sync failed - continuing with caution"
        # Don't exit - this is not critical enough to stop
    fi

    # ========================================================================
    # Step 3/5: AC-002 Cache & Dependency Cleanup
    # ========================================================================

    show_progress 3 "Cleaning caches $(if [[ -n "$FULL_FLAG" ]]; then echo "(FULL mode)"; else echo "(quick mode)"; fi)..."

    if ! run_operation "Cache cleanup" "$SCRIPT_DIR/clean-caches.sh" $FULL_FLAG; then
        warn "Cache cleanup failed - continuing with caution"
        # Don't exit - can proceed with dirty caches if needed
    fi

    # ========================================================================
    # Step 4/5: AC-003 Server Lifecycle Management
    # ========================================================================

    show_progress 4 "Restarting development servers..."

    if ! run_operation "Server restart" "$SCRIPT_DIR/restart-servers.sh"; then
        warn "Server restart failed - some services may not be running"
        # Don't exit - can proceed without servers for some tasks
    fi

    # ========================================================================
    # Step 5/5: AC-004 Browser Debugging Tools Validation
    # ========================================================================

    show_progress 5 "Validating browser debugging tools..."

    if ! run_operation "Browser MCP validation" "$SCRIPT_DIR/validate-browser-mcps.sh"; then
        warn "Browser MCP validation failed - some tools may not be configured"
        # Don't exit - can proceed without browser tools for some tasks
    fi

    # ========================================================================
    # Final Summary
    # ========================================================================

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ $FAILED_OPERATIONS -eq 0 ]; then
        success "Environment setup complete!"
        echo "   $SUCCESSFUL_OPERATIONS/$TOTAL_OPERATIONS operations successful"
        echo "   Ready for development"
    else
        warn "Environment setup completed with warnings"
        echo "   $SUCCESSFUL_OPERATIONS/$TOTAL_OPERATIONS operations successful"
        echo "   $FAILED_OPERATIONS/$TOTAL_OPERATIONS operations failed"
        echo ""
        echo "Some operations failed but environment may still be usable."
        echo "Review the errors above and fix as needed."
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Exit with appropriate code
    if [ $FAILED_OPERATIONS -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main
