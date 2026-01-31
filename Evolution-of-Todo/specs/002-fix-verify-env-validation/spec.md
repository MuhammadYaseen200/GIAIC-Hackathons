# Feature Specification: Fix verify-env.py Phase 3 Validation Mismatch

**Feature ID**: 002-fix-verify-env-validation
**Status**: Draft
**Created**: 2026-01-27
**Priority**: High (Blocking Phase 3 recovery)

---

## Problem Statement

The `scripts/verify-env.py` validation script has hardcoded environment variable requirements that don't match Phase 3's actual implementation:

**Current Validator Expects**:
- `DATABASE_URL` (PostgreSQL format with asyncpg)
- `OPENROUTER_API_KEY`
- `NEXTAUTH_SECRET` (for NextAuth library)

**Phase 3 Actually Uses**:
- `DATABASE_URL` (SQLite for development: `sqlite+aiosqlite:///./todo_app.db`)
- `OPENROUTER_API_KEY` (correct)
- Custom JWT authentication (NO NextAuth - uses `SECRET_KEY` instead)

**Impact**:
- Blocks dev-env-setup automation (`./scripts/dev-env-setup.sh` fails with exit code 2)
- False validation errors prevent legitimate development work
- Script unusable for other projects with different tech stacks
- Violates "reusable intelligence" principle from constitution

---

## User Requirements

### Functional Requirements

**FR-001: Phase-Aware Validation**
- Validator MUST detect which phase/project it's running in
- Validate only the environment variables relevant to that phase
- Support multiple validation profiles (Phase 2, Phase 3, Phase 4, etc.)

**FR-002: Flexible Database URL Support**
- Accept BOTH SQLite AND PostgreSQL DATABASE_URL formats
- SQLite: `sqlite+aiosqlite:///<path>`
- PostgreSQL: `postgresql+asyncpg://user:pass@host:port/db`

**FR-003: Auth Stack Detection**
- Auto-detect if project uses NextAuth vs custom JWT
- Check `NEXTAUTH_SECRET` only if NextAuth detected (presence of `.auth/` directory or `next-auth` in package.json)
- Check `SECRET_KEY` if custom JWT detected (FastAPI backend with JWT auth)

**FR-004: Dotenv Loading**
- Load `.env` file automatically (already added in previous fix)
- Support `python-dotenv` library if available
- Gracefully fallback to environment variables if `python-dotenv` not installed

**FR-005: Optional vs Required Variables**
- Mark some variables as "optional" based on context
- Provide clear guidance on which variables are critical vs nice-to-have

### Non-Functional Requirements

**NFR-001: Backward Compatibility**
- Existing Phase 2 projects must continue working without changes
- Phase 3 projects validate correctly
- Future phases (4, 5) easily add their own validation profiles

**NFR-002: Clear Error Messages**
- If validation fails, show EXACTLY which phase profile was detected
- Explain WHY each variable is required for that specific phase
- Provide actionable fix commands

**NFR-003: Reusability**
- User can copy this validator to other projects
- Easy to customize validation rules via config file or env vars
- Document extension points

---

## Proposed Solution

### Architecture Decision

**Selected: Phase Detection via Directory Structure (Option A)**

Rationale:
- Zero configuration required - works automatically when switching branches
- Most robust for multi-phase projects
- Aligns with existing project structure conventions
- Maximizes reusability across projects without manual setup

Implementation:
- Detect phase by checking for phase-specific directories
- If `phase-3-chatbot/` exists → Phase 3 validation profile
- If only `phase-2-web/` exists → Phase 2 validation profile
- If `phase-4-k8s/` exists → Phase 4 validation profile
- If none found → Generic validation mode (minimal requirements)

**Rejected Alternatives:**
- Option B (Config File): Rejected - requires manual configuration, reduces reusability
- Option C (Environment Variable): Rejected - requires manual export, error-prone

### Implementation Plan

1. **Refactor `check_env_var()` function**:
   - Add `phase` parameter
   - Add `optional` parameter
   - Return structured validation result

2. **Add phase detection function**:
   ```python
   def detect_phase():
       if (Path.cwd() / 'phase-3-chatbot').exists():
           return 3
       elif (Path.cwd() / 'phase-2-web').exists():
           return 2
       elif (Path.cwd() / 'phase-1-console').exists():
           return 1
       return None
   ```

3. **Create validation profiles**:
   ```python
   VALIDATION_PROFILES = {
       2: {
           'required': ['DATABASE_URL', 'SECRET_KEY', 'NEXTAUTH_SECRET'],
           'optional': [],
           'database_formats': ['postgresql+asyncpg'],
       },
       3: {
           'required': ['DATABASE_URL', 'OPENROUTER_API_KEY', 'SECRET_KEY'],
           'optional': ['NEXTAUTH_SECRET', 'GEMINI_API_KEY'],
           'database_formats': ['sqlite+aiosqlite', 'postgresql+asyncpg'],
       },
   }
   ```

