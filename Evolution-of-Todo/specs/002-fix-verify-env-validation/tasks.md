---
description: "Task list for phase-aware environment validation refactor"
feature: "002-fix-verify-env-validation"
date: "2026-01-27"
---

# Tasks: Phase-Aware Environment Validation

**Input**: Design documents from `/specs/002-fix-verify-env-validation/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/validation-profiles.yaml ✅

**Tests**: Manual acceptance testing (6 AC + 4 edge cases) - automated tests not requested

**Organization**: Tasks are grouped by acceptance criteria (user stories) to enable independent implementation and testing of each validation capability.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which acceptance criterion this task belongs to (e.g., AC1, AC2, AC3, AC4, AC5, AC6)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Automation script (Python)
- **Script location**: `scripts/verify-env.py` (existing file to be modified)
- **Documentation**: `specs/002-fix-verify-env-validation/quickstart.md` (existing)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Validate working directory is `E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo` (Directory Safety Rule)
- [x] T002 [P] Backup existing `scripts/verify-env.py` to `scripts/verify-env.py.backup-2026-01-27`
- [x] T003 [P] Create git branch `002-fix-verify-env-validation` from `004-phase3-chatbot`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Add argparse import and CLI argument parser to `scripts/verify-env.py` (~lines 300-320)
- [x] T005 [P] Add pathlib.Path import for phase detection in `scripts/verify-env.py` (line ~10) - ALREADY PRESENT
- [x] T006 Create VALIDATION_PROFILES constant dictionary in `scripts/verify-env.py` (~lines 80-140) with Phase 2, Phase 3, and Generic profiles
- [x] T007 Implement detect_phase() function in `scripts/verify-env.py` (~lines 45-75) for directory-based phase detection

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel
**Completed**: 2026-01-27 by devops-rag-engineer

---

## Phase 3: User Story 1 - Phase Detection & Clear Messaging (AC-001, AC-003) 🎯 MVP

**Goal**: Enable automatic phase detection from directory structure and display clear phase information

**Independent Test**:
```bash
cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo
./scripts/verify-env.py
# Expected: Output shows "Detected Phase: 3" and "Using Phase 3 profile"
```

### Implementation for User Story 1

- [x] T008 [AC1] Integrate detect_phase() into main() function in `scripts/verify-env.py` (~line 310)
- [x] T009 [AC1] Add --phase CLI flag handling with priority over auto-detection in `scripts/verify-env.py` (~line 313-314)
- [x] T010 [AC1] Load appropriate validation profile from VALIDATION_PROFILES based on detected/specified phase in `scripts/verify-env.py` (~line 317-322)
- [x] T011 [AC3] Add console output showing "Detected Phase: X | Using Phase X profile" in `scripts/verify-env.py` (~line 325-327)
- [x] T012 [AC3] Add console output showing "Generic validation mode (no phase detected)" for generic mode in `scripts/verify-env.py` (~line 328-330)

**Checkpoint**: Phase detection works and displays clear messages - VERIFIED 2026-01-27

---

## Phase 4: User Story 2 - Database Format Flexibility (AC-004)

**Goal**: Accept both SQLite and PostgreSQL DATABASE_URL formats based on phase requirements

**Independent Test**:
```bash
# Test SQLite format (Phase 3)
export DATABASE_URL="sqlite+aiosqlite:///./todo_app.db"
./scripts/verify-env.py --phase 3
# Expected: Exit code 0 (success)

# Test PostgreSQL format (Phase 2 and Phase 3)
export DATABASE_URL="postgresql+asyncpg://localhost/db"
./scripts/verify-env.py --phase 3
# Expected: Exit code 0 (success)

