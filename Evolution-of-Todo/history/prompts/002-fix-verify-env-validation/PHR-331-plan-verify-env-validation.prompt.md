---
id: PHR-331
title: Create Implementation Plan for verify-env Validation Fix
stage: plan
date: 2026-01-27T18:30:00Z
surface: Claude Code CLI
model: claude-sonnet-4-5
feature: 002-fix-verify-env-validation
branch: 004-phase3-chatbot
user: M_Y
command: /sp.plan
labels: [planning, architecture, validation, reusability]
links:
  spec: specs/002-fix-verify-env-validation/spec.md
  ticket: null
  adr: history/adr/ADR-013-fail-fast-environment-validation.md
  pr: null
files:
  - path: specs/002-fix-verify-env-validation/plan.md
    action: created
    lines: 580 lines (complete implementation plan)
  - path: specs/002-fix-verify-env-validation/research.md
    action: created
    lines: 310 lines (Phase 0 research complete)
  - path: specs/002-fix-verify-env-validation/data-model.md
    action: created
    lines: 295 lines (Phase 1 data model)
  - path: specs/002-fix-verify-env-validation/contracts/validation-profiles.yaml
    action: created
    lines: 280 lines (API contracts)
  - path: specs/002-fix-verify-env-validation/quickstart.md
    action: created
    lines: 360 lines (Phase 1 quickstart guide)
tests: []
---

## Prompt

User requested: `/sp.plan --feature 002-fix-verify-env-validation`

**Context**: Specification complete and clarified (PHR-330). Now creating implementation plan following SDD workflow: SPEC → PLAN → TASKS → IMPLEMENT.

**Feature Goal**: Refactor `scripts/verify-env.py` to support phase-aware validation, fixing blocker where Phase 3's SQLite + custom JWT setup fails validation designed for Phase 2's PostgreSQL + NextAuth.

**Requirements from Spec**:
- FR-001: Phase-aware validation (auto-detect via directory structure)
- FR-002: Flexible database URL support (SQLite + PostgreSQL)
- FR-003: Auth stack detection (NextAuth vs custom JWT)
- FR-004: Dotenv loading (graceful fallback)
- FR-005: Optional vs required variables

**Workflow**: Execute `/sp.plan` template workflow through Phases 0-1.

## Response snapshot

### Phase 0: Research & Design Patterns

**Research Topics Resolved** (5/5):

1. **argparse Best Practices**:
   - Decision: `argparse.ArgumentParser` with `type=int`, `choices=[2, 3]`
   - Rationale: Standard library, automatic help, type validation
   - Pattern documented in `research.md`

2. **Phase Detection Patterns**:
   - Decision: `Path.cwd() / 'phase-X-name'` with `.exists()` check
   - Rationale: Zero config, automatic on branch switch, O(1) complexity
   - Pattern documented in `research.md`

3. **URL Validation (SQLite vs PostgreSQL)**:
   - Decision: urllib.parse + scheme validation (extract base scheme before '+')
   - Rationale: Handles both `sqlite+aiosqlite://` and `postgresql+asyncpg://` formats
   - Pattern documented in `research.md`

4. **Graceful Dependency Handling**:
   - Decision: Try/except ImportError for python-dotenv
   - Rationale: Maximizes portability (works without external deps)
   - Pattern documented in `research.md`

5. **Error Message Best Practices**:
   - Decision: Structured format with emoji indicators (✓/✗), progress counters, actionable fixes
   - Rationale: Industry standard (cargo/npm-like), scannable, helpful
   - Pattern documented in `research.md`

**Deliverable**: ✅ `research.md` complete (310 lines)

### Phase 1: Data Model & Contracts

**Data Model Entities** (3):

1. **ValidationProfile**:
   - Attributes: phase_id, phase_name, required_vars, optional_vars, database_formats, description
   - 3 instances: Phase 2, Phase 3, Generic
   - Documented in `data-model.md`

2. **ValidationResult**:
   - Attributes: success, phase_detected, phase_used, errors, warnings, exit_code
   - Represents validation run outcome
   - Documented in `data-model.md`

3. **EnvironmentVariable** (implicit):
   - Metadata: name, value, required, phase_id, format_hint, fix_hint
   - Not stored, just checked on-the-fly
   - Documented in `data-model.md`

**State Machines**:
- Phase Detection: CLI args → directory scan → profile selection
- Validation Execution: Load profile → check vars → validate format → generate result

**Deliverable**: ✅ `data-model.md` complete (295 lines)

**API Contracts**:

**Input Contract**:
- CLI: `--phase` flag (optional, int, choices=[2, 3])
- Environment: Variables loaded from .env or shell
- Phase detection: Auto-detect from directories

**Output Contract**:
- Console: Plain text with ANSI colors, structured sections
- Exit codes: 0 (success), 1 (execution error), 2 (validation failure), 3 (reserved)

