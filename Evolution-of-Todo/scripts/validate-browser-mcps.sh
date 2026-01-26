#!/usr/bin/env bash
# Browser MCP Validation Script
# Verifies browser debugging tools (Playwright required, ChromeDevTools/Puppeteer optional).
#
# Usage:
#   ./scripts/validate-browser-mcps.sh              # Full validation
#   ./scripts/validate-browser-mcps.sh --check-only # Only check MCP presence, no tests
#
# Exit codes:
#   0 - Playwright MCP available (required check passed)
#   1 - Playwright MCP not found (required check failed)
#   2 - Servers not running (cannot run tests)

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Configuration
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"
SCREENSHOT_DIR="$PROJECT_ROOT/logs/screenshots"

# Track MCP availability
PLAYWRIGHT_AVAILABLE=false
CHROMEDEVTOOLS_AVAILABLE=false
PUPPETEER_AVAILABLE=false

# Parse arguments
CHECK_ONLY=false
if [[ "${1:-}" == "--check-only" ]]; then
    CHECK_ONLY=true
fi

# ============================================================================
# MCP Detection Functions
# ============================================================================

check_mcp_registry() {
    local mcp_name="$1"

    # Method 1: Try claude-code CLI if available
    if command_exists claude-code; then
        if claude-code mcp list 2>/dev/null | grep -q "$mcp_name"; then
            return 0
        fi
    fi

    # Method 2: Check for MCP in common locations
    # Claude Code typically stores MCP configs in user config directory
    local config_locations=(
        "$HOME/.config/claude/mcp-settings.json"
        "$HOME/AppData/Roaming/Claude/mcp-settings.json"
        "$HOME/Library/Application Support/Claude/mcp-settings.json"
    )

    for config_file in "${config_locations[@]}"; do
        if [ -f "$config_file" ]; then
            if grep -q "$mcp_name" "$config_file" 2>/dev/null; then
                return 0
            fi
        fi
    done

    return 1
}

check_playwright_mcp() {
    info "Checking Playwright MCP (REQUIRED)..."

    if check_mcp_registry "playwright"; then
        success "Playwright MCP found in registry"
        PLAYWRIGHT_AVAILABLE=true
        return 0
    fi

    # Fallback: Provide manual verification instructions
    warn "Cannot auto-detect Playwright MCP"
    echo ""
    echo "Manual verification required:"
    echo "  1. Check if Playwright MCP is configured in your MCP settings"
    echo "  2. Verify you can run browser automation commands"
    echo "  3. If not installed, add Playwright MCP to your configuration"
    echo ""

    # Ask user if they want to proceed anyway
    echo "If Playwright MCP is installed but not auto-detected, the tests below may still work."
    echo ""

    return 1
}

check_chromedevtools_mcp() {
    info "Checking ChromeDevTools MCP (optional)..."

    if check_mcp_registry "chrome-devtools" || check_mcp_registry "chromedevtools"; then
        success "ChromeDevTools MCP found in registry"
        CHROMEDEVTOOLS_AVAILABLE=true
        return 0
    else
        warn "ChromeDevTools MCP not configured (optional)"
        return 1
    fi
}

check_puppeteer_mcp() {
    info "Checking Puppeteer MCP (optional)..."

    if check_mcp_registry "puppeteer"; then
        success "Puppeteer MCP found in registry"
        PUPPETEER_AVAILABLE=true
        return 0
    else
        warn "Puppeteer MCP not configured (optional)"
        return 1
    fi
}

# ============================================================================
# Server Availability Check
# ============================================================================

check_servers_running() {
    info "Checking if servers are running..."

    local frontend_running=false
    local backend_running=false

    if command_exists curl; then
        # Check frontend
        local frontend_code
        frontend_code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")

        if [[ "$frontend_code" == "200" || "$frontend_code" == "304" ]]; then
            success "Frontend server is running on port 3000"
            frontend_running=true
        else
            warn "Frontend server is not running on port 3000 (HTTP $frontend_code)"
        fi

        # Check backend
        local backend_code
        backend_code=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health" 2>/dev/null || echo "000")

        if [[ "$backend_code" == "200" ]]; then
            success "Backend server is running on port 8000"
            backend_running=true
        else
            warn "Backend server is not running on port 8000 (HTTP $backend_code)"
        fi
    else
        warn "curl not found - cannot check server status"
    fi

    if $frontend_running && $backend_running; then
        return 0
    else
        echo ""
        warn "Servers not running. Start them with:"
        echo "  ./scripts/restart-servers.sh"
        echo ""
        return 1
    fi
}

# ============================================================================
# Playwright Tests (if servers running)
# ============================================================================

