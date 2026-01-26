# ADR-013: Fail-Fast Environment Validation Strategy

**Status**: Accepted
**Date**: 2026-01-26
**Context**: Feature 001-dev-env-setup (Development Environment Readiness)
**Supersedes**: None
**Amended by**: None

## Context

During Phase 3 (AI Chatbot), the project experienced a 34-day overrun partially caused by invalid environment configurations that went undetected:

1. **Invalid `.env` values** (e.g., `HOST=0.0.0.0.1` instead of `HOST=0.0.0.0`) caused 2 days of debugging
2. **Missing environment variables** discovered mid-development wasted time on error tracing
3. **Wrong dependency versions** led to compatibility issues found after hours of work
4. **Stale cache issues** caused "works on my machine" problems

Constitution Principle VIII (Process Failure Prevention) was added specifically to address these failures:

> **DON'T** paste environment variables without validation
> **DON'T** trust cache (Next.js `.next` folder)
> **DON'T** skip environment validation

The project must decide: Should environment validation **warn** developers of issues (soft validation) or **block** all operations until issues are fixed (fail-fast)?

**Constraint**: Must align with Constitution Principle VIII and Phase 3 retrospective learnings.

## Decision

Implement **fail-fast environment validation** with blocking behavior:

1. **Validation Script** (`verify-env.sh`) runs FIRST in execution sequence (AC-005)
2. **Exit Code 2** for validation failures (distinct from general errors = exit code 1)
3. **Block ALL Operations** when validation fails - no warnings, no bypass, no "continue anyway"
4. **Structured Error Messages** with specific failures and suggested fix commands
5. **Comprehensive Checks**:
   - Environment variables exist and have valid formats (URLs, ports, hosts)
   - Runtime versions meet minimums (Python 3.13+, Node.js 18+)
   - CLI tools are installed (pnpm, uv, git)
   - Database connectivity verified (Neon PostgreSQL)

**Execution Sequence** (from `/sp.clarify`):
```
AC-005 (Validation) → AC-001 (Governance) → AC-002 (Cleanup) → AC-003 (Servers) → AC-004 (Browser MCPs)
```

**Failure Behavior**: If validation detects ANY issue, system MUST:
1. Display specific error messages for each failure
2. Provide suggested fix commands
3. Exit with code 2 (validation failure)
4. Block server startup and development operations until validation passes

## Consequences

### Positive

✅ **Prevents Time Waste**: Catches environment issues in seconds, not hours/days
✅ **Enforces Constitution**: Implements Principle VIII (Process Failure Prevention) exactly
✅ **Clear Feedback**: Developers know EXACTLY what's broken and how to fix it
✅ **Reduces "Works On My Machine"**: Validation ensures consistent environment across team
✅ **Protects Phase 4+**: Prevents repeat of Phase 3 environment-related delays
✅ **Fail-Fast Philosophy**: Errors discovered immediately, not mid-development
✅ **Scriptable**: CI/CD can use same validation (exit code 2 = environment issue)

### Negative

⚠️ **Friction for New Developers**: First-time setup blocked until all checks pass (mitigation: clear error messages with fix commands)
⚠️ **No "Quick Bypass"**: Cannot skip validation even for trivial changes (mitigation: this is intentional - prevents bad habits)
⚠️ **Dependency on External Services**: Database connectivity check requires Neon to be accessible (mitigation: graceful handling of temporary outages)

### Risks

- **False Positives**: Overly strict validation could block legitimate workflows (mitigation: validation rules based on actual Phase 3 failures)
- **Developer Frustration**: Strict blocking may feel heavy-handed (mitigation: Constitution mandates this after Phase 3 retrospective)
- **Network Dependencies**: Database check fails if network down (mitigation: clear error message distinguishes network vs config issues)

## Alternatives Considered

### Alternative 1: Soft Validation (Warnings Only)

**Approach**: Display warnings for validation failures but allow developer to proceed.

**Pros**:
- Less friction for experienced developers
- Faster for "quick experiments"
- Developers can bypass temporarily broken checks

**Cons**:
- ❌ **Violates Constitution Principle VIII**: "Block all operations on validation failure" explicitly required
- ❌ **Repeats Phase 3 Mistakes**: Soft warnings were ignored, leading to 34-day overrun
- ❌ **Creates Bad Habits**: Developers learn to ignore warnings, defeats purpose
- ❌ **No Enforcement**: Team members can skip validation, inconsistent environments

