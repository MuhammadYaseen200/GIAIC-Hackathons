# Governance Amendments Draft

**Date**: 2026-01-27
**Trigger**: Phase 2 auto-execution violation after Phase 1 completion
**Agents**: loop-controller (gap analysis), path-warden (structure validation)

---

## Amendment 1: Phase Execution Gate (CRITICAL)

### Problem Identified

Claude Code auto-executed Phase 2 after Phase 1 completion without explicit user approval, violating user authority.

### Root Cause

No explicit rule prevents automatic phase progression. Existing "Pre-Phase Checklist" describes prerequisites but lacks user approval gate.

### Proposed Solution

Add **Phase Execution Gate Protocol** to both `constitution.md` and `AGENTS.md`.

---

### Amendment 1A: Constitution Update

**File**: `.specify/memory/constitution.md`
**Section**: Principle II. Iterative Evolution (The Brownfield Protocol)
**Insert After**: Line 93 (after Pre-Phase Checklist)

```markdown
**Phase Execution Gate Protocol** (MANDATORY):

Phase transitions require EXPLICIT user approval. No agent may auto-execute the next phase.

**Enforcement Sequence**:
1. **Phase Completion Verification**:
   - qa-overseer certifies all acceptance criteria pass
   - lead-architect confirms constitution compliance
   - loop-controller validates spec artifacts complete
   - imperator validates no blocker bugs remain

2. **User Notification** (STOP and REPORT):
   - Display completion summary with pass/fail status
   - List all acceptance criteria results
   - Report any warnings or technical debt
   - Present checkpoint: "Phase N complete. Options: (A) Proceed to Phase N+1, (B) Pause and review"

3. **User Authority** (WAIT FOR EXPLICIT APPROVAL):
   - Agent MUST WAIT for user response
   - Valid responses: "proceed", "next phase", "continue", "A", "yes"
   - Pause responses: "pause", "review", "wait", "stop", "B", "no"
   - NO ASSUMPTIONS: Silence != approval

4. **Phase Transition Authorization**:
   - User grants explicit permission to proceed
   - imperator validates prerequisites for Phase N+1
   - loop-controller begins Phase N+1 workflow

**Prohibited Actions**:
- Auto-starting next phase without user confirmation
- Assuming user intent to proceed
- Bundling phase completion with next phase kickoff
- Skipping user approval gate "for efficiency"

**Violation Response**:
- If auto-progression detected: HALT immediately
- Display error: "Phase auto-progression violates governance. Awaiting user directive."
- Request user decision: Proceed or rollback?
- Log violation in PHR

**Exit Code**: 5 (unauthorized phase progression)
```

---

### Amendment 1B: AGENTS.md Update

**File**: `AGENTS.md`
**Section**: Agent Behavior Rules
**Insert After**: Line 485 (after "Agents MUST NOT" list)

```markdown
### Phase Execution Gate (MANDATORY)

**Rule**: Phase transitions require EXPLICIT user approval. No agent may auto-execute the next phase.

**Operational Workflow**:

1. **Phase Completion**:
   - Complete all tasks for current phase
   - Mark all tasks as [X] in tasks.md
   - Run acceptance tests
   - Verify exit codes (0 = success)

2. **STOP and Report**:
   - Display: "✅ Phase N Complete"
   - Show completion summary:
     ```
     Phase N: [Phase Name]
     Status: COMPLETE
     Tasks: [X/X completed]
     Acceptance Criteria: [X/X passing]
     Warnings: [list any issues]

     OPTIONS:
     A. Proceed to Phase N+1
     B. Pause and review

     What would you like to do?
     ```

3. **WAIT for User Input**:
   - DO NOT proceed until user responds
   - Valid proceed signals: "proceed", "A", "next", "continue", "yes"
   - Valid pause signals: "pause", "B", "review", "stop", "no"

4. **Execute User Decision**:
   - If proceed: Begin Phase N+1 workflow
   - If pause: End session, preserve state

**Example Violation**:
```
❌ WRONG:
Phase 1 complete → Auto-start Phase 2

✅ CORRECT:
Phase 1 complete → Report to user → Wait for approval → User says "proceed" → Start Phase 2
```

**Enforcement**: loop-controller validates phase transitions include user approval checkpoint.
```

---

## Amendment 2: Specialized Agent Usage Enforcement

### Problem Identified

No mandatory enforcement requiring specialized agents for domain-specific tasks. Backend work could be done by general Claude Code without specialist review.

### Root Cause

Agent roles documented but no enforcement mechanism blocks generic implementations.

### Proposed Solution

Add **Specialized Agent Enforcement** to both `constitution.md` and `AGENTS.md`.

---

### Amendment 2A: Constitution Update

**File**: `.specify/memory/constitution.md`
**Section**: Agent Orchestration
**Insert After**: Line 351 (after "Command Team Workflow")

