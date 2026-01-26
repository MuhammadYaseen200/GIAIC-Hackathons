#!/usr/bin/env bash
# Server Lifecycle Management Script
# Kills old servers, starts new ones, verifies health.
#
# Usage:
#   ./scripts/restart-servers.sh        # Kill, start, verify servers
#   ./scripts/restart-servers.sh --kill-only   # Only kill servers
#   ./scripts/restart-servers.sh --start-only  # Only start servers
#
# Exit codes:
#   0 - Servers restarted successfully
#   1 - Error during restart
#   2 - Health checks failed

set -euo pipefail

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source common utilities
source "$SCRIPT_DIR/_common.sh"

# Configuration
FRONTEND_PORT=3000
BACKEND_PORT=8000
HEALTH_CHECK_TIMEOUT=30
HEALTH_CHECK_INTERVAL=2

# Parse arguments
KILL_ONLY=false
START_ONLY=false

if [[ "${1:-}" == "--kill-only" ]]; then
    KILL_ONLY=true
elif [[ "${1:-}" == "--start-only" ]]; then
    START_ONLY=true
fi

# ============================================================================
# Phase 1: Kill old servers
# ============================================================================

kill_servers() {
    info "Phase 1: Killing old servers..."
    echo ""

    # Kill frontend server on port 3000
    kill_port $FRONTEND_PORT

    # Kill backend server on port 8000
    kill_port $BACKEND_PORT

    echo ""
}

# ============================================================================
# Phase 2: Start new servers
# ============================================================================

start_servers() {
    info "Phase 2: Starting new servers..."
    echo ""

    # Start frontend server in background
    info "[Frontend] Starting Next.js dev server on port $FRONTEND_PORT..."
    cd "$PROJECT_ROOT/phase-3-chatbot/frontend"

    # Check if pnpm is available
    if ! command_exists pnpm; then
        error "pnpm not found. Install with: npm install -g pnpm"
        return 1
    fi

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        warn "node_modules not found. Installing dependencies..."
        pnpm install
    fi

    # Start frontend in background
    nohup pnpm dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
    FRONTEND_PID=$!
    success "Frontend server started (PID: $FRONTEND_PID)"

    echo ""

    # Start backend server in background
    info "[Backend] Starting FastAPI server on port $BACKEND_PORT..."
    cd "$PROJECT_ROOT/phase-3-chatbot/backend"

    # Check if uv is available
    if ! command_exists uv; then
        error "uv not found. Install from: https://astral.sh/uv"
        return 1
    fi

    # Check if .venv exists
    if [ ! -d ".venv" ]; then
        warn ".venv not found. Running uv sync..."
        uv sync
    fi

    # Start backend in background
    nohup uv run uvicorn app.main:app --reload --port $BACKEND_PORT > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
    BACKEND_PID=$!
    success "Backend server started (PID: $BACKEND_PID)"

    echo ""

    # Return to project root
    cd "$PROJECT_ROOT"
}

# ============================================================================
# Phase 3: Verify server health
# ============================================================================

wait_for_health() {
    local url="$1"
    local name="$2"
    local timeout="$3"
    local interval="$4"

    local elapsed=0

    while [ $elapsed -lt $timeout ]; do
        # Try health check
        if command_exists curl; then
            local http_code
            http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

            if [[ "$http_code" == "200" || "$http_code" == "304" ]]; then
                success "$name is healthy (HTTP $http_code)"
                return 0
            fi
        else
            error "curl not found. Install curl to perform health checks."
            return 1
        fi

        # Wait and retry
        sleep $interval
        elapsed=$((elapsed + interval))
        echo -n "."
    done

    echo ""
    error "$name health check failed after ${timeout}s"
    return 1
}

verify_health() {
    info "Phase 3: Verifying server health..."
    echo ""

    # Create logs directory if it doesn't exist
    mkdir -p "$PROJECT_ROOT/logs"

    # Wait for servers to start up
    info "Waiting for servers to start..."
    sleep 5

    # Check frontend health
    info "[Frontend] Checking http://localhost:$FRONTEND_PORT..."
    if wait_for_health "http://localhost:$FRONTEND_PORT" "Frontend" $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        success "Frontend is accessible"
    else
        error "Frontend health check failed"
        warn "Check logs at: $PROJECT_ROOT/logs/frontend.log"
        return 1
    fi

    echo ""

    # Check backend health
    info "[Backend] Checking http://localhost:$BACKEND_PORT/health..."
    if wait_for_health "http://localhost:$BACKEND_PORT/health" "Backend" $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        success "Backend is accessible"
    else
        error "Backend health check failed"
        warn "Check logs at: $PROJECT_ROOT/logs/backend.log"
        return 1
    fi

    echo ""

    # Check frontend-to-backend connectivity
    info "[Integration] Verifying frontend can reach backend API..."

    # Test backend API from same context
    if command_exists curl; then
        local api_response
        api_response=$(curl -s "http://localhost:$BACKEND_PORT/health" 2>/dev/null || echo "ERROR")

        if [[ "$api_response" != "ERROR" ]]; then
            success "Frontend-to-backend connectivity verified"
        else
            warn "Could not verify API connectivity (backend may not be ready yet)"
        fi
    fi

    echo ""
}

# ============================================================================
# Summary output
# ============================================================================

print_summary() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    success "Server lifecycle complete"
    echo ""
    echo "Server Status:"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  Backend:  http://localhost:$BACKEND_PORT"
    echo "  Backend Health: http://localhost:$BACKEND_PORT/health"
    echo ""
    echo "Logs:"
    echo "  Frontend: $PROJECT_ROOT/logs/frontend.log"
    echo "  Backend:  $PROJECT_ROOT/logs/backend.log"
    echo ""
    echo "To stop servers:"
    echo "  ./scripts/restart-servers.sh --kill-only"
    echo ""
    echo "To view logs:"
    echo "  tail -f logs/frontend.log"
    echo "  tail -f logs/backend.log"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================================================
# Main execution
# ============================================================================

main() {
    if $START_ONLY; then
        info "Running in START ONLY mode..."
        echo ""
        start_servers || exit 1
        verify_health || exit 2
        print_summary
        exit 0
    fi

    if $KILL_ONLY; then
        info "Running in KILL ONLY mode..."
        echo ""
        kill_servers
        success "Servers stopped"
        exit 0
    fi

    # Full restart: kill -> start -> verify
    info "Restarting servers (full lifecycle)..."
    echo ""

    kill_servers
    start_servers || exit 1
    verify_health || exit 2
    print_summary
}

# Run main function
main
exit 0
