#!/bin/bash
# Development Server Startup Script
# Auto-generated: 2026-02-07

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="E:/M.Y/GIAIC-Hackathons/Evolution-of-Todo"

echo "============================================================"
echo "Evolution of Todo - Development Servers"
echo "============================================================"

# Validate working directory
if [ "$PWD" != "$PROJECT_ROOT" ]; then
    echo -e "${RED}[ERROR] Wrong directory detected${NC}"
    echo "Current:  $PWD"
    echo "Required: $PROJECT_ROOT"
    echo ""
    echo "Run: cd '$PROJECT_ROOT' && ./scripts/start-dev-servers.sh"
    exit 3
fi

echo -e "${GREEN}[OK]${NC} Working directory validated"

# Test database connection
echo ""
echo "Testing Neon Database Connection..."
cd "$PROJECT_ROOT/phase-3-chatbot/backend"
if uv run python test_connections.py > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC} Database connection successful"
else
    echo -e "${RED}[ERR]${NC} Database connection failed"
    echo "Run: cd phase-3-chatbot/backend && uv run python test_connections.py"
    exit 1
fi

# Start backend server
echo ""
echo "============================================================"
echo "Starting Backend Server (FastAPI)"
echo "============================================================"
echo -e "${BLUE}[INFO]${NC} Backend URL: http://localhost:8000"
echo -e "${BLUE}[INFO]${NC} API Docs: http://localhost:8000/docs"
echo -e "${BLUE}[INFO]${NC} Press Ctrl+C to stop"
echo ""

cd "$PROJECT_ROOT/phase-3-chatbot/backend"
uv run uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

echo -e "${GREEN}[OK]${NC} Backend server started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
sleep 5

# Start frontend server
echo ""
echo "============================================================"
echo "Starting Frontend Server (Next.js)"
echo "============================================================"
echo -e "${BLUE}[INFO]${NC} Frontend URL: http://localhost:3000"
echo -e "${BLUE}[INFO]${NC} Press Ctrl+C to stop"
echo ""

cd "$PROJECT_ROOT/phase-3-chatbot/frontend"
pnpm dev &
FRONTEND_PID=$!

echo -e "${GREEN}[OK]${NC} Frontend server started (PID: $FRONTEND_PID)"

# Cleanup on exit
cleanup() {
    echo ""
    echo "============================================================"
    echo "Shutting down servers..."
    echo "============================================================"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}[OK]${NC} Servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
echo ""
echo "============================================================"
echo "Servers Running"
echo "============================================================"
echo -e "${GREEN}[OK]${NC} Backend:  http://localhost:8000"
echo -e "${GREEN}[OK]${NC} Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "============================================================"

wait
