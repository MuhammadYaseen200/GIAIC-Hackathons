#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Environment Validation Script
Validates development environment configuration before operations.

Exit Codes:
    0 - All validations passed
    2 - Validation failures detected (fail-fast)
    1 - Script execution error
"""

import argparse
import os
import sys
import subprocess
import re
from urllib.parse import urlparse
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Load from root .env file
    root_dir = Path(__file__).parent.parent
    env_path = root_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not available, expect env vars to be set externally
    print("Warning: python-dotenv not found - .env file will not be auto-loaded. Install with: pip install python-dotenv")

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# =============================================================================
# VALIDATION PROFILES
# =============================================================================
# Phase-aware validation profiles
# Each profile defines required/optional environment variables and allowed
# database formats for a specific project phase or generic mode (phase=None).
#
# Profile Structure:
#   - name: Human-readable profile name
#   - required: List of environment variables that MUST be present
#   - optional: List of environment variables that MAY be present
#                (no error if missing)
#   - database_formats: List of allowed DATABASE_URL base schemes
#                       (e.g., ['sqlite', 'postgresql'])
#                       Empty list [] means accept any valid URL scheme
#                       (generic mode)
#   - description: Brief description of this phase's technology stack
#
# Profiles:
#   - Phase 2 (Web): Full-stack web app with PostgreSQL and NextAuth
#   - Phase 3 (Chatbot): AI chatbot with OpenRouter, SQLite/PostgreSQL,
#                         custom JWT
#   - Generic (None): Fallback for unknown projects (DATABASE_URL only)
#
# Extension: To add a new phase, add a new entry to VALIDATION_PROFILES,
#            update detect_phase(), and update parse_args() --phase choices.
#            See specs/002-fix-verify-env-validation/contracts/
#            validation-profiles.yaml for the full contract definition.
# =============================================================================

VALIDATION_PROFILES = {
    2: {
        'name': 'Phase 2 Web',
        'required': ['DATABASE_URL', 'SECRET_KEY', 'NEXTAUTH_SECRET'],
        'optional': [],
        'database_formats': ['postgresql', 'postgres'],
        'description': 'Full-stack web application with PostgreSQL and NextAuth'
    },
    3: {
        'name': 'Phase 3 Chatbot',
        'required': ['DATABASE_URL', 'OPENROUTER_API_KEY', 'SECRET_KEY'],
        'optional': ['NEXTAUTH_SECRET', 'GEMINI_API_KEY'],
        'database_formats': ['sqlite', 'postgresql', 'postgres'],
        'description': 'AI chatbot with OpenRouter, SQLite/PostgreSQL, and custom JWT'
    },
    None: {
        'name': 'Generic',
        'required': ['DATABASE_URL'],
        'optional': [],
        'database_formats': [],  # Empty = accept any scheme
        'description': 'Generic validation for unknown projects (DATABASE_URL only)'
    }
}


def detect_phase():
    """
    Detect project phase by scanning for phase directories.

    Scans the current working directory for phase-specific folders in
    descending order (highest phase first). When multiple phase directories
    exist, returns the highest phase number found.

    Returns:
        int or None: Phase number (1, 2, 3) or None if no phase directories
                     found. Phase 1 (console) has minimal env requirements.
                     Returns None for generic validation mode.

    Examples:
        detect_phase()  # In project with phase-3-chatbot/ -> returns 3
        detect_phase()  # In project with phase-2-web/ only -> returns 2
        detect_phase()  # In generic project (no phase dirs) -> returns None
    """
    # Check directories in descending order (highest phase first)
    if (Path.cwd() / 'phase-3-chatbot').exists():
        return 3
    if (Path.cwd() / 'phase-2-web').exists():
        return 2
    if (Path.cwd() / 'phase-1-console').exists():
        return 1  # Phase 1 has minimal requirements, but return 1 for detection
    return None  # Generic mode - no phase directories found


def parse_args():
    """
    Parse command-line arguments for the environment validator.

    Supports a --phase flag that overrides automatic phase detection,
    allowing users to force a specific validation profile regardless
    of which phase directories exist in the project.

    Returns:
        argparse.Namespace: Parsed arguments with 'phase' attribute.
            phase (int or None): Phase number (2 or 3) if specified
            via --phase flag, or None if auto-detection should be used.

    Examples:
        parse_args()                  # No args -> phase=None (auto-detect)
        parse_args(['--phase', '2'])  # Force Phase 2 validation
        parse_args(['--phase', '3'])  # Force Phase 3 validation
    """
    parser = argparse.ArgumentParser(
        description='Validate development environment configuration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                  Auto-detect phase from directory structure
  %(prog)s --phase 2        Force Phase 2 validation profile
  %(prog)s --phase 3        Force Phase 3 validation profile

Exit Codes:
  0  All validations passed
  1  Script execution error
  2  Validation failures detected
'''
    )
    parser.add_argument(
        '--phase',
        type=int,
        choices=[2, 3],
        required=False,
        help='Manually override phase detection (2=Phase 2 Web, 3=Phase 3 Chatbot)'
    )
    return parser.parse_args()


def check_env_var(name, required=True):
    """
    Check if environment variable exists and has a value.

    Args:
        name: Environment variable name
        required: Whether the variable is required

    Returns:
        tuple: (bool success, str error_message)
    """
    value = os.getenv(name)
    if required and not value:
        return False, f"Missing required environment variable: {name}"
    return True, None


def check_url_format(url_str, var_name="DATABASE_URL", allowed_schemes=None):
    """
    Validate URL format for database connection strings.

    Parses the URL and extracts the base scheme (before '+' if present),
    then validates against the allowed schemes list. For PostgreSQL URLs,
    also verifies that a host/netloc is present.

    Args:
        url_str (str): URL string to validate (e.g.,
            'sqlite+aiosqlite:///./todo.db' or
            'postgresql+asyncpg://user:pass@host:5432/db').
        var_name (str): Variable name for error messages
            (default: 'DATABASE_URL').
        allowed_schemes (list or None): List of allowed URL base schemes
            (e.g., ['sqlite', 'postgresql']). If None or empty list,
            accept any valid URL scheme (used in generic mode).

    Returns:
        tuple: (bool success, str or None error_message).
            Returns (True, None) on success.
            Returns (False, 'error description') on failure.

    Examples:
        check_url_format('sqlite+aiosqlite:///./app.db',
                         allowed_schemes=['sqlite', 'postgresql'])
        # -> (True, None)

        check_url_format('mysql://localhost/db',
                         allowed_schemes=['postgresql'])
        # -> (False, 'DATABASE_URL must use one of ...')
    """
    if not url_str:
        return False, f"{var_name} is empty"

    try:
        parsed = urlparse(url_str)

        # T014: Extract base scheme (before '+' character if present)
        # Examples:
        #   'sqlite+aiosqlite://...' -> 'sqlite'
        #   'postgresql+asyncpg://...' -> 'postgresql'
        #   'postgresql://...' -> 'postgresql'
        full_scheme = parsed.scheme
        base_scheme = full_scheme.split('+')[0] if '+' in full_scheme else full_scheme

        # T015: Validate base scheme against allowed list (if specified)
        if allowed_schemes and len(allowed_schemes) > 0:
            if base_scheme not in allowed_schemes:
                # T016: Error message shows allowed formats for current phase
                allowed_str = ', '.join(allowed_schemes)
                return False, f"{var_name} must use one of these database formats: {allowed_str}. Found: {base_scheme}"

        # For PostgreSQL URLs, require host/netloc
        # SQLite URLs use file paths (no netloc required)
        if base_scheme in ['postgresql', 'postgres']:
            if not parsed.netloc:
                return False, f"{var_name} missing host/netloc for PostgreSQL URL"

        return True, None
    except Exception as e:
        return False, f"{var_name} invalid format: {str(e)}"


def check_version(command, min_version_str):
    """
    Check if a command's version meets minimum requirement.

    Args:
        command: Command to check (e.g., 'python3', 'node')
        min_version_str: Minimum version string (e.g., '3.13', '18.0')

    Returns:
        tuple: (bool success, str error_message, str current_version)
    """
    try:
        # Run command --version
        result = subprocess.run(
            [command, '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False, f"{command} version check failed", None

        # Extract version number from output
        version_output = result.stdout + result.stderr

        # Match version patterns like "3.13.0", "v18.20.0", etc.
        version_match = re.search(r'(\d+)\.(\d+)\.?(\d+)?', version_output)

        if not version_match:
            return False, f"Could not parse {command} version from: {version_output[:50]}", None

        # Parse current version
        major = int(version_match.group(1))
        minor = int(version_match.group(2))
        patch = int(version_match.group(3) or 0)
        current_version = f"{major}.{minor}.{patch}"

        # Parse minimum version
        min_parts = min_version_str.split('.')
        min_major = int(min_parts[0])
        min_minor = int(min_parts[1]) if len(min_parts) > 1 else 0

        # Compare versions
        if major < min_major or (major == min_major and minor < min_minor):
            return False, f"{command} version {current_version} < {min_version_str} (required)", current_version

        return True, None, current_version

    except FileNotFoundError:
        return False, f"{command} not found in PATH", None
    except subprocess.TimeoutExpired:
        return False, f"{command} version check timed out", None
    except Exception as e:
        return False, f"{command} version check error: {str(e)}", None


def check_cli_tools():
    """
    Check if required CLI tools are installed and accessible.

    Returns:
        list: List of (tool_name, success, error_message) tuples
    """
    tools = ['pnpm', 'uv', 'git']
    results = []

    for tool in tools:
        try:
            # Use 'where' on Windows, 'which' on Unix
            which_cmd = 'where' if sys.platform == 'win32' else 'which'
            result = subprocess.run(
                [which_cmd, tool],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                results.append((tool, True, None))
            else:
                results.append((tool, False, f"{tool} not found in PATH"))

        except Exception as e:
            results.append((tool, False, f"{tool} check error: {str(e)}"))

    return results


def check_database_connectivity(database_url):
    """
    Check if database is reachable (basic connectivity test).

    For PostgreSQL URLs, attempts a psycopg2 connection with timeout.
    For SQLite URLs, checks that the parent directory exists (file-based, no network).

    Args:
        database_url: Database connection URL (PostgreSQL or SQLite)

    Returns:
        tuple: (bool success, str error_message)
    """
    if not database_url:
        return False, "DATABASE_URL not set"

    # T024: Skip psycopg2 connectivity for SQLite URLs (file-based, no network)
    parsed = urlparse(database_url)
    base_scheme = parsed.scheme.split('+')[0] if '+' in parsed.scheme else parsed.scheme
    if base_scheme == 'sqlite':
        # SQLite is file-based - no network connectivity check needed
        # Verify the parent directory exists for the database file path
        db_path_str = parsed.path
        if db_path_str and db_path_str not in ['/', '']:
            # Remove leading slashes for relative paths like ///./todo_app.db
            clean_path = db_path_str.lstrip('/')
            if clean_path.startswith('./'):
                clean_path = clean_path[2:]
            parent_dir = Path(clean_path).parent
            if parent_dir != Path('.') and not parent_dir.exists():
                return False, f"SQLite database parent directory does not exist: {parent_dir}"
        return True, None

    try:
        # Try to import psycopg2 (optional - graceful fallback)
        try:
            import psycopg2

            # Strip SQLAlchemy driver suffix for psycopg2 compatibility
            # e.g., 'postgresql+asyncpg://...' -> 'postgresql://...'
            connect_url = database_url
            if '+' in parsed.scheme:
                connect_url = base_scheme + '://' + database_url.split('://', 1)[1]

            # Attempt connection with 5-second timeout
            conn = psycopg2.connect(connect_url, connect_timeout=5)
            conn.close()
            return True, None

        except ImportError:
            # psycopg2 not installed - skip database connectivity check
            return True, "psycopg2 not installed - skipping database connectivity check"

    except Exception as e:
        error_msg = str(e)
        # Check if it's a network/connection error vs bad credentials
        if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower():
            return False, f"Database unreachable: {error_msg}"
        else:
            return False, f"Database connection error: {error_msg}"


def main():
    """Main validation routine - collects all errors before failing."""
    errors = []
    warnings = []

    # T008: Detect project phase from directory structure
    detected_phase = detect_phase()

    # T009: Parse CLI arguments - CLI flag overrides auto-detection
    args = parse_args()
    phase = args.phase if args.phase is not None else detected_phase

    # T010: Load validation profile for this phase
    profile = VALIDATION_PROFILES.get(phase)

    if profile is None:
        # Fallback to generic mode if phase not recognized
        profile = VALIDATION_PROFILES[None]
        phase = None

    # T011/T012: Display phase information to user
    if phase is not None:
        print(f"\nDetected Phase: {phase} | Using {profile['name']} profile")
        print(f"Description: {profile['description']}\n")
    else:
        print("\nGeneric validation mode (no phase detected)")
        print("Validating DATABASE_URL only\n")

    print("=" * 60)
    print("ENVIRONMENT VALIDATION")
    print("=" * 60)
    print()

    # Check 1: Environment Variables
    print("[1/5] Checking environment variables...")

    # T017-T019/T021-T023: Use phase-specific required/optional vars from profile
    required_env_vars = profile.get('required', ['DATABASE_URL'])
    optional_env_vars = profile.get('optional', [])

    for var in required_env_vars:
        success, error = check_env_var(var, required=True)
        if not success:
            errors.append((var, error,
                           "Copy .env.example to .env and fill in values. "
                           "See specs/002-fix-verify-env-validation/quickstart.md "
                           "for setup examples"))

    for var in optional_env_vars:
        success, error = check_env_var(var, required=False)
        # Optional vars don't generate errors, just informational

    # Check DATABASE_URL format with phase-specific allowed schemes
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Get allowed database formats from profile
        allowed_db_formats = profile.get('database_formats', [])
        success, error = check_url_format(database_url, 'DATABASE_URL', allowed_schemes=allowed_db_formats)
        if not success:
            # Build phase-specific fix message with quickstart.md reference
            if allowed_db_formats:
                formats_str = ', '.join(allowed_db_formats)
                fix_msg = (f"Ensure DATABASE_URL uses one of: {formats_str}. "
                           "See specs/002-fix-verify-env-validation/quickstart.md "
                           "for format examples")
            else:
                fix_msg = ("Ensure DATABASE_URL is a valid database URL. "
                           "See specs/002-fix-verify-env-validation/quickstart.md "
                           "for format examples")
            errors.append(('DATABASE_URL format', error, fix_msg))

    print(f"   {'✓' if len([e for e in errors if 'DATABASE_URL' in e[0] or any(v in e[0] for v in required_env_vars)]) == 0 else '✗'} Environment variables")
    print()

    # Check 2: Runtime Versions
    print("[2/5] Checking runtime versions...")

    python_ok, python_err, python_ver = check_version('python3', '3.13')
    if not python_ok:
        errors.append(('Python version', python_err or 'Check failed', "Install Python 3.13+ from python.org"))
    else:
        print(f"   ✓ Python {python_ver}")

    node_ok, node_err, node_ver = check_version('node', '18.0')
    if not node_ok:
        errors.append(('Node.js version', node_err or 'Check failed', "Install Node.js 18+ from nodejs.org"))
    else:
        print(f"   ✓ Node.js {node_ver}")

    print()

    # Check 3: CLI Tools
    print("[3/5] Checking CLI tools...")

    tool_results = check_cli_tools()
    for tool, success, error in tool_results:
        if success:
            print(f"   ✓ {tool}")
        else:
            print(f"   ✗ {tool}")
            if tool == 'pnpm':
                fix = "npm install -g pnpm"
            elif tool == 'uv':
                fix = "Install uv from https://astral.sh/uv"
            elif tool == 'git':
                fix = "Install Git from git-scm.com"
            else:
                fix = f"Install {tool}"
            errors.append((f"{tool} CLI", error, fix))

    print()

    # Check 4: Database Connectivity
    print("[4/5] Checking database connectivity...")

    if database_url:
        db_ok, db_err = check_database_connectivity(database_url)
        if not db_ok:
            errors.append(('Database connectivity', db_err, "Check DATABASE_URL and network connection"))
            print("   ✗ Database unreachable")
        elif db_err and '⚠' in db_err:
            # Warning, not error
            warnings.append(db_err)
            print(f"   ⚠ {db_err}")
        else:
            print("   ✓ Database reachable")
    else:
        errors.append(('Database connectivity', 'DATABASE_URL not set', "Set DATABASE_URL in .env file"))
        print("   ✗ DATABASE_URL not set")

    print()

    # Check 5: Project Structure
    print("[5/5] Checking project structure...")

    project_root = Path(__file__).parent.parent
    required_dirs = ['phase-3-chatbot/frontend', 'phase-3-chatbot/backend']

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"   ✓ {dir_path}/")
        else:
            warnings.append(f"Directory not found: {dir_path}/")
            print(f"   ⚠ {dir_path}/ not found")

    print()
    print("=" * 60)

    # Display results
    if warnings:
        print()
        print("WARNINGS:")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if errors:
        print()
        print("❌ VALIDATION FAILED")
        print()
        print(f"Issues found ({len(errors)}):")
        print()

        for i, (category, error, fix) in enumerate(errors, 1):
            print(f"  {i}. {category}")
            print(f"     Error: {error}")
            print(f"     Fix: {fix}")
            print()

        print("Blocking all operations until fixed (fail-fast)")
        print("Troubleshooting: specs/002-fix-verify-env-validation/quickstart.md")
        print("=" * 60)
        sys.exit(2)  # Exit code 2 = validation failure

    print()
    print("✅ All validations passed")
    print("=" * 60)
    sys.exit(0)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