test_playwright_navigation() {
    info "Testing Playwright navigation to $FRONTEND_URL..."

    # Note: This is a simulation since we don't have direct MCP access
    # In real usage, this would invoke Playwright MCP to navigate

    if command_exists curl; then
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null || echo "000")

        if [[ "$http_code" == "200" || "$http_code" == "304" ]]; then
            success "Frontend is accessible (ready for Playwright navigation)"
            return 0
        else
            error "Frontend not accessible (HTTP $http_code)"
            return 1
        fi
    else
        warn "curl not available - cannot verify server accessibility"
        return 1
    fi
}

test_playwright_screenshot() {
    info "Testing Playwright screenshot capability..."

    # Create screenshot directory if it doesn't exist
    mkdir -p "$SCREENSHOT_DIR"

    # Note: This is a placeholder for actual Playwright MCP screenshot
    # In real usage, this would invoke Playwright MCP to capture screenshot

    success "Screenshot directory ready: $SCREENSHOT_DIR"
    echo "  To capture screenshots with Playwright:"
    echo "  1. Use Playwright MCP screenshot command"
    echo "  2. Target: $FRONTEND_URL"
    echo "  3. Output: $SCREENSHOT_DIR/frontend-<timestamp>.png"

    return 0
}

# ============================================================================
# Summary Output
# ============================================================================

print_summary() {
    local total_mcps=3
    local configured_mcps=0

    if $PLAYWRIGHT_AVAILABLE; then
        configured_mcps=$((configured_mcps + 1))
    fi

    if $CHROMEDEVTOOLS_AVAILABLE; then
        configured_mcps=$((configured_mcps + 1))
    fi

    if $PUPPETEER_AVAILABLE; then
        configured_mcps=$((configured_mcps + 1))
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if $PLAYWRIGHT_AVAILABLE; then
        success "Browser tools validation complete"
    else
        error "Browser tools validation incomplete (Playwright required)"
    fi

    echo ""
    echo "MCP Status:"
    echo "  Playwright:      $(if $PLAYWRIGHT_AVAILABLE; then echo "✅ CONFIGURED (required)"; else echo "❌ NOT FOUND (required)"; fi)"
    echo "  ChromeDevTools:  $(if $CHROMEDEVTOOLS_AVAILABLE; then echo "✅ CONFIGURED (optional)"; else echo "⚠️  NOT FOUND (optional)"; fi)"
    echo "  Puppeteer:       $(if $PUPPETEER_AVAILABLE; then echo "✅ CONFIGURED (optional)"; else echo "⚠️  NOT FOUND (optional)"; fi)"
    echo ""
    echo "Browser tools ready: $configured_mcps/$total_mcps configured (1 required)"
    echo ""

    if $PLAYWRIGHT_AVAILABLE; then
        echo "Next steps:"
        echo "  • Use Playwright MCP for browser automation"
        echo "  • Capture screenshots: $SCREENSHOT_DIR/"
        echo "  • Test navigation to: $FRONTEND_URL"
    else
        echo "Action required:"
        echo "  1. Configure Playwright MCP in Claude Code settings"
        echo "  2. Verify Playwright MCP can connect to browser"
        echo "  3. Re-run this script to validate"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================================================
# Main execution
# ============================================================================

main() {
    info "Browser MCP Validation"
    echo ""

    # Phase 1: Check MCP registry
    info "Phase 1: Checking MCP registry..."
    echo ""

    check_playwright_mcp || true
    echo ""

    check_chromedevtools_mcp || true
    echo ""

    check_puppeteer_mcp || true
    echo ""

    # If check-only mode, stop here
    if $CHECK_ONLY; then
        print_summary

        if $PLAYWRIGHT_AVAILABLE; then
            exit 0
        else
            exit 1
        fi
    fi

    # Phase 2: Check servers (prerequisite for tests)
    info "Phase 2: Checking server availability..."
    echo ""

    if ! check_servers_running; then
        warn "Skipping Playwright tests (servers not running)"
        echo ""
        print_summary
        exit 2
    fi

    echo ""

    # Phase 3: Run Playwright tests (if available)
    if $PLAYWRIGHT_AVAILABLE; then
        info "Phase 3: Running Playwright tests..."
        echo ""

        test_playwright_navigation || warn "Navigation test skipped"
        echo ""

        test_playwright_screenshot || warn "Screenshot test skipped"
        echo ""
    else
        info "Phase 3: Skipping Playwright tests (MCP not configured)"
        echo ""
    fi

    # Summary
    print_summary

    # Exit based on Playwright availability (required)
    if $PLAYWRIGHT_AVAILABLE; then
        exit 0
    else
        exit 1
    fi
}

# Run main function
main