```markdown
**Specialized Agent Enforcement** (MANDATORY):

Domain-specific tasks MUST involve appropriate specialized agents. Generic implementation without specialist review is prohibited.

**Required Agent Delegation**:

| Task Domain | Required Agent | Validator |
|-------------|----------------|-----------|
| Backend (Python, FastAPI, SQLModel) | backend-builder | loop-controller |
| Frontend (Next.js, React, Tailwind) | ux-frontend-developer | loop-controller |
| Architecture decisions | lead-architect | qa-overseer |
| Specifications | spec-architect | loop-controller |
| Security changes | enterprise-grade-validator | qa-overseer |
| AI/ML systems | modular-ai-architect | lead-architect |
| Infrastructure (Docker, K8s, Dapr) | devops-rag-engineer | qa-overseer |
| File placement | path-warden | loop-controller |
| Quality certification | qa-overseer | User (ultimate) |

**Enforcement Protocol**:
1. loop-controller identifies task domain
2. loop-controller delegates to appropriate Build Team agent
3. Build Team agent executes implementation
4. Validator agent certifies work quality
5. User approves final output

**Prohibited Actions**:
- General-purpose Claude Code implementing backend without backend-builder
- Specifications created without spec-architect
- Security changes without enterprise-grade-validator audit
- File creation without path-warden verification
- Quality claims without qa-overseer certification

**Violation Response**:
- If generic implementation detected: HALT
- Require specialist agent review
- If specialist unavailable: BLOCK and report to user

**Agent Role Boundaries**:
- imperator: Delegates, does NOT code
- loop-controller: Validates, does NOT implement
- qa-overseer: Certifies, does NOT write code
- Build Team: Implements, does NOT self-approve
- path-warden: Validates placement, does NOT create files
```

---

### Amendment 2B: AGENTS.md Update

**File**: `AGENTS.md`
**Section**: Boundaries / Safety
**Insert After**: Line 485 (after "Agents MUST NOT" list, before Directory Safety Rule)

```markdown
### Specialized Agent Usage Enforcement (MANDATORY)

**Rule**: Domain-specific tasks MUST use appropriate specialized agents.

**Implementation Workflow**:

1. **Task Analysis**:
   - Identify task domain (backend, frontend, infra, etc.)
   - Match task to required specialist agent
   - Verify specialist agent available

2. **Delegation**:
   - Use Task tool to launch specialist agent
   - Provide complete context (spec, plan, tasks)
   - Specify expected deliverables

3. **Validation**:
   - Validator agent reviews output
   - Checks compliance with spec
   - Verifies code quality

4. **Certification**:
   - qa-overseer certifies if quality gate
   - User approves final deliverable

**Example Workflows**:

**Backend Implementation**:
```
loop-controller → backend-builder (implement) → qa-overseer (certify) → User (approve)
```

**File Creation**:
```
backend-builder (create file) → path-warden (verify placement) → loop-controller (validate)
```

**Architecture Decision**:
```
User (request) → lead-architect (design) → spec-architect (document) → User (approve)
```

**Enforcement**: If task executed without required specialist, loop-controller BLOCKS and requires review.
```

---

## Amendment 3: Enhanced Directory Safety Rule

### Problem Identified

Existing Directory Safety Rule is comprehensive but needs integration with Phase Execution Gate.

### Proposed Enhancement

**File**: `AGENTS.md`
**Section**: Directory Safety Rule (lines 487-529)
**Enhancement**: Add phase execution validation

**Insert After**: Line 500 (after "Validation Protocol")

```markdown
4. **Phase Execution Integration**:
   - Validate directory BEFORE each phase starts
   - Re-validate directory after phase completion
   - If directory changed mid-phase: HALT, report violation
   - Phase transitions MUST occur in correct directory
```

---

## Testing Protocol

After amendments are added, test with these scenarios:

### Test 1: Phase Auto-Progression Prevention

**Scenario**: Complete Phase 1, attempt to start Phase 2
**Expected**: Agent stops after Phase 1, reports completion, waits for approval
**Actual**: [TO BE TESTED]

### Test 2: Specialized Agent Enforcement

**Scenario**: Attempt backend implementation without backend-builder
**Expected**: loop-controller blocks and requires backend-builder delegation
**Actual**: [TO BE TESTED]

### Test 3: Directory Safety Integration

**Scenario**: Change directory mid-phase
**Expected**: Agent detects change, halts, reports violation
**Actual**: [TO BE TESTED]

### Test 4: User Approval Recognition

**Scenario**: Complete phase, user says "proceed"
**Expected**: Agent starts next phase
**Actual**: [TO BE TESTED]

### Test 5: User Pause Recognition

**Scenario**: Complete phase, user says "review"
**Expected**: Agent pauses, preserves state, ends session
**Actual**: [TO BE TESTED]

---

## Version Impact

**Constitution Version**: 2.0.0 → 2.1.0 (MINOR - new enforcement rules)
**Reason**: Adding operational gates without changing principles

**Sync Impact Report Update Required**: Yes
- Add Phase Execution Gate entry
- Add Specialized Agent Enforcement entry
- Document exit code 5 addition

---

## Approval Checklist

Before applying amendments:

- [ ] User reviews Amendment 1A (constitution Phase Gate)
- [ ] User reviews Amendment 1B (AGENTS.md Phase Gate)
- [ ] User reviews Amendment 2A (constitution Agent Enforcement)
- [ ] User reviews Amendment 2B (AGENTS.md Agent Enforcement)
- [ ] User reviews Amendment 3 (Directory Safety enhancement)
- [ ] User approves version bump (2.0.0 → 2.1.0)
- [ ] User approves exit code 5 addition
- [ ] User grants permission to apply amendments

---

## Application Order

1. Update `.specify/memory/constitution.md` (Amendments 1A, 2A)
2. Update `AGENTS.md` (Amendments 1B, 2B, 3)
3. Update constitution version metadata
4. Update constitution sync impact report
5. Create PHR documenting governance update
6. Create git commit with governance amendments
7. Test all 5 test scenarios
8. Report test results to user

---

**STATUS**: DRAFT - Awaiting user approval
**Next Action**: User reviews and approves/rejects amendments
