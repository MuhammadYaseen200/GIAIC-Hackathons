---
id: PHR-332
title: Generate Atomic Task Breakdown for verify-env Validation Fix
stage: tasks
date: 2026-01-27T19:00:00Z
surface: Claude Code CLI
model: claude-sonnet-4-5
feature: 002-fix-verify-env-validation
branch: 004-phase3-chatbot
user: M_Y
command: /sp.tasks
labels: [task-generation, atomic-tasks, dependency-ordering, phase-aware-validation]
links:
  spec: specs/002-fix-verify-env-validation/spec.md
  plan: specs/002-fix-verify-env-validation/plan.md
  tasks: specs/002-fix-verify-env-validation/tasks.md
  ticket: null
  adr: history/adr/ADR-013-fail-fast-environment-validation.md
  pr: null
files:
  - path: specs/002-fix-verify-env-validation/tasks.md
    action: created
    lines: 478 lines (complete atomic task breakdown)
tests: []
---

## Prompt

User requested: `/sp.tasks if found bug and error or if work in wrong directory instead of E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo, stop and get the correct directory and then continue Wrong Directory = no work, stop imediately, or get wright directory move everything related to project in correct directory. use Specialized, sub-agents, Skills and MCPs that must be used during this major development...`

**Context**: Planning complete (PHR-331). Now generating atomic task breakdown following SDD workflow: SPEC → PLAN → TASKS → IMPLEMENT.

**Feature Goal**: Refactor `scripts/verify-env.py` to support phase-aware validation with reusability for other projects.

**Requirements from Plan**:
- 5 components: Phase Detection, Validation Profiles, Enhanced URL Validator, CLI Parser, Main Orchestrator
- Minimal changes to existing script (single file modification)
- Zero new dependencies (python-dotenv optional)
- Backward compatibility with Phase 2

**Workflow**: Execute `/sp.tasks` template workflow to generate dependency-ordered task list.

## Response snapshot

### Task Generation Strategy

**Approach**: User story-driven task breakdown (one phase per acceptance criterion)

**Key Decisions**:
1. **Single File Constraint**: All tasks modify `scripts/verify-env.py` → Sequential execution required (no parallel)
2. **Phase Organization**: 9 phases aligned with 6 AC + 1 Generic mode + Setup + Polish
3. **MVP Scope**: Phases 1-4 + 6 (core Phase 3 validation) vs Full (all 9 phases)
4. **Testing Strategy**: Manual bash commands (no automated tests requested in spec)

### Task Breakdown Structure

**Phase 1: Setup (3 tasks)**
- T001: Directory Safety Rule validation
- T002: Backup existing script
- T003: Create feature branch

**Phase 2: Foundational (4 tasks - BLOCKING)**
- T004: Add argparse CLI parser
- T005: Add pathlib import
- T006: Create VALIDATION_PROFILES constant
- T007: Implement detect_phase() function

**Phase 3: User Story 1 - Phase Detection & Messaging (AC-001, AC-003) - 5 tasks**
- T008-T012: Integrate detection, CLI flag handling, profile loading, console output

**Phase 4: User Story 2 - Database Flexibility (AC-004) - 4 tasks**
- T013-T016: Refactor URL validator, extract base scheme, validate against profile

**Phase 5: User Story 3 - Phase 2 Backward Compatibility (AC-002) - 4 tasks**
- T017-T020: Add Phase 2 detection, configure profile, test existing projects

**Phase 6: User Story 4 - Automation Integration (AC-006) - 4 tasks**
- T021-T024: Use profile-specific vars, remove hardcoded list, test dev-env-setup.sh

**Phase 7: User Story 5 - Dotenv Verification (AC-005) - 3 tasks**
- T025-T027: Verify existing dotenv code, test loading, test optional dependency

**Phase 8: User Story 6 - Generic Mode Reusability - 5 tasks**
- T028-T032: Add Generic profile, update detection, fallback logic, test portability

**Phase 9: Polish & Cross-Cutting (8 tasks)**
- T033-T040: Documentation, docstrings, error messages, edge case testing, cleanup

**Total**: 40 atomic tasks, 478 lines of task documentation

### Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS all user stories
    ↓
    ├─→ Phase 3 (AC-001, AC-003) → Phase 4 (AC-004) ─┐
    ├─→ Phase 5 (AC-002) ─────────────────────────────┤
    ├─→ Phase 7 (AC-005) ─────────────────────────────┤
    └─→ Phase 8 (Generic) ────────────────────────────┤
                                                       ↓
                                                  Phase 6 (AC-006) ← Integration test
                                                       ↓
                                                  Phase 9 (Polish)
