# Implementation Plan: Fix verify-env.py Phase 3 Validation Mismatch

**Branch**: `004-phase3-chatbot` | **Date**: 2026-01-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-fix-verify-env-validation/spec.md`

## Summary

Refactor `scripts/verify-env.py` to support phase-aware validation profiles, enabling it to automatically detect the current project phase (Phase 2, Phase 3, etc.) and validate only the appropriate environment variables. This fixes the current blocker where Phase 3's SQLite + custom JWT setup fails validation designed for Phase 2's PostgreSQL + NextAuth stack, while maintaining backward compatibility and maximizing reusability for other projects.

**Primary Goal**: Unblock Phase 3 dev-env-setup automation by making validator phase-aware
**Technical Approach**: Directory-based phase detection with profile-specific validation rules

---

## Technical Context

**Language/Version**: Python 3.13+ (existing script)
**Primary Dependencies**:
- `python-dotenv` (optional - graceful fallback if missing)
- Standard library: `os`, `sys`, `subprocess`, `argparse`, `pathlib`, `urllib.parse`, `re`

**Storage**: N/A (script reads environment variables + .env files)
**Testing**: Manual testing across Phase 2, Phase 3, and generic mode scenarios
**Target Platform**: Cross-platform (Windows Git Bash, WSL, Unix/macOS)
**Project Type**: Single Python script within monorepo

**Performance Goals**:
- Validation completes in <1 second
- Exit immediately on critical failures (fail-fast principle)

**Constraints**:
- Must maintain backward compatibility with Phase 2 projects
- Must work without python-dotenv dependency
- Must not require manual configuration (zero-config auto-detection)
- Must be copy-pasteable to other projects

**Scale/Scope**:
- Single 350-line Python script (`scripts/verify-env.py`)
- 3-5 validation profiles (Phase 2, Phase 3, generic, future phases)
- ~10 total environment variables validated across all profiles

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ **Principle I: Spec-Driven Development**
- **Status**: PASS
- **Evidence**: Complete specification exists at `specs/002-fix-verify-env-validation/spec.md` with 5 functional requirements, 3 non-functional requirements, 6 acceptance criteria, and 4 edge cases
- **Traceability**: All code changes will reference task IDs from `/sp.tasks`

### ✅ **Principle II: Iterative Evolution (Brownfield Protocol)**
- **Status**: PASS
- **Evidence**: Refactoring existing `scripts/verify-env.py` (not creating new file), preserving all existing functionality
- **Backward Compatibility**: Phase 2 validation must continue working (AC-002)

### ✅ **Principle III: Test-First Mindset**
- **Status**: PASS
- **Evidence**: 6 acceptance criteria defined with clear pass/fail conditions (AC-001 through AC-006)
- **Verification**: Manual testing steps documented for each phase

### ✅ **Principle IV: Smallest Viable Diff**
- **Status**: PASS
- **Evidence**: Changes limited to verify-env.py only, no feature creep beyond phase-aware validation

### ✅ **Principle V: Intelligence Capture**
- **Status**: PASS
- **Evidence**: PHR-330 documents clarification workflow, this plan documents design decisions, ADR-013 referenced for fail-fast validation principle

### ✅ **Principle VIII: Process Failure Prevention**
- **Status**: PASS
- **Evidence**: Addresses root cause from Phase 3 retrospective ("environment validation failures caused 34-day overrun")

### ⚠️ **NFR-003: Reusability** (Constitution Principle V)
- **Status**: ATTENTION REQUIRED
- **Justification**: Generic validation mode added specifically for reusability in other projects (DATABASE_URL-only validation when no phase detected)
- **Rationale**: Maximizes constitution's "reusable intelligence" mandate

---

## Project Structure

### Documentation (this feature)

```text
specs/002-fix-verify-env-validation/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/sp.plan output)
├── research.md          # Phase 0 output (patterns, best practices)
├── data-model.md        # Phase 1 output (validation profiles structure)
├── quickstart.md        # Phase 1 output (usage examples)
├── contracts/           # Phase 1 output (validation API contract)
│   └── validation-profiles.yaml
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
scripts/
├── verify-env.py        # MODIFIED - Primary implementation file
├── _common.sh           # Unchanged - Shared bash utilities
├── dev-env-setup.sh     # Unchanged - Orchestrator (calls verify-env.py)
└── README.md            # MODIFIED - Update usage documentation