**Why Rejected**: Direct violation of Constitution mandateafter Phase 3 retrospective. Soft validation proven ineffective.

### Alternative 2: Tiered Validation (Critical vs Non-Critical)

**Approach**: Block on critical issues (missing DATABASE_URL), warn on non-critical issues (outdated versions).

**Pros**:
- Balances strictness with pragmatism
- Blocks major issues while allowing minor ones
- Reduces false positives from non-essential checks

**Cons**:
- ❌ **Ambiguity**: What's "critical" vs "non-critical" subjective and changes over time
- ❌ **Slippery Slope**: "Non-critical" warnings still ignored, same problem as Alternative 1
- ❌ **Maintenance Burden**: Must categorize every check, update categories as project evolves

**Why Rejected**: Complexity without clear benefit. Phase 3 failures included "minor" issues (version mismatches) that cascaded into major delays.

### Alternative 3: No Validation (Developer Responsibility)

**Approach**: Trust developers to configure environments correctly, no automated validation.

**Pros**:
- Zero friction, maximum flexibility
- No false positives
- Developers own their setup

**Cons**:
- ❌ **Proven Failure**: Phase 3 overrun directly caused by lack of validation
- ❌ **Violates Constitution**: Principle VIII explicitly mandates validation
- ❌ **Inconsistent Environments**: "Works on my machine" problems continue
- ❌ **Onboarding Friction**: New developers waste days debugging environment issues

**Why Rejected**: Directly contradicts Constitution and Phase 3 retrospective findings.

### Alternative 4: IDE Plugin Validation

**Approach**: Build validation into VS Code extension, check on file save or commit.

**Pros**:
- Integrated into developer workflow
- Real-time feedback
- Could prevent invalid `.env` files from being saved

**Cons**:
- ❌ **IDE-Specific**: Only works in VS Code, not other editors
- ❌ **Bypassable**: Developers can disable extension or use different editor
- ❌ **Development Overhead**: Requires building and maintaining VS Code extension
- ❌ **Doesn't Replace Script**: Still need script validation for CLI/CI/CD workflows

**Why Rejected**: IDE plugin is complementary, not a replacement. Script-based validation is universal and enforceable.

## Implementation Notes

**Validation Checks** (`verify-env.sh` Python script):

1. **Environment Variables**:
   ```python
   def check_env_var(name, format_validator=None):
       value = os.getenv(name)
       if not value:
           errors.append(f"Missing: {name}")
           return False
       if format_validator and not format_validator(value):
           errors.append(f"Invalid format: {name}={value}")
           return False
       return True
   ```

2. **Version Checking**:
   ```python
   def check_version(command, min_version):
       try:
           result = subprocess.run([command, "--version"], capture_output=True)
           current_version = parse_version_from_output(result.stdout)
           if current_version < min_version:
               errors.append(f"{command} {current_version} < {min_version}")
               return False
           return True
       except FileNotFoundError:
           errors.append(f"{command} not found in PATH")
           return False
   ```

3. **Database Connectivity**:
   ```python
   def check_database(url):
       try:
           # Attempt connection with 5-second timeout
           conn = psycopg2.connect(url, connect_timeout=5)
           conn.close()
           return True
       except Exception as e:
           errors.append(f"Database unreachable: {e}")
           return False
   ```

4. **Exit Codes**:
   - `0` = All checks passed
   - `2` = Validation failed (blocks operations)

**Error Message Format**:
```
❌ Environment validation failed

Issues found:
  1. Missing environment variable: DATABASE_URL
     Fix: cp .env.example .env in backend/ directory

  2. Python version 3.11 < 3.13 (required)
     Fix: Install Python 3.13 from python.org

  3. Command not found: pnpm
     Fix: npm install -g pnpm

Blocking all operations until fixed (fail-fast)
Exit code: 2
```

## References

- **Spec**: `specs/001-dev-env-setup/spec.md` (AC-005, Clarifications)
- **Plan**: `specs/001-dev-env-setup/plan.md` (Constitution Check, Phase 0 Research)
- **Research**: `specs/001-dev-env-setup/research.md` (Section 3: Environment Validation Patterns)
- **Constitution**: Principle VIII (Process Failure Prevention)
- **Phase 3 Retrospective**: `PHASE_3_RETROSPECTIVE.md` (environment validation failures)

## Related ADRs

- **ADR-012**: Cross-Platform Automation Stack (defines Python as validation engine)

## Revision History

- **2026-01-26**: Initial decision for 001-dev-env-setup feature