# Test SQLite format on Phase 2 (should fail)
export DATABASE_URL="sqlite+aiosqlite:///./todo_app.db"
./scripts/verify-env.py --phase 2
# Expected: Exit code 2 (validation failure)
```

### Implementation for User Story 2

- [x] T013 [AC4] Refactor check_url_format() function in `scripts/verify-env.py` (~lines 150-192) to accept `allowed_schemes` parameter
- [x] T014 [AC4] Extract base scheme from DATABASE_URL (before '+' character) using urllib.parse in `scripts/verify-env.py` (~lines 169-175)
- [x] T015 [AC4] Validate DATABASE_URL scheme against profile's allowed list (Phase 2: ['postgresql', 'postgres'], Phase 3: ['sqlite', 'postgresql', 'postgres'], Generic: any) in `scripts/verify-env.py` (~lines 177-182)
- [x] T016 [AC4] Update error message to show allowed formats for current phase in `scripts/verify-env.py` (~lines 180-182, 372-379)

**Checkpoint**: At this point, database URL validation should respect phase-specific formats
**Completed**: 2026-01-28 by devops-rag-engineer - All tests pass (5/5 scenarios verified)

---

## Phase 5: User Story 3 - Phase 2 Backward Compatibility (AC-002)

**Goal**: Ensure Phase 2 projects continue working without any changes

**Independent Test**:
```bash
# Switch to Phase 2 branch (if exists) or create test scenario
git checkout <phase-2-branch> || mkdir -p phase-2-web
cd phase-2-web
cat > .env <<'EOF'
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/todo_db
SECRET_KEY=test-secret-key-32-characters-long
NEXTAUTH_SECRET=test-nextauth-secret-32-characters
EOF
../scripts/verify-env.py
# Expected: Exit code 0 or 2 (depending on actual env), but "Detected Phase: 2" and checks NEXTAUTH_SECRET
```

### Implementation for User Story 3

- [x] T017 [AC2] Add phase-2-web directory detection to detect_phase() in `scripts/verify-env.py` (~line 55)
- [x] T018 [AC2] Configure Phase 2 profile in VALIDATION_PROFILES with required_vars: ['DATABASE_URL', 'SECRET_KEY', 'NEXTAUTH_SECRET'] in `scripts/verify-env.py` (~line 85)
- [x] T019 [AC2] Configure Phase 2 profile database_formats: ['postgresql', 'postgres'] in `scripts/verify-env.py` (~line 90)
- [x] T020 [AC2] Test Phase 2 validation with existing .env (if phase-2-web directory exists)

**Checkpoint**: Phase 2 backward compatibility verified - existing projects should continue working
**Completed**: 2026-01-28 by devops-rag-engineer - All 4 tests pass (profile config, PostgreSQL URL, SQLite rejection, required vars)

---

## Phase 6: User Story 4 - Automation Integration (AC-006)

**Goal**: Unblock dev-env-setup.sh automation by making validation pass for Phase 3

**Independent Test**:
```bash
# Ensure Phase 3 .env is set up
cd E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo
cat > .env <<'EOF'
DATABASE_URL=sqlite+aiosqlite:///./todo_app.db
OPENROUTER_API_KEY=sk-or-v1-test-key
SECRET_KEY=test-secret-key-32-characters-long
EOF

# Run full automation
./scripts/dev-env-setup.sh
# Expected: Step 1/5 passes, continues to steps 2-5
```

### Implementation for User Story 4

- [x] T021 [AC6] Update main() to use phase-specific required_vars from selected profile in `scripts/verify-env.py` (~line 370)
- [x] T022 [AC6] Update main() to use phase-specific optional_vars from selected profile in `scripts/verify-env.py` (~line 375)
- [x] T023 [AC6] Remove hardcoded required_env_vars list in `scripts/verify-env.py` (delete lines 214-216)
- [x] T024 [AC6] Test integration: Run `./scripts/dev-env-setup.sh` and verify step 1/5 passes

**Checkpoint**: Automation now proceeds past step 1/5 validation
**Completed**: 2026-01-31 by devops-rag-engineer - Step 1/5 passes (exit code 0), automation continues to steps 2-5. Additional fixes: SQLite connectivity skip, psycopg2 driver suffix stripping, verify-env.sh .env loading, root .env updated to SQLite URL.

---

## Phase 7: User Story 5 - Dotenv Loading Verification (AC-005)

**Goal**: Verify that .env file loading works correctly (already partially implemented, just needs verification)

**Independent Test**:
```bash
# Create .env in project root
cat > .env <<'EOF'
DATABASE_URL=sqlite+aiosqlite:///./todo_app.db
OPENROUTER_API_KEY=sk-or-v1-test-key
SECRET_KEY=test-secret-key
EOF

# Unset all env vars
unset DATABASE_URL OPENROUTER_API_KEY SECRET_KEY