.env                     # CREATED (if missing) - Root environment file
.env.example             # MODIFIED - Document new usage patterns

tests/
└── verify-env/          # CREATED - Test validation scenarios
    ├── test_phase2.sh
    ├── test_phase3.sh
    └── test_generic.sh
```

**Structure Decision**: Single-script modification with comprehensive testing. No new dependencies, no new files except optional test scripts for manual verification.

---

## Complexity Tracking

> No constitution violations. This section intentionally left blank as all gates pass.

---

## Phase 0: Research & Design Patterns

### Research Topics

1. **Python argparse Best Practices** (for `--phase` CLI flag)
   - Task: Research argparse usage patterns for optional integer arguments
   - Output: Document in `research.md` - argparse.ArgumentParser with `add_argument('--phase', type=int, choices=[2, 3])`

2. **Phase Detection Patterns** (directory-based detection)
   - Task: Research robust directory existence checking with pathlib
   - Output: Document in `research.md` - `Path.cwd() / 'phase-X-name'` pattern with `.exists()` check

3. **URL Validation Patterns** (SQLite vs PostgreSQL)
   - Task: Research urllib.parse patterns for validating both SQLite and PostgreSQL URLs
   - Output: Document in `research.md` - Accept `sqlite+aiosqlite://` and `postgresql+asyncpg://` schemes

4. **Graceful Dependency Handling** (python-dotenv)
   - Task: Research try/except ImportError pattern for optional dependencies
   - Output: Document in `research.md` - Try import, catch ImportError, show warning, continue

5. **Error Message Best Practices** (actionable, phase-specific)
   - Task: Research CLI error message formatting for developer tools
   - Output: Document in `research.md` - Format: "Error: [issue] | Fix: [command] | Phase: [X]"

**Deliverable**: `research.md` with all unknowns resolved

---

## Phase 1: Data Model & Contracts

### Data Model

**Entity**: ValidationProfile
- `phase_id`: int (2, 3, or None for generic)
- `phase_name`: str ("Phase 2 Web", "Phase 3 Chatbot", "Generic")
- `required_vars`: list[str] (environment variables that MUST exist)
- `optional_vars`: list[str] (environment variables that MAY exist)
- `database_formats`: list[str] (allowed DATABASE_URL schemes)
- `description`: str (displayed to user when validation runs)

**Entity**: ValidationResult
- `success`: bool (overall validation status)
- `phase_detected`: int | None (which phase was auto-detected)
- `phase_used`: int | None (which profile was used for validation)
- `errors`: list[tuple[str, str, str]] (var_name, error_msg, fix_hint)
- `warnings`: list[str] (non-critical issues)

**Deliverable**: `data-model.md` with entity definitions

### API Contract

**Input Contract** (CLI Arguments):
```yaml
arguments:
  - name: --phase
    type: integer
    required: false
    choices: [2, 3]
    description: "Manually override phase detection"
    example: "./scripts/verify-env.py --phase 3"

environment_variables:
  # Loaded from .env file (if python-dotenv available) or shell environment
  - name: DATABASE_URL
    required: true (all phases)
    format: "sqlite+aiosqlite:///<path> OR postgresql+asyncpg://user:pass@host:port/db"

  - name: SECRET_KEY
    required: true (Phase 2, Phase 3)
    format: "string (32+ characters)"

  - name: NEXTAUTH_SECRET
    required: true (Phase 2 only)
    required: false (Phase 3 - optional)
    format: "string"

  - name: OPENROUTER_API_KEY
    required: true (Phase 3 only)
    required: false (Phase 2)
    format: "sk-or-v1-<hex>"
```

