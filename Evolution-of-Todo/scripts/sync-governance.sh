#!/usr/bin/env bash
# Governance File Synchronization Check
# Validates that AGENTS.md and ai-control/CLAUDE.md are properly cross-referenced
# and contain required workflow documentation.
#
# Exit codes:
#   0 - All governance checks passed
#   1 - Governance files out of sync

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Initialize error tracking
ERRORS=()

# Main execution
info "Checking governance file synchronization..."
echo ""

# Check 1: ai-control/CLAUDE.md references @AGENTS.md
info "[1/5] Checking CLAUDE.md → @AGENTS.md reference..."
if grep -q "@AGENTS.md" "$PROJECT_ROOT/ai-control/CLAUDE.md" 2>/dev/null; then
    success "✓ ai-control/CLAUDE.md references @AGENTS.md"
else
    error "✗ CLAUDE.md does not reference @AGENTS.md"
    ERRORS+=("ai-control/CLAUDE.md missing @AGENTS.md reference (line 3 expected)")
fi
echo ""

# Check 2: AGENTS.md contains Spec-Kit workflow documentation
info "[2/5] Checking AGENTS.md → Spec-Kit workflow..."
if grep -q "Spec-Kit" "$PROJECT_ROOT/AGENTS.md" 2>/dev/null; then
    # Verify specific workflow commands exist
    MISSING_CMDS=()
    for cmd in "/sp.specify" "/sp.plan" "/sp.tasks" "/sp.implement"; do
        if ! grep -q "$cmd" "$PROJECT_ROOT/AGENTS.md" 2>/dev/null; then
            MISSING_CMDS+=("$cmd")
        fi
    done

    if [ ${#MISSING_CMDS[@]} -eq 0 ]; then
        success "✓ AGENTS.md contains Spec-Kit workflow (/sp.specify, /sp.plan, /sp.tasks, /sp.implement)"
    else
        error "✗ AGENTS.md missing Spec-Kit commands: ${MISSING_CMDS[*]}"
        ERRORS+=("AGENTS.md incomplete Spec-Kit workflow documentation")
    fi
else
    error "✗ AGENTS.md does not contain Spec-Kit workflow"
    ERRORS+=("AGENTS.md missing Spec-Kit workflow section")
fi
echo ""

# Check 3: Constitution v2.0.0 referenced in both files
info "[3/5] Checking Constitution v2.0.0 references..."
AGENTS_HAS_V2=false
CLAUDE_HAS_V2=false

if grep -Eq "constitution.*v?2\.0\.0|v?2\.0\.0.*constitution" "$PROJECT_ROOT/AGENTS.md" 2>/dev/null; then
    AGENTS_HAS_V2=true
fi

if grep -Eq "constitution.*v?2\.0\.0|v?2\.0\.0.*constitution" "$PROJECT_ROOT/ai-control/CLAUDE.md" 2>/dev/null; then
    CLAUDE_HAS_V2=true
fi

if $AGENTS_HAS_V2 && $CLAUDE_HAS_V2; then
    success "✓ Constitution v2.0.0 referenced in both AGENTS.md and CLAUDE.md"
elif ! $AGENTS_HAS_V2 && ! $CLAUDE_HAS_V2; then
    error "✗ Constitution v2.0.0 missing in both files"
    ERRORS+=("Both files missing constitution v2.0.0 reference")
elif ! $AGENTS_HAS_V2; then
    error "✗ Constitution v2.0.0 missing in AGENTS.md"
    ERRORS+=("AGENTS.md missing constitution v2.0.0 reference")
else
    error "✗ Constitution v2.0.0 missing in CLAUDE.md"
    ERRORS+=("CLAUDE.md missing constitution v2.0.0 reference")
fi
echo ""

# Check 4: Agent team definitions consistent
info "[4/5] Checking agent team definitions..."
TEAMS=("Command Team" "Build Team" "Support Team")
AGENTS_TEAMS=()
CLAUDE_TEAMS=()

for team in "${TEAMS[@]}"; do
    if grep -q "$team" "$PROJECT_ROOT/AGENTS.md" 2>/dev/null; then
        AGENTS_TEAMS+=("$team")
    fi

    if grep -q "$team" "$PROJECT_ROOT/ai-control/CLAUDE.md" 2>/dev/null; then
        CLAUDE_TEAMS+=("$team")
    fi
done

if [ ${#AGENTS_TEAMS[@]} -eq 3 ] && [ ${#CLAUDE_TEAMS[@]} -eq 3 ]; then
    success "✓ Agent team definitions consistent (Command/Build/Support)"
else
    error "✗ Agent team definitions inconsistent"
    if [ ${#AGENTS_TEAMS[@]} -ne 3 ]; then
        ERRORS+=("AGENTS.md missing teams: $(printf '%s, ' "${TEAMS[@]}" | sed 's/, $//')")
    fi
    if [ ${#CLAUDE_TEAMS[@]} -ne 3 ]; then
        ERRORS+=("CLAUDE.md missing teams: $(printf '%s, ' "${TEAMS[@]}" | sed 's/, $//')")
    fi
fi
echo ""

# Check 5: Both files exist and are readable
info "[5/5] Checking file accessibility..."
FILES_OK=true

if [ ! -f "$PROJECT_ROOT/AGENTS.md" ]; then
    error "✗ AGENTS.md not found"
    ERRORS+=("AGENTS.md file missing")
    FILES_OK=false
fi

if [ ! -f "$PROJECT_ROOT/ai-control/CLAUDE.md" ]; then
    error "✗ ai-control/CLAUDE.md not found"
    ERRORS+=("ai-control/CLAUDE.md file missing")
    FILES_OK=false
fi

if $FILES_OK; then
    success "✓ Both governance files exist and are readable"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ ${#ERRORS[@]} -eq 0 ]; then
    success "Governance files synchronized"
    echo "✓ All 5 checks passed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    error "Governance files out of sync"
    echo ""
    echo "Issues found (${#ERRORS[@]}):"
    for i in "${!ERRORS[@]}"; do
        echo "  $((i+1)). ${ERRORS[$i]}"
    done
    echo ""
    echo "Fix: Update AGENTS.md and ai-control/CLAUDE.md to ensure consistency"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
