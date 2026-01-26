# ADR-012: Cross-Platform Automation Stack for Environment Management

**Status**: Accepted
**Date**: 2026-01-26
**Context**: Feature 001-dev-env-setup (Development Environment Readiness)
**Supersedes**: None
**Amended by**: None

## Context

The Evolution of Todo project requires automated environment setup and maintenance scripts to ensure developers have clean, properly configured environments before Phase 3/4 work. These scripts must:

1. Work across Windows (Git Bash/PowerShell), Unix (Linux/macOS), and WSL
2. Support idempotent operations (safe to run multiple times)
3. Perform complex validation (environment variables, versions, connectivity)
4. Kill/start processes on different platforms with different tooling
5. Provide informative feedback without silent failures

The team must choose a technology stack that balances cross-platform support, developer familiarity, and maintenance burden.

**Constraints**:
- Target platforms: Windows 10/11 (primary), Unix/macOS (secondary), WSL (tertiary)
- Must complete all operations in under 5 minutes
- Must not require additional runtime installations beyond project prerequisites (Python 3.13+, Node.js 18+)
- Scripts must be maintainable by developers with varying shell scripting experience

## Decision

Use a **hybrid automation stack**:

1. **Primary Language**: **Bash** for main scripts and orchestration
   - Compatible with Git Bash (Windows), Unix shells, WSL
   - Familiar to most developers
   - Excellent process management and file operations

2. **Validation Engine**: **Python 3.13+** for environment validation
   - Superior string parsing (`urllib.parse`, `re`)
   - Easy version comparison (`packaging.version`)
   - Database connectivity testing (`psycopg2`, `urllib.request`)
   - Cross-platform without shell syntax variations

3. **Fallback/Alternative**: **PowerShell** (optional, for Windows-specific operations if needed)
   - Available on all Windows systems
   - Not required for core functionality

**Technology Cluster**:
- **Scripting**: Bash (primary) + Python (validation)
- **Process Management**: `netstat` + `taskkill` (Windows), `lsof` + `kill` (Unix)
- **File Operations**: Standard shell utilities (`rm`, `find`, `cat`, `grep`)
- **Platform Detection**: `$OSTYPE` environment variable with conditional branching

## Consequences

### Positive

✅ **Cross-Platform Support**: Bash works on Git Bash (Windows), Unix, macOS, WSL without modification
✅ **Idempotency**: Bash conditional checks (`if [ -d ]`) make safe, repeatable operations easy
✅ **Developer Familiarity**: Most developers know Bash basics; Python validation is readable
✅ **No Additional Dependencies**: Uses existing project dependencies (Python 3.13+)
✅ **Robust Validation**: Python provides better string parsing and version comparison than pure Bash
✅ **Clear Separation**: Bash for orchestration/operations, Python for complex validation logic
✅ **Maintainability**: Standard patterns (functions, exit codes) documented in research.md

### Negative

⚠️ **Windows Git Bash Dependency**: Windows users must have Git Bash installed (acceptable - already project requirement)
⚠️ **Two Languages**: Requires familiarity with both Bash and Python (mitigated: Python only for one script)
⚠️ **Platform-Specific Code Paths**: Conditional logic needed for Windows vs Unix process management
⚠️ **Limited IDE Support**: Bash has weaker IDE tooling compared to JavaScript/Python

### Risks

- **Git Bash Availability**: If Git Bash unavailable on Windows, scripts fail (mitigation: documented prerequisite)
- **Shell Variations**: Different Bash versions may behave differently (mitigation: use POSIX-compliant patterns)
- **Maintenance Burden**: Mixed language stack requires context switching (mitigation: clear separation of concerns)

## Alternatives Considered

### Alternative 1: Pure PowerShell

**Approach**: Write all scripts in PowerShell for Windows-first development.

**Pros**:
- Native Windows tooling, no Git Bash dependency
- Rich object pipeline, better error handling
- Strong IDE support (VS Code PowerShell extension)