**Profiles Defined**:
- Phase 2: DATABASE_URL (PostgreSQL), SECRET_KEY, NEXTAUTH_SECRET
- Phase 3: DATABASE_URL (SQLite/PostgreSQL), OPENROUTER_API_KEY, SECRET_KEY
- Generic: DATABASE_URL only (any format)

**Deliverable**: ✅ `contracts/validation-profiles.yaml` complete (280 lines)

**Quickstart Guide**:
- Basic usage examples (auto-detect, manual override)
- Phase-specific setup (Phase 2, Phase 3, generic mode)
- Troubleshooting (common errors + fixes)
- Testing validation (6 test scenarios)
- Integration with dev-env-setup.sh
- Exit codes reference

**Deliverable**: ✅ `quickstart.md` complete (360 lines)

### Phase 2: Implementation Architecture

**Plan Document Created** (`plan.md`, 580 lines):

**Technical Context**:
- Language: Python 3.13+
- Dependencies: Standard library only (python-dotenv optional)
- Performance: <1 second validation time
- Constraints: Backward compatible, zero-config, portable

**Constitution Check**: ✅ All gates pass (no violations)

**Component Breakdown** (5 components):

1. **Phase Detection System** (~lines 45-75 in verify-env.py)
   - Function: `detect_phase() -> int | None`
   - Responsibility: Auto-detect by scanning directories
   - Returns: Phase number or None (generic)

2. **Validation Profile Registry** (~lines 80-140)
   - Constant: `VALIDATION_PROFILES: dict[int, dict]`
   - Stores phase-specific requirements
   - 3 profiles defined (Phase 2, Phase 3, Generic)

3. **Enhanced URL Validator** (~lines 145-180, modify existing)
   - Function: `check_url_format(url_str, allowed_schemes, var_name)`
   - Accepts multiple DATABASE_URL formats based on phase
   - Validates scheme against allowed list

4. **CLI Argument Parser** (~lines 300-320, new in main())
   - Function: `parse_args() -> argparse.Namespace`
   - Parses `--phase` flag for manual override

5. **Main Validation Orchestrator** (~lines 330-450, modify existing)
   - Coordinates: phase detection → profile selection → validation execution
   - 10-step flow documented in plan

**Modification Strategy**:
- Minimal changes to existing script
- Add 5 new components
- Preserve all existing functionality
- No new dependencies

**Testing Strategy**:
- 6 acceptance criteria (AC-001 through AC-006)
- 4 edge cases
- Manual testing procedures documented
- Integration with dev-env-setup.sh verified

**Risk Analysis**:
- High risk: Phase 2 backward compatibility (mitigation: thorough testing)
- Medium risk: Generic mode too permissive (mitigation: clear documentation)
- Low risk: Performance degradation (mitigation: O(1) phase detection)

**Success Criteria**:
- All 6 acceptance criteria pass
- Phase 2 backward compatibility verified
- dev-env-setup.sh automation unblocked
- Zero new dependencies

### Deliverables Summary

| Artifact | Lines | Status | Content |
|----------|-------|--------|---------|
| plan.md | 580 | ✅ Complete | Full implementation plan with architecture |
| research.md | 310 | ✅ Complete | 5 research topics resolved with patterns |
| data-model.md | 295 | ✅ Complete | 3 entities, state machines, constraints |
| contracts/validation-profiles.yaml | 280 | ✅ Complete | API contracts, profiles, testing specs |
| quickstart.md | 360 | ✅ Complete | Usage guide, troubleshooting, examples |
| **TOTAL** | **1,825** | **✅** | **All Phase 0-1 artifacts complete** |

## Outcome

- ✅ Impact: Complete implementation plan ready for `/sp.tasks` and `/sp.implement`
- 🧪 Tests: 6 acceptance criteria defined, 4 edge cases covered, testing strategy documented
- 📁 Files: 5 specification artifacts created (1,825 total lines)
- 🔁 Next prompts: `/sp.tasks` to generate atomic task breakdown, then `/sp.implement` with backend-builder agent
- 🧠 Reflection: Plan emphasizes minimal changes (refactoring existing script), zero new dependencies, and maximum reusability through generic mode. All constitution gates pass. Architecture prioritizes backward compatibility while enabling phase-aware validation.

## Evaluation notes (flywheel)

- Failure modes observed: PowerShell scripts not available in bash environment (handled with fallback path detection)
- Graders run and results (PASS/FAIL):
  - Constitution Check: PASS (all principles satisfied)
  - Research completeness: PASS (5/5 topics resolved)
  - Data model clarity: PASS (3 entities well-defined with state machines)
  - API contracts: PASS (comprehensive YAML with examples)
  - Testing strategy: PASS (6 AC + 4 edge cases)
- Prompt variant (if applicable): Standard `/sp.plan` workflow with Phase 0-1 execution
- Next experiment (smallest change to try): During implementation, validate that Phase 2 tests pass first before declaring success (AC-002 is critical for backward compatibility)