```

**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 6 → Phase 9

**MVP Path**: Phases 1, 2, 3, 4, 6 (skip 5, 7, 8 for minimal unblocking)

### Key Features of Tasks.md

1. **Acceptance Criteria Mapping**:
   - Table mapping AC-001 through AC-006 to task IDs
   - Test commands for each AC
   - Clear verification steps

2. **Edge Case Mapping**:
   - Table mapping EC-1 through EC-4 to task IDs
   - Test scenarios for each edge case

3. **Independent Test Sections**:
   - Each user story phase includes "Independent Test" bash commands
   - Expected output documented for validation

4. **Directory Safety Rule Integration**:
   - T001 explicitly validates working directory before any work
   - Exit code 3 for wrong directory detection

5. **Sequential Execution Requirements**:
   - Explicit note: Single file modification → No parallel execution
   - Task order ensures dependencies resolved

6. **Checkpoint System**:
   - Checkpoints after each phase for validation
   - "STOP and VALIDATE" reminders

7. **Reusability Focus**:
   - Generic mode (Phase 8) enables portability
   - Zero new dependencies
   - Clear extension points documented

### Implementation Recommendations

**Recommended Approach**: Sequential Story Delivery
1. Complete Phase 1-3 → Test phase detection MVP
2. Add Phase 4 → Test database flexibility
3. Add Phase 5 → Test Phase 2 compatibility
4. Add Phase 6 → Integration test with automation
5. Add Phase 7 → Verify dotenv (already works)
6. Add Phase 8 → Test generic mode portability
7. Complete Phase 9 → Final polish and validation

**Minimal Viable Product**: Phases 1, 2, 3, 4, 6 only
- Unblocks Phase 3 automation immediately
- Phase 2 compatibility can be added later (separate validation)
- Generic mode nice-to-have (not critical for Evolution-of-Todo project)

### Specialized Agents/Skills/MCPs to Use

**Next Command**: `/sp.implement` with `backend-builder` agent

**Agents**:
- `backend-builder` - Python script refactoring (PRIMARY)
- `path-warden` - Validate file placement after modifications (AFTER implementation)
- `qa-overseer` - Certification after all AC pass (FINAL)

**Skills**:
- `env-validator` - Environment validation patterns (already in use)
- `systematic-debugging` - If unexpected issues arise during testing
- `security-scan` - Validate no secrets in code before commit

**MCPs**:
- `filesystem` - File read/write operations
- `postgres` - NOT needed (no database operations in this feature)
- `github` - Create PR after implementation complete

**Tools**:
- `Read` - Read existing verify-env.py
- `Edit` - Apply atomic changes per task
- `Bash` - Run acceptance tests and edge case validation

### Estimated Effort

- **Total Tasks**: 40 tasks
- **LOC Modified**: ~150-200 lines in single file
- **New Functions**: 2 (detect_phase, parse_args)
- **Modified Functions**: 2 (check_url_format, main)
- **Estimated Time**: 4-6 hours for experienced developer

### Success Criteria

✅ All 6 acceptance criteria pass (AC-001 through AC-006)
✅ All 4 edge cases handled correctly
✅ Phase 2 backward compatibility verified
✅ dev-env-setup.sh automation unblocked
✅ Zero new dependencies
✅ Generic mode works for other projects
✅ Exit codes correct (0, 1, 2, 3)
✅ quickstart.md examples validated

## Outcome

- ✅ Impact: Complete atomic task breakdown ready for `/sp.implement`
- 🧪 Tests: 6 AC + 4 edge cases mapped to tasks with test commands
- 📁 Files: 1 file created (tasks.md, 478 lines)
- 🔁 Next prompts: `/sp.implement` with backend-builder agent to execute tasks sequentially
- 🧠 Reflection: Single file modification constraint prevents parallel execution, but clear dependency order enables systematic refactoring. MVP path (Phases 1-4, 6) provides fastest unblocking route while full implementation (all 9 phases) maximizes reusability.

## Evaluation notes (flywheel)

- Failure modes observed: None (task generation phase, no execution yet)
- Graders run and results (PASS/FAIL):
  - Template compliance: PASS (follows tasks-template.md structure)
  - User story organization: PASS (9 phases aligned with 6 AC + setup + generic + polish)
  - Dependency ordering: PASS (critical path identified, MVP path documented)
  - Acceptance criteria mapping: PASS (table with test commands)
  - Edge case mapping: PASS (table with test scenarios)
  - Directory Safety Rule integration: PASS (T001 validates directory)
- Prompt variant (if applicable): Standard `/sp.tasks` workflow with single-file modification constraint
- Next experiment (smallest change to try): During implementation, execute MVP path first (Phases 1-4, 6) to unblock automation, then add remaining phases (5, 7, 8, 9) as enhancements

---

## Template Compliance Check

✅ **Format**: All tasks use `[ID] [P?] [Story] Description` format
✅ **Organization**: Tasks grouped by user story (acceptance criteria)
✅ **Phase Dependencies**: Setup → Foundational → User Stories → Polish
✅ **Checkpoints**: After each phase for independent validation
✅ **Parallel Opportunities**: Documented (limited due to single file)
✅ **Independent Tests**: Bash commands for each user story
✅ **Success Criteria**: Mapped to AC and edge cases
✅ **Implementation Strategy**: MVP vs Full delivery paths documented
