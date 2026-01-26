# Research: Development Environment Setup Best Practices

**Feature**: 001-dev-env-setup
**Date**: 2026-01-26
**Purpose**: Research best practices for cross-platform automation scripts

## 1. Cross-Platform Process Management

### Decision
Use conditional logic to detect platform and apply appropriate commands:
- **Windows (PowerShell)**: `Get-Process` + `Stop-Process` or `netstat` + `taskkill`
- **Windows (Git Bash)**: `netstat` + `taskkill` (Windows commands via Git Bash)
- **Unix/WSL**: `lsof` + `kill`

### Rationale
- Git Bash on Windows can execute Windows commands (`tas kkill.exe`, `netstat.exe`)
- Platform detection via `uname` or `$OS SYSTEM` environment variable
- Graceful fallback if command not found

### Implementation Pattern
```bash
# Detect platform
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (Git Bash)
    PID=$(netstat -ano | grep ":3000" | awk '{print $5}' | head -1)
    if [ -n "$PID" ]; then
        taskkill //PID $PID //F
    fi
elif [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    # Unix/Linux/Mac
    PID=$(lsof -ti:3000)
    if [ -n "$PID" ]; then
        kill -9 $PID
    fi
fi
```

### Alternatives Considered
- **Pure PowerShell**: Requires users to run PowerShell exclusively (rejected - less flexible)
- **Node.js script**: Adds dependency, slower startup (rejected - unnecessary complexity)
- **Python script**: Same issues as Node.js (rejected)

---

## 2. Idempotent File Operations

### Decision
Use existence checks before removal and suppress errors for already-deleted directories:
```bash
# Safe removal pattern
if [ -d ".next" ]; then
    rm -rf .next
    echo "✓ Removed .next/"
else
    echo "ℹ .next/ already clean"
fi
```

### Rationale
- Prevents script failure when cache already clean
- Provides informative feedback (not silent)
- Supports "run multiple times" requirement (idempotent)

### Implementation Pattern
```bash
# Function for safe directory removal
safe_remove() {
    local dir=$1
    if [ -d "$dir" ]; then
        rm -rf "$dir"
        echo "✓ Removed $dir"
        return 0
    else
        echo "ℹ $dir already clean"
        return 0
    fi
}

# Usage
safe_remove "phase-3-chatbot/frontend/.next"
safe_remove "phase-3-chatbot/backend/__pycache__"
```

### Alternatives Considered
- **Silent removal with `-f` only**: No user feedback (rejected - less transparent)
- **Error on missing directory**: Breaks idempotency (rejected - violates AC-003 clarification)

---

## 3. Environment Validation Patterns

### Decision
Use Python script for validation with structured error reporting:
- Check environment variables exist and have valid formats
- Check version numbers meet minimum requirements
- Check CLI tools are in PATH
- Check database connectivity
- Exit with code 2 on validation failure (distinct from general error code 1)

### Rationale
- Python has better string validation libraries (`urllib.parse`, `re`)
- Version comparison easier with `packaging.version`
- Database connectivity check via `psycopg2` or `urllib.request`
- Structured error messages with suggested fixes

### Implementation Pattern
```python
#!/usr/bin/env python3
import os
import sys
import subprocess
from urllib.parse import urlparse

def check_env_var(name, required=True):
    value = os.getenv(name)
    if required and not value:
        print(f"❌ Missing required environment variable: {name}")
        return False
    return True

def check_version(command, min_version):
    try:
        result = subprocess.run([command, "--version"], capture_output=True, text=True)
        # Parse version and compare
        # ...
        return True
    except FileNotFoundError:
        print(f"❌ {command} not found in PATH")
        return False

def main():
    errors = []

    # Check env vars
    if not check_env_var("DATABASE_URL"):
        errors.append("DATABASE_URL")

    # Check versions
    if not check_version("python3", "3.13"):
        errors.append("Python version")

    if errors:
        print(f"\n❌ Validation failed: {len(errors)} errors")
        print("\nSuggested fixes:")
        for error in errors:
            print(f"  - {error}: [fix command]")
        sys.exit(2)  # Exit code 2 = validation failure

    print("✅ Environment validation passed")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

### Alternatives Considered
- **Pure Bash validation**: Limited string parsing, harder version comparison (rejected - less robust)
- **Soft validation (warnings only)**: Violates AC-005 fail-fast requirement (rejected)

---

## 4. Exit Code Conventions

### Decision
Use standard Unix exit codes with custom code for validation:
- **0**: Success - all operations completed
- **1**: General error - script failure, unexpected error
- **2**: Validation failure - environment issues detected (fail-fast)

### Rationale
- Standard conventions recognized by CI/CD tools and shell scripts
- Distinguishes validation failures from script bugs
- Allows calling scripts to handle validation failures differently

### Implementation Pattern
```bash
#!/usr/bin/env bash
set -e  # Exit on error

# Run validation
if ! ./scripts/verify-env.sh; then
    echo "❌ Environment validation failed - fix issues before proceeding"
    exit 2
fi

# Continue with operations
echo "✓ Validation passed, proceeding..."
exit 0
```

### Alternatives Considered
- **Single exit code (0/1)**: Cannot distinguish validation vs script errors (rejected - less informative)
- **Multiple error codes (3, 4, 5...)**: Overly complex for this use case (rejected - unnecessary)

---

## 5. Browser MCP Validation

### Decision
Use MCP registry inspection (if available) or test invocation:
```bash
# Option 1: Check MCP registry (if Claude Code provides CLI)
claude-code mcp list | grep "playwright"

# Option 2: Test invocation with simple operation
# (Requires MCP tool to accept test commands)
```

### Rationale
- Playwright MCP is required (AC-004 clarification)
- ChromeDevTools and Puppeteer are optional (warn if missing)
- Testing with actual navigation ensures MCP is working, not just installed

### Implementation Pattern
```bash
check_playwright_mcp() {
    echo "Checking Playwright MCP..."

    # Method 1: Try MCP list command
    if command -v claude-code &> /dev/null; then
        if claude-code mcp list | grep -q "playwright"; then
            echo "✓ Playwright MCP found in registry"
            return 0
        fi
    fi

    # Method 2: Manual check (fallback)
    echo "⚠ Cannot auto-detect MCP - manual verification required"
    echo "  1. Open Claude Code MCP settings"
    echo "  2. Verify 'playwright' MCP is enabled"
    echo "  3. Test by running a browser automation command"
    return 1
}
```

### Alternatives Considered
- **Skip MCP validation**: Violates AC-004 (rejected)
- **Require all 3 MCPs**: Violates clarification (Playwright required, others optional) (rejected)
- **Try direct Playwright CLI**: MCP ≠ Playwright CLI, different tools (rejected - incorrect validation)

---

## Summary

**Decisions Made**: 5/5 research questions answered
**Unknowns Remaining**: 0 (all NEEDS CLARIFICATION resolved)
**Ready for Phase 1**: ✅ Yes - proceed to script design

**Key Takeaways**:
1. Cross-platform support via conditional platform detection
2. Idempotent operations with existence checks
3. Python for robust environment validation
4. Standard exit codes (0/1/2)
5. MCP validation via registry inspection or manual verification

**Next Step**: Create `quickstart.md` and begin task generation