**Output Contract** (Console Output + Exit Codes):
```yaml
console_output:
  format: "Plain text with ANSI colors"
  sections:
    - banner: "ENVIRONMENT VALIDATION"
    - phase_detection: "Detected Phase: X | Using Phase X profile"
    - progress: "[1/5] Checking environment variables... ✓"
    - summary: "✅ VALIDATION PASSED" OR "❌ VALIDATION FAILED"
    - errors: "Issues found (N): 1. [var] Error: [msg] | Fix: [hint]"

exit_codes:
  0: "All validations passed"
  1: "Script execution error (Python exception, etc.)"
  2: "Validation failures detected (fail-fast)"
  3: "Wrong directory detected" (future: Directory Safety Rule)
```

**Deliverable**: `contracts/validation-profiles.yaml` with complete validation profile specifications

### Quickstart Guide

**Deliverable**: `quickstart.md` with:
- Installation: "No installation required - uses standard library"
- Basic usage: `./scripts/verify-env.py`
- Manual phase override: `./scripts/verify-env.py --phase 2`
- Testing Phase 2: "Switch to branch, run validator, expect PostgreSQL + NextAuth checks"
- Testing Phase 3: "Switch to branch, run validator, expect SQLite + OpenRouter checks"
- Testing generic mode: "Run in clean directory, expect DATABASE_URL-only validation"
- Troubleshooting: "If python-dotenv missing, export vars manually OR pip install python-dotenv"

---

## Phase 2: Implementation Architecture

**Note**: This section provides architectural guidance for `/sp.tasks` and `/sp.implement`. The actual task breakdown and implementation occur in subsequent commands.

### Component Breakdown

#### Component 1: Phase Detection System
**Location**: `scripts/verify-env.py` (lines ~45-75, new function `detect_phase()`)
**Responsibility**: Auto-detect current phase by checking for phase-specific directories
**Interface**:
```python
def detect_phase() -> int | None:
    """
    Detect project phase by checking for phase-specific directories.

    Returns:
        int: Phase number (2, 3, etc.) or None if no phase detected
    """
```

**Implementation Notes**:
- Check directories in descending order (phase-3-chatbot, phase-2-web, phase-1-console)
- Return highest detected phase
- Return None if no phase directories found (triggers generic mode)

#### Component 2: Validation Profile Registry
**Location**: `scripts/verify-env.py` (lines ~80-140, new constant `VALIDATION_PROFILES`)
**Responsibility**: Store phase-specific validation requirements
**Interface**:
```python
VALIDATION_PROFILES: dict[int, dict] = {
    2: {
        'name': 'Phase 2 Web',
        'required': ['DATABASE_URL', 'SECRET_KEY', 'NEXTAUTH_SECRET'],
        'optional': [],
        'database_formats': ['postgresql', 'postgres'],
    },
    3: {
        'name': 'Phase 3 Chatbot',
        'required': ['DATABASE_URL', 'OPENROUTER_API_KEY', 'SECRET_KEY'],
        'optional': ['NEXTAUTH_SECRET', 'GEMINI_API_KEY'],
        'database_formats': ['sqlite', 'postgresql', 'postgres'],
    },
}
```

#### Component 3: Enhanced URL Validator
**Location**: `scripts/verify-env.py` (lines ~145-180, modify existing `check_url_format()`)
**Responsibility**: Accept multiple DATABASE_URL formats based on phase profile
**Interface**:
```python
def check_url_format(url_str: str, allowed_schemes: list[str], var_name: str = "DATABASE_URL") -> tuple[bool, str | None]:
    """
    Validate URL format against allowed schemes.

    Args:
        url_str: URL string to validate
        allowed_schemes: List of allowed URL schemes (e.g., ['sqlite', 'postgresql'])
        var_name: Variable name for error messages

    Returns:
        tuple: (success: bool, error_message: str | None)
    """
```

