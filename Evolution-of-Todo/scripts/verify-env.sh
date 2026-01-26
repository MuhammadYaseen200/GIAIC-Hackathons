#!/usr/bin/env bash
# Environment validation wrapper script
# Calls Python validation script and propagates exit code
#
# Exit codes:
#   0 - All validations passed
#   2 - Validation failures detected (fail-fast)
#   1 - Script error

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Main execution
info "Running environment validation..."
echo ""

# Call Python validation script
if python3 "$SCRIPT_DIR/verify-env.py"; then
    echo ""
    success "Environment validation passed"
    exit 0
else
    EXIT_CODE=$?
    echo ""
    if [ $EXIT_CODE -eq 2 ]; then
        error "Environment validation failed - fix issues before proceeding (fail-fast)"
    else
        error "Validation script error (exit code: $EXIT_CODE)"
    fi
    exit $EXIT_CODE
fi