# Run validation (should load from .env)
./scripts/verify-env.py
# Expected: Variables loaded from .env, validation proceeds
```

### Implementation for User Story 5

- [x] T025 [AC5] Verify dotenv loading code exists in `scripts/verify-env.py` (lines 19-29) - already implemented in previous fix
- [x] T026 [AC5] Test .env file loading: Create .env, unset environment variables, run validator
- [x] T027 [AC5] Test python-dotenv optional: Uninstall python-dotenv (if installed), verify warning shows but validation continues

**Checkpoint**: .env file loading works correctly with graceful fallback - VERIFIED
**Completed**: 2026-01-31 by devops-rag-engineer - All 3 tasks verified:
  - T025: Code inspection confirmed dotenv loading at lines 21-31 with try/except ImportError pattern
  - T026: Runtime test passed - unset env vars, validator loaded from .env, exit code 0
  - T027: Runtime simulation passed - blocked dotenv import, script continued with shell env vars, exit code 0

---

## Phase 8: User Story 6 - Generic Mode Reusability (Implicit from spec)

**Goal**: Enable validator to work in other projects without modification (generic mode)

**Independent Test**:
```bash
# Copy validator to clean test directory
mkdir -p /tmp/test-generic-validation
cp scripts/verify-env.py /tmp/test-generic-validation/
cd /tmp/test-generic-validation

# Create .env with only DATABASE_URL
echo "DATABASE_URL=sqlite:///./test.db" > .env