**Implementation Notes**:
- Parse URL with urllib.parse
- Extract scheme (e.g., "sqlite" from "sqlite+aiosqlite://...")
- Check if base scheme in allowed_schemes list
- Return clear error if scheme not allowed for detected phase

#### Component 4: CLI Argument Parser
**Location**: `scripts/verify-env.py` (lines ~300-320, new in `main()`)
**Responsibility**: Parse `--phase` CLI flag for manual override
**Interface**:
```python
def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Namespace with 'phase' attribute (int | None)
    """
```

**Implementation Notes**:
- Use argparse.ArgumentParser
- Add `--phase` argument with `type=int`, `choices=[2, 3]`, `required=False`
- Return parsed arguments

#### Component 5: Main Validation Orchestrator
**Location**: `scripts/verify-env.py` (lines ~330-450, modify existing `main()`)
**Responsibility**: Coordinate phase detection, profile selection, and validation execution
**Flow**:
```
1. Parse CLI args → get manual_phase_override
2. Detect phase from directories → get auto_detected_phase
3. Select phase: manual_phase_override OR auto_detected_phase OR None (generic)
4. Load validation profile OR use generic profile
5. Display phase detection message
6. Run environment variable validation
7. Run database URL validation with phase-specific formats
8. Collect errors and warnings
9. Display summary
10. Exit with appropriate code (0, 1, or 2)
```

### Modification Strategy

**File**: `scripts/verify-env.py`

**Minimal Changes**:
1. Add `detect_phase()` function after imports (~line 45)
2. Add `VALIDATION_PROFILES` constant after `detect_phase()` (~line 80)
3. Modify `check_url_format()` signature to accept `allowed_schemes` parameter (~line 145)
4. Add `parse_args()` function before `main()` (~line 300)
5. Refactor `main()` to:
   - Call `parse_args()` and `detect_phase()`
   - Select validation profile
   - Update validation loop to use profile's `required` and `optional` lists
   - Pass `allowed_schemes` to `check_url_format()`

**Preservation**:
- Keep all existing helper functions (`check_version`, `check_cli_tools`, `check_database_connectivity`)
- Keep dotenv loading logic (already added in previous fix)
- Keep Windows console encoding fix
- Keep exit code conventions (0, 1, 2)

### Testing Strategy

**Manual Testing** (AC-001 through AC-006):

1. **Test AC-001**: Phase 3 Validation Passes
   ```bash
   cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo
   git checkout 004-phase3-chatbot
   ./scripts/verify-env.py
   # Expected: Exit code 0, "Detected Phase: 3", accepts SQLite DATABASE_URL
   ```

2. **Test AC-002**: Phase 2 Still Works
   ```bash
   git stash
   git checkout <phase-2-branch-name>
   ./scripts/verify-env.py
   # Expected: Exit code 0 or 2 (depending on .env), validates PostgreSQL + NextAuth
   ```

3. **Test AC-003**: Clear Phase Detection
   ```bash
   git checkout 004-phase3-chatbot
   ./scripts/verify-env.py
   # Expected output: "Detected Phase: 3"
   ```

4. **Test AC-004**: Database Format Flexibility
   ```bash
   # Set DATABASE_URL=sqlite+aiosqlite:///./todo_app.db in .env
   ./scripts/verify-env.py
   # Expected: Accept SQLite format (Phase 3)

   # Set DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db
   ./scripts/verify-env.py
   # Expected: Accept PostgreSQL format (Phase 3 also allows this)
   ```

5. **Test AC-005**: Dotenv Loading Works
   ```bash
   # Create .env with DATABASE_URL, OPENROUTER_API_KEY, SECRET_KEY
   ./scripts/verify-env.py
   # Expected: Load from .env, validation passes

   # Rename .env temporarily, unset python-dotenv
   pip uninstall python-dotenv -y
   ./scripts/verify-env.py
   # Expected: Show warning about missing python-dotenv, try os.getenv()
   ```