4. **Update validation logic**:
   - Detect phase → Select profile → Validate only required vars
   - Accept any of the allowed `database_formats`
   - Show phase-specific error messages

5. **Add `--phase` CLI flag**:
   - Allow manual override: `./scripts/verify-env.py --phase 3`
   - Behavior: Override auto-detection completely, no warnings
   - If specified, skip auto-detection and use provided phase profile directly
   - Useful for testing, debugging, or when working in non-standard directory structures
   - Example: `./scripts/verify-env.py --phase 2` forces Phase 2 validation regardless of detected directories

---

## Acceptance Criteria

**AC-001: Phase 3 Validation Passes**
- Run `./scripts/verify-env.py` in Phase 3 branch
- MUST return exit code 0 (success)
- MUST NOT require `NEXTAUTH_SECRET`
- MUST accept SQLite DATABASE_URL

**AC-002: Phase 2 Still Works**
- Switch to Phase 2 branch
- Run `./scripts/verify-env.py`
- MUST still validate PostgreSQL and NextAuth

**AC-003: Clear Phase Detection**
- Output shows: "Detected Phase: 3"
- If detection fails, show: "Could not detect phase, using generic validation"

**AC-004: Database Format Flexibility**
- Accept `sqlite+aiosqlite:///./todo_app.db` (Phase 3)
- Accept `postgresql+asyncpg://user:pass@host:5432/db` (Phase 2/3)
- Reject invalid formats with clear error

**AC-005: Dotenv Loading Works**
- Place `.env` file in root
- Run validator
- MUST load variables from `.env`
- If `python-dotenv` missing, show warning but still try `os.getenv()`

**AC-006: Automation Unblocked**
- Run `./scripts/dev-env-setup.sh`
- MUST pass environment validation (exit code 0 on step 1/5)
- Continue to steps 2-5 (governance sync, cache cleanup, etc.)

---

## Out of Scope

- Validating actual database connectivity (already exists, keep as-is)
- Adding validation for Phase 4/5 (will add when those phases start)
- Creating a GUI for validation results
- Real-time monitoring of environment changes

---

## Edge Cases

1. **Multiple phases present** (e.g., both phase-2-web/ and phase-3-chatbot/)
   - Validate highest phase only (e.g., if Phase 2 and Phase 3 exist, use Phase 3 profile)
   - Show info message: "Detected phases: 2, 3 | Using Phase 3 profile"
   - Only validate requirements for highest phase (no merging of requirements)
   - Rationale: Simplifies validation, aligns with typical single-phase development workflow
   - Users can manually specify lower phase with `--phase` flag if needed

2. **No phase directories found**
   - Use generic validation mode (minimal requirements for maximum reusability)
   - Required: DATABASE_URL only (accept any format: SQLite, PostgreSQL, MySQL, etc.)
   - Optional: All other variables (SECRET_KEY, API keys, etc.) skipped
   - Show info: "Generic validation mode (no phase detected) - validating DATABASE_URL only"
   - Exit code 0 if DATABASE_URL present and valid format
   - Rationale: Maximizes reusability in other projects without assuming tech stack

3. **python-dotenv not installed**
   - Show warning: "⚠ python-dotenv not found - .env file will not be auto-loaded. Install with: pip install python-dotenv"
   - Continue validation using `os.getenv()` (assumes vars exported externally or loaded by shell)
   - Exit code 0 if validation passes (don't fail on missing dependency)
   - Rationale: Maximizes portability - validator works "out of the box" without requiring pip install
   - Users who have python-dotenv benefit from automatic .env loading, others export vars manually

4. **Mixed auth stacks** (NextAuth + JWT)
   - Check for BOTH `NEXTAUTH_SECRET` and `SECRET_KEY`
   - Warn if only one found: "Partial auth configuration detected"

---

## Clarifications

### Session 2026-01-27

- Q: Which architecture approach should be used for phase detection? → A: Option A (Phase Detection via Directory Structure)
- Q: What should generic validation mode require for unknown projects? → A: Option A (Minimal - DATABASE_URL only, any format)
- Q: When multiple phase directories exist, how should validator behave? → A: Option A (Validate highest phase only)
- Q: When python-dotenv is not installed, should the validator fail or continue? → A: Option A (Show warning and continue with os.getenv())
- Q: When user provides --phase flag, how should it interact with auto-detection? → A: Option A (Override completely, no warning)

---

## References

- Constitution Section VIII: Process Failure Prevention
- ADR-013: Fail-Fast Environment Validation
- Phase 3 Retrospective: "Environment validation failures caused 34-day overrun"
- `phase-3-chatbot/backend/.env` (actual Phase 3 configuration)
- `phase-3-chatbot/backend/CLAUDE.md` (documents JWT auth, not NextAuth)