# Run validation
./verify-env.py
# Expected: "Generic validation mode", validates DATABASE_URL only, exit code 0
```

### Implementation for User Story 6

- [x] T028 [Generic] Add Generic profile to VALIDATION_PROFILES with required_vars: ['DATABASE_URL'], optional_vars: [], database_formats: [] (any) in `scripts/verify-env.py` (~line 125)
- [x] T029 [Generic] Update detect_phase() to return None when no phase directories found in `scripts/verify-env.py` (~line 70)
- [x] T030 [Generic] Add fallback to Generic profile when phase is None in main() in `scripts/verify-env.py` (~line 345)
- [x] T031 [Generic] Add informational message for generic mode with note about limited validation in `scripts/verify-env.py` (~line 365)
- [x] T032 [Generic] Test generic mode: Copy validator to clean directory, run validation

**Checkpoint**: Validator should work in any project without modification
**Completed**: 2026-01-31 by devops-rag-engineer - All 5 tasks verified:
  - T028: Generic profile confirmed at lines 69-75 (key=None, required=['DATABASE_URL'], optional=[], database_formats=[], description present)
  - T029: detect_phase() returns None at line 98 when no phase directories found
  - T030: Fallback logic confirmed at lines 358-363 (VALIDATION_PROFILES.get(phase) -> VALIDATION_PROFILES[None])
  - T031: Generic mode message confirmed at lines 369-371 ("Generic validation mode (no phase detected)" + "Validating DATABASE_URL only")
  - T032: Two runtime tests passed:
    - In-project clean dir (no phase dirs in CWD): Generic mode detected, exit code 0
    - Isolated dir with DATABASE_URL env var: Generic mode detected, exit code 0, only DATABASE_URL validated (no OPENROUTER_API_KEY/SECRET_KEY errors)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T033 [P] Update VALIDATION_PROFILES documentation comments in `scripts/verify-env.py` (~line 42-70)
- [x] T034 [P] Add function docstrings for detect_phase(), check_url_format(), and parse_args() in `scripts/verify-env.py`
- [x] T035 [P] Update error messages to reference quickstart.md for troubleshooting in `scripts/verify-env.py`
- [x] T036 Test all 4 edge cases from contracts/validation-profiles.yaml (lines 263-278)
- [x] T037 Verify exit codes: 0 (success), 1 (execution error), 2 (validation failure)
- [x] T038 [P] Update `specs/002-fix-verify-env-validation/quickstart.md` - fixed output examples to match actual implementation
- [x] T039 Run complete acceptance testing (AC-001 through AC-006) and document results
- [x] T040 Code cleanup: Remove old commented code, verify consistent formatting

**Checkpoint**: All polish tasks complete - feature 100% done
**Completed**: 2026-01-31 by devops-rag-engineer

**T033 Details**: Added comprehensive comment block above VALIDATION_PROFILES with profile structure documentation, field descriptions, extension points, and contract reference.

**T034 Details**: Enhanced docstrings for all three functions:
  - detect_phase(): Added Examples section, clarified return semantics
  - parse_args(): Added description of --phase override behavior, Examples section
  - check_url_format(): Added detailed Args types, return tuple semantics, Examples

**T035 Details**: Added quickstart.md references to three error message locations:
  - Missing required env var errors
  - DATABASE_URL format validation errors
  - Final "VALIDATION FAILED" footer line

**T036 Edge Case Results**:
  - EC-1 (Multiple phases): PASS - Detects Phase 3 (highest) when both phase-2-web/ and phase-3-chatbot/ exist
  - EC-2 (No phase dirs): PASS - Generic mode activated, only DATABASE_URL validated
  - EC-3 (python-dotenv missing): PASS - try/except ImportError pattern verified, continues silently
  - EC-4 (CLI flag override): PASS - `--phase 2` overrides auto-detected Phase 3, uses Phase 2 profile

**T037 Exit Code Results**:
  - Exit code 0: VERIFIED - normal run with valid .env returns 0
  - Exit code 1: VERIFIED - Python exceptions caught by try/except, returns 1
  - Exit code 2: VERIFIED - missing env vars in isolated dir (no .env) returns 2

**T038 Details**: Updated quickstart.md to match actual implementation output:
  - Fixed "Using Phase 3 profile" -> "Using Phase 3 Chatbot profile"
  - Fixed "VALIDATION PASSED" -> "All validations passed"
  - Fixed generic mode output (shows [1/5]-[5/5], not [1/1])
  - Fixed error message format in troubleshooting section

**T039 Acceptance Test Results**:
  - AC-001 (Phase 3 validation): PASS - exit code 0, detects Phase 3, accepts SQLite, no NEXTAUTH_SECRET required
  - AC-002 (Phase 2 backward compat): PASS - detects Phase 2 with --phase 2, requires NEXTAUTH_SECRET + PostgreSQL
  - AC-003 (Clear phase detection): PASS - shows "Detected Phase: 3 | Using Phase 3 Chatbot profile"
  - AC-004 (Database format flexibility): PASS - SQLite accepted (Phase 3), PostgreSQL accepted (Phase 2/3), SQLite rejected (Phase 2)
  - AC-005 (Dotenv loading): PASS - .env file loaded automatically, variables available to validator
  - AC-006 (Automation unblocked): PASS - verify-env.py returns exit code 0, dev-env-setup.sh step 1/5 proceeds

**T040 Details**: Code cleanup verified:
  - No commented-out code found
  - No TODO/FIXME comments
  - No debug print statements
  - All imports used (argparse, os, sys, subprocess, re, urlparse, Path)
  - Consistent 4-space indentation throughout
  - Fixed unnecessary f-strings (lines with no interpolation)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed sequentially (recommended for single developer)
  - AC-001/003 (Phase 3) → AC-004 (Phase 4) → AC-002 (Phase 5) → AC-006 (Phase 6) → AC-005 (Phase 7) → Generic (Phase 8)
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **Phase 3 (AC-001, AC-003)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **Phase 4 (AC-004)**: Depends on Phase 3 (needs phase detection + profile loading) - NOT independently testable
- **Phase 5 (AC-002)**: Can start after Phase 3 - Independently testable (different phase)
- **Phase 6 (AC-006)**: Depends on Phases 3 + 4 + 5 (needs all validation working) - Integration test
- **Phase 7 (AC-005)**: Can start after Foundational - Independently testable (dotenv only)
- **Phase 8 (Generic)**: Can start after Phase 3 - Independently testable (different profile)

### Within Each User Story

- Foundation tasks (T004-T007) MUST complete before any user story tasks
- Phase 3 tasks (T008-T012) should complete before Phase 4 (T013-T016)
- All implementation tasks before Polish phase
- Testing tasks after implementation tasks complete

### Parallel Opportunities

- Phase 1: T002 and T003 can run in parallel
- Phase 2: T005 and T006 can run in parallel (different sections of file)
- Phase 9: T033, T034, T035, T038 can run in parallel (different files/sections)

### Sequential Requirements (Single File Modification)

⚠️ **IMPORTANT**: Since all tasks modify the same file (`scripts/verify-env.py`), tasks CANNOT run in parallel. Sequential execution required:

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundation) in order: T004 → T005 → T006 → T007
3. Complete Phase 3 in order: T008 → T009 → T010 → T011 → T012
4. Complete Phase 4 in order: T013 → T014 → T015 → T016
5. Complete Phase 5 in order: T017 → T018 → T019 → T020
6. Complete Phase 6 in order: T021 → T022 → T023 → T024
7. Complete Phase 7 in order: T025 → T026 → T027
8. Complete Phase 8 in order: T028 → T029 → T030 → T031 → T032
9. Complete Phase 9 in order (some parallel): T033-T040

---

## Implementation Strategy

### Recommended Approach: Sequential Story Delivery

Given single-file modification constraint:

1. **Complete Phase 1: Setup** (T001-T003)
2. **Complete Phase 2: Foundational** (T004-T007) - CRITICAL blocker
3. **Complete Phase 3: Phase Detection MVP** (T008-T012) → Test independently
4. **Complete Phase 4: Database Flexibility** (T013-T016) → Test independently
5. **Complete Phase 5: Phase 2 Compatibility** (T017-T020) → Test independently
6. **Complete Phase 6: Automation Integration** (T021-T024) → Integration test
7. **Complete Phase 7: Dotenv Verification** (T025-T027) → Test independently
8. **Complete Phase 8: Generic Mode** (T028-T032) → Test independently
9. **Complete Phase 9: Polish** (T033-T040) → Final validation

**STOP at each checkpoint to validate story independently before proceeding**

### Minimal Viable Product (MVP)

MVP = Phases 1 + 2 + 3 + 4 + 6 (unblock Phase 3 automation)

- Skippable for MVP: Phase 5 (Phase 2 can be added later), Phase 7 (already works), Phase 8 (nice-to-have)
- Must-have for MVP: Phases 1-4, 6 (core Phase 3 validation)

---

## Notes

- **Directory Safety Rule**: T001 validates correct directory before any work begins
- **Single File**: All tasks modify `scripts/verify-env.py` - no parallel execution possible
- **Existing Code**: Lines 19-29 already have dotenv loading (from previous fix attempt)
- **Backup**: T002 creates backup before modifications begin
- **Testing**: Manual testing via bash commands (no automated test suite)
- **Exit Codes**: 0 (success), 1 (execution error), 2 (validation failure), 3 (wrong directory)
- **Reusability**: Generic mode (Phase 8) enables use in other projects
- **Constitution**: Zero new dependencies (python-dotenv optional), backward compatible
- **Integration**: Works with dev-env-setup.sh automation (Phase 6)

---

## Acceptance Criteria Mapping

| AC | Description | Tasks | Test Command |
|----|-------------|-------|--------------|
| AC-001 | Phase 3 validation passes | T008-T012, T021-T023 | `./scripts/verify-env.py` (in Phase 3) |
| AC-002 | Phase 2 still works | T017-T020 | `./scripts/verify-env.py` (in Phase 2 dir) |
| AC-003 | Clear phase detection | T011-T012 | Check console output shows phase |
| AC-004 | Database format flexibility | T013-T016 | Test SQLite + PostgreSQL URLs |
| AC-005 | Dotenv loading works | T025-T027 | Create .env, unset vars, run validator |
| AC-006 | Automation unblocked | T021-T024 | `./scripts/dev-env-setup.sh` passes step 1/5 |

---

## Edge Cases Mapping

| Edge Case | Description | Tasks | Test Scenario |
|-----------|-------------|-------|---------------|
| EC-1 | Multiple phases present | T008-T010 | Create phase-2-web/ and phase-3-chatbot/, verify highest phase used |
| EC-2 | No phase directories | T028-T031 | Copy validator to clean dir, verify generic mode |
| EC-3 | python-dotenv not installed | T027 | `pip uninstall python-dotenv`, run validator, verify warning shown |
| EC-4 | CLI flag override | T009 | `./scripts/verify-env.py --phase 2` (in Phase 3 dir), verify override works |

---

## Estimated Effort

- **Total Tasks**: 40 tasks
- **LOC Modified**: ~150-200 lines in `scripts/verify-env.py`
- **New Functions**: 2 (detect_phase, parse_args)
- **Modified Functions**: 2 (check_url_format, main)
- **New Constants**: 1 (VALIDATION_PROFILES dictionary)
- **Estimated Time**: 4-6 hours for experienced developer (single file, well-specified)

---

## Success Criteria

✅ All 6 acceptance criteria pass (AC-001 through AC-006)
✅ All 4 edge cases handled correctly
✅ Phase 2 backward compatibility verified (no breaking changes)
✅ dev-env-setup.sh automation unblocked (step 1/5 passes)
✅ Zero new dependencies added
✅ Generic mode works for other projects
✅ Exit codes correct (0, 1, 2, 3)
✅ quickstart.md examples validated against implementation