6. **Test AC-006**: Automation Unblocked
   ```bash
   ./scripts/dev-env-setup.sh
   # Expected: Pass step 1/5 (environment validation), continue to steps 2-5
   ```

**Edge Case Testing**:

1. **Multiple Phases Present** (Edge Case 1)
   ```bash
   # Ensure both phase-2-web/ and phase-3-chatbot/ exist
   ./scripts/verify-env.py
   # Expected: "Detected phases: 2, 3 | Using Phase 3 profile"
   ```

2. **No Phase Directories** (Edge Case 2)
   ```bash
   cd /tmp/clean-project
   cp E:/M.Y/.../verify-env.py .
   export DATABASE_URL=sqlite:///test.db
   ./verify-env.py
   # Expected: "Generic validation mode (no phase detected) - validating DATABASE_URL only"
   ```

3. **python-dotenv Not Installed** (Edge Case 3)
   ```bash
   pip uninstall python-dotenv -y
   ./scripts/verify-env.py
   # Expected: Warning message, continue with os.getenv(), exit 0 if vars present
   ```

4. **CLI Flag Override** (Clarification 5)
   ```bash
   ./scripts/verify-env.py --phase 2
   # Expected: Use Phase 2 profile regardless of detected directories
   ```

---

## Risk Analysis

### High Risk

**Risk**: Phase 2 backward compatibility broken
- **Mitigation**: Test AC-002 thoroughly on actual Phase 2 branch before merge
- **Rollback Plan**: Git revert to previous verify-env.py version

### Medium Risk

**Risk**: Generic mode too permissive (only DATABASE_URL check)
- **Mitigation**: Document clearly in output: "Generic validation mode - other variables not validated"
- **Acceptance**: User chose minimal validation (Clarification Q2, Option A)

### Low Risk

**Risk**: Performance degradation from phase detection logic
- **Mitigation**: Phase detection is O(1) directory checks (~3 checks max), negligible overhead
- **Acceptance**: <1ms additional latency, within performance goal of <1 second total

---

## Dependencies

### Internal Dependencies
- `.env` file (optional, created if missing)
- Phase-specific directories (phase-2-web/, phase-3-chatbot/) for auto-detection
- `scripts/dev-env-setup.sh` (consumer of this validator)

### External Dependencies
- `python-dotenv` (optional, graceful fallback if missing)
- Python 3.13+ standard library (no additional packages required)

### Blocking Dependencies
- None (all dependencies optional or already available)

---

## Success Criteria

**Definition of Done**:
1. ✅ All 6 acceptance criteria (AC-001 through AC-006) pass manual testing
2. ✅ All 4 edge cases handled correctly
3. ✅ Phase 2 backward compatibility verified (test on actual Phase 2 branch)
4. ✅ `./scripts/dev-env-setup.sh` automation unblocked (exit code 0 on step 1/5)
5. ✅ Documentation updated (README.md, quickstart.md)
6. ✅ PHR created documenting implementation
7. ✅ Zero new dependencies added (maintains portability)

**Ready for Merge When**:
- All success criteria met
- qa-overseer agent certification obtained
- Phase 3 recovery workflow can proceed

---

## Next Steps

After this plan is approved:

1. **Run `/sp.tasks`** to generate atomic task breakdown from this plan
2. **Run `/sp.implement`** to execute tasks using backend-builder agent
3. **Manual verification** of all 6 acceptance criteria
4. **Commit changes** with `/sp.git.commit_pr`
5. **Resume Phase 3 recovery** workflow (create missing MCP tools spec, ADRs, etc.)

---

**Plan Status**: ✅ COMPLETE - Ready for `/sp.tasks`
**Estimated Implementation Time**: 2-3 hours (refactoring + testing)
**Blocking**: Phase 3 automation currently blocked, high priority fix