**Cons**:
- ❌ **Not cross-platform**: Requires PowerShell Core on Unix (another dependency)
- ❌ **Team familiarity**: Fewer developers comfortable with PowerShell syntax
- ❌ **Verbosity**: PowerShell syntax more verbose than Bash for simple operations
- ❌ **WSL compatibility**: PowerShell on WSL adds complexity

**Why Rejected**: Cross-platform requirement prioritizes Bash (works everywhere) over PowerShell (requires additional setup on Unix).

### Alternative 2: Node.js Scripts

**Approach**: Write scripts in JavaScript using Node.js with libraries like `shelljs` or `execa`.

**Pros**:
- Cross-platform by design
- Team already uses Node.js (frontend)
- Rich package ecosystem (process management, file operations)

**Cons**:
- ❌ **Slower Startup**: Node.js VM startup overhead (~500ms) for each script
- ❌ **Additional Dependency**: Requires `node_modules/` for script dependencies
- ❌ **Overhead**: Too heavyweight for simple file/process operations
- ❌ **Development Friction**: Requires `package.json`, dependency management for scripts

**Why Rejected**: Unnecessary complexity and slower startup for simple automation tasks. Bash is lightweight and instant.

### Alternative 3: Pure Python

**Approach**: Write all scripts in Python using `subprocess`, `os`, `pathlib`.

**Pros**:
- Single language (simpler mental model)
- Cross-platform
- Team already uses Python (backend)

**Cons**:
- ❌ **Verbosity**: More lines of code for simple operations (file deletion, process management)
- ❌ **Shell Integration**: Harder to compose with shell commands and pipes
- ❌ **Less Idiomatic**: Bash is the standard for automation scripts in Unix ecosystem

**Why Rejected**: Bash is more concise and idiomatic for shell automation. Python reserved for complex validation where its strengths shine.

### Alternative 4: Make/Makefile

**Approach**: Use `Makefile` with targets for each operation.

**Pros**:
- Standard build automation tool
- Simple syntax for target dependencies

**Cons**:
- ❌ **Limited Logic**: Makefiles not designed for complex conditional logic
- ❌ **Cross-Platform Issues**: `make` syntax varies (GNU make vs BSD make)
- ❌ **No Built-in Validation**: Still requires external scripts for validation

**Why Rejected**: Makefiles good for build steps, not complex validation and process management workflows.

## Implementation Notes

**Key Patterns** (documented in `specs/001-dev-env-setup/research.md`):

1. **Platform Detection**:
   ```bash
   if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
       # Windows (Git Bash)
       taskkill //PID $PID //F
   elif [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
       # Unix/Linux/Mac
       kill -9 $PID
   fi
   ```

2. **Idempotent File Operations**:
   ```bash
   safe_remove() {
       if [ -d "$1" ]; then
           rm -rf "$1"
           echo "✓ Removed $1"
       else
           echo "ℹ $1 already clean"
       fi
   }
   ```

3. **Exit Code Conventions**:
   - `0` = Success
   - `1` = General error
   - `2` = Validation failure (fail-fast)

4. **Python Validation** (single script: `verify-env.sh`):
   - Environment variable existence and format validation
   - Version comparison (Python 3.13+, Node.js 18+)
   - Database connectivity testing
   - Structured error reporting with suggested fixes

## References

- **Plan**: `specs/001-dev-env-setup/plan.md` (Technical Context)
- **Research**: `specs/001-dev-env-setup/research.md` (Sections 1, 2, 4, 5)
- **Constitution**: Principle VIII (Process Failure Prevention)
- **Spec**: `specs/001-dev-env-setup/spec.md` (AC-002, AC-003, AC-005)

## Related ADRs

- None (first ADR for automation tooling)

## Revision History

- **2026-01-26**: Initial decision for 001-dev-env-setup feature
