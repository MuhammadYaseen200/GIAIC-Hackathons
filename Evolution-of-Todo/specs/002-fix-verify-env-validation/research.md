# Research: verify-env.py Phase-Aware Validation

**Feature**: 002-fix-verify-env-validation
**Date**: 2026-01-27
**Status**: Complete

---

## 1. Python argparse Best Practices

### Decision
Use `argparse.ArgumentParser` with `add_argument('--phase', type=int, choices=[2, 3])` for CLI flag handling.

### Rationale
- Standard library solution (no external dependencies)
- Automatic help text generation (`--help`)
- Built-in type conversion and validation (`choices` parameter)
- Industry-standard for Python CLI tools

### Implementation Pattern
```python
import argparse

def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate development environment configuration"
    )
    parser.add_argument(
        '--phase',
        type=int,
        choices=[2, 3],
        required=False,
        help="Manually override phase detection (e.g., --phase 3)"
    )
    return parser.parse_args()
```

### Alternatives Considered
- **sys.argv manual parsing**: Rejected - error-prone, no type safety, no help generation
- **click library**: Rejected - external dependency, overkill for single optional argument
- **docopt**: Rejected - external dependency, less common in Python ecosystem

### References
- Python argparse documentation: https://docs.python.org/3/library/argparse.html
- Best practice: Use `type=int` + `choices` for enum-like arguments

---

## 2. Phase Detection via Directory Structure

### Decision
Use `Path.cwd() / 'phase-X-name'` with `.exists()` check to detect phase directories.

### Rationale
- Zero configuration required
- Works automatically when switching git branches
- Robust across operating systems (Path object handles platform differences)
- O(1) complexity (just directory existence checks)

### Implementation Pattern
```python
from pathlib import Path

def detect_phase():
    """Detect project phase by checking for phase-specific directories."""
    # Check in descending order (highest phase first)
    if (Path.cwd() / 'phase-3-chatbot').exists():
        return 3
    elif (Path.cwd() / 'phase-2-web').exists():
        return 2
    elif (Path.cwd() / 'phase-1-console').exists():
        return 1
    return None  # Generic mode
```

### Alternatives Considered
- **Config file (.verify-env.yaml)**: Rejected - requires manual configuration, reduces reusability
- **Environment variable (PROJECT_PHASE=3)**: Rejected - must be set manually before each run, error-prone
- **Git branch name parsing**: Rejected - assumes specific branch naming convention, fragile

### References
- pathlib.Path documentation: https://docs.python.org/3/library/pathlib.html
- Best practice: Use Path objects instead of os.path for modern Python

---

## 3. URL Validation: SQLite vs PostgreSQL

### Decision
Accept both `sqlite+aiosqlite://` and `postgresql+asyncpg://` URL schemes using urllib.parse.

### Rationale
- SQLAlchemy/asyncio convention: `<dialect>+<driver>://<connection>`
- Phase 3 uses SQLite for development, PostgreSQL for production
- Phase 2 uses PostgreSQL exclusively
- Generic mode accepts any format (maximum flexibility)

### Implementation Pattern
```python
from urllib.parse import urlparse

def check_url_format(url_str, allowed_schemes, var_name="DATABASE_URL"):
    """
    Validate URL format against allowed schemes.

    Args:
        url_str: URL string to validate
        allowed_schemes: List of allowed base schemes (e.g., ['sqlite', 'postgresql'])
        var_name: Variable name for error messages

    Returns:
        tuple: (success: bool, error_message: str | None)
    """
    if not url_str:
        return False, f"{var_name} is empty"

    try:
        parsed = urlparse(url_str)

        # Extract base scheme (before '+' if present)
        # Example: "sqlite+aiosqlite" → "sqlite"
        base_scheme = parsed.scheme.split('+')[0] if '+' in parsed.scheme else parsed.scheme

        if base_scheme not in allowed_schemes:
            return False, f"{var_name} scheme '{parsed.scheme}' not allowed for this phase (expected: {', '.join(allowed_schemes)})"

        # Additional validation for specific schemes
        if base_scheme in ['postgresql', 'postgres'] and not parsed.netloc:
            return False, f"{var_name} missing host/netloc (PostgreSQL requires full connection string)"

        return True, None
    except Exception as e:
        return False, f"{var_name} invalid format: {str(e)}"
```

### Database URL Formats

**SQLite** (Phase 3 development):
```
sqlite+aiosqlite:///./todo_app.db          # Relative path
sqlite+aiosqlite:////absolute/path/db.db   # Absolute path
```

