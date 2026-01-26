#!/usr/bin/env bash
# Common utility functions for automation scripts
# Usage: source scripts/_common.sh

set -euo pipefail

# Output formatting functions
info() {
    echo "ℹ $*"
}

warn() {
    echo "⚠ $*" >&2
}

error() {
    echo "❌ $*" >&2
}

success() {
    echo "✅ $*"
}

# Safe directory removal (idempotent)
# Usage: safe_remove "/path/to/directory"
safe_remove() {
    local target="$1"
    if [ -d "$target" ]; then
        rm -rf "$target"
        success "Removed $target"
        return 0
    else
        info "$target already clean (not present)"
        return 0
    fi
}

# Platform detection
# Returns: "windows" (Git Bash/MSYS), "linux", "darwin" (macOS), or "unknown"
detect_platform() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        echo "windows"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "darwin"
    else
        echo "unknown"
    fi
}

# Kill process on port (cross-platform)
# Usage: kill_port 3000
kill_port() {
    local port="$1"
    local platform
    platform=$(detect_platform)

    if [[ "$platform" == "windows" ]]; then
        # Windows (Git Bash) - use netstat and taskkill
        local pid
        pid=$(netstat -ano 2>/dev/null | grep ":$port " | awk '{print $5}' | head -1 || true)
        if [ -n "$pid" ] && [ "$pid" != "0" ]; then
            taskkill //PID "$pid" //F 2>/dev/null || true
            success "Killed process on port $port (PID: $pid)"
        else
            info "No process running on port $port"
        fi
    else
        # Unix/Linux/Mac - use lsof and kill
        local pid
        pid=$(lsof -ti:$port 2>/dev/null || true)
        if [ -n "$pid" ]; then
            kill -9 "$pid" 2>/dev/null || true
            success "Killed process on port $port (PID: $pid)"
        else
            info "No process running on port $port"
        fi
    fi
}

# Check if command exists in PATH
# Usage: command_exists "pnpm"
command_exists() {
    command -v "$1" >/dev/null 2>&1
}