**PostgreSQL** (Phase 2, Phase 3 production):
```
postgresql+asyncpg://user:pass@localhost:5432/dbname
postgresql+asyncpg://user:pass@ep-cool-name.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Generic Mode** (other projects):
- Accept any valid URL format
- Only check that URL parses successfully
- No scheme restrictions

### Alternatives Considered
- **Regex validation**: Rejected - brittle, hard to maintain, doesn't handle URL encoding
- **SQLAlchemy engine creation**: Rejected - external dependency, overkill for format validation
- **String startswith()**: Rejected - doesn't handle complex URL structures, encoding issues

### References
- SQLAlchemy database URLs: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls
- urllib.parse documentation: https://docs.python.org/3/library/urllib.parse.html

---

## 4. Graceful Dependency Handling: python-dotenv

### Decision
Try to import python-dotenv, catch ImportError, show warning, continue with os.getenv().

### Rationale
- Maximizes portability (script works without external dependencies)
- Users with python-dotenv get automatic .env loading
- Users without python-dotenv can export vars manually
- Warning message educates users about optional feature

### Implementation Pattern
```python
import os
from pathlib import Path

# Global flag for dependency availability
DOTENV_AVAILABLE = False

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
    # Load from root .env file
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not available, will show warning in main()
    pass

def main():
    if not DOTENV_AVAILABLE:
        print("⚠ python-dotenv not found - .env file will not be auto-loaded")
        print("   Install with: pip install python-dotenv")
        print()

    # Continue with validation using os.getenv()
    # ...
```

### Alternatives Considered
- **Require python-dotenv**: Rejected - adds setup friction, reduces portability
- **Auto-install with pip**: Rejected - requires network, might fail in restricted environments, unexpected behavior
- **Silent fallback**: Rejected - user might not realize why .env isn't loading

### References
- python-dotenv documentation: https://pypi.org/project/python-dotenv/
- Best practice: Graceful degradation for optional dependencies

---

## 5. Error Message Best Practices for CLI Tools

### Decision
Use structured format: `Error: [issue] | Fix: [command] | Context: [phase/var]`

### Rationale
- Actionable: Users know exactly what to do
- Scannable: Clear sections with separators
- Context-aware: Shows which phase profile is active
- Industry standard: Similar to cargo, npm, rust-analyzer error formats

### Implementation Pattern

**Success Output**:
```
============================================================
ENVIRONMENT VALIDATION
============================================================

[1/5] Checking environment variables...
   ✓ Environment variables

[2/5] Checking runtime versions...
   ✓ Python 3.13.9
   ✓ Node.js 24.11.1

============================================================
✅ VALIDATION PASSED
============================================================
```

**Failure Output**:
```
============================================================
ENVIRONMENT VALIDATION
============================================================

Detected Phase: 3 | Using Phase 3 profile

[1/5] Checking environment variables...
   ✗ Environment variables

============================================================
❌ VALIDATION FAILED

Issues found (3):

  1. DATABASE_URL
     Error: Missing required environment variable: DATABASE_URL
     Fix: Add DATABASE_URL to .env file
     Phase: 3 (requires sqlite+aiosqlite:// or postgresql+asyncpg://)

  2. OPENROUTER_API_KEY
     Error: Missing required environment variable: OPENROUTER_API_KEY
     Fix: Add OPENROUTER_API_KEY to .env file
     Phase: 3 (required for AI chatbot features)

  3. SECRET_KEY
     Error: Missing required environment variable: SECRET_KEY
     Fix: Generate with: openssl rand -hex 32
     Phase: 3 (required for JWT authentication)

============================================================
```

**Generic Mode Output**:
```
============================================================
ENVIRONMENT VALIDATION
============================================================

Generic validation mode (no phase detected)
Validating DATABASE_URL only

[1/1] Checking database configuration...
   ✓ DATABASE_URL present

============================================================
✅ VALIDATION PASSED
============================================================

Note: Only DATABASE_URL was validated. Other variables not checked in generic mode.
```

### Formatting Conventions
- **Emoji indicators**: ✓ (success), ✗ (failure), ⚠ (warning), ℹ (info)
- **Progress counters**: [1/5], [2/5], etc.
- **Section separators**: 60-character `=` lines
- **Indentation**: 2 spaces for sub-items, 4 spaces for detailed messages
- **Exit codes**: 0 (all pass), 1 (execution error), 2 (validation failure)

### Alternatives Considered
- **JSON output**: Rejected - harder to read for humans, overkill for simple validator
- **Minimal output**: Rejected - doesn't provide enough context for debugging
- **Verbose output**: Rejected - too noisy, slows down development workflow

### References
- Rust cargo error format: https://doc.rust-lang.org/cargo/reference/error-format.html
- Human-friendly CLI design: https://clig.dev/

---

## Summary

All research topics resolved with clear decisions and implementation patterns:

1. ✅ **argparse** for CLI flag handling (--phase)
2. ✅ **Path.cwd() / 'phase-X'** for directory-based phase detection
3. ✅ **urllib.parse + scheme validation** for flexible DATABASE_URL formats
4. ✅ **Try/except ImportError** for graceful python-dotenv handling
5. ✅ **Structured error messages** with actionable fixes

**No blockers remain**. All patterns use standard library, zero external dependencies required.

**Ready for Phase 1**: Data model and API contracts can now be defined based on these patterns.
