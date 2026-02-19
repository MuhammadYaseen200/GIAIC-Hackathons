# H0 Enforcement Loops

## Purpose
This file defines every enforcement loop that governs execution in the H0 project. Loops are the heartbeat of the system — they ensure work stays on track, violations are caught, and the project maintains quality standards. Violation of any loop MUST halt execution immediately.

## Loop 1: Spec-Driven Loop (PRIMARY)

**Authority**: Loop-Controller agent
**Trigger**: Any attempt to write implementation code
**Violation Response**: STOP immediately. No exceptions.

```
┌──────────┐     ┌───────────┐     ┌──────┐     ┌────┐     ┌─────┐
│  SPECIFY  │────►│ IMPLEMENT │────►│ TEST │────►│ QA │────►│ FIX │
│ spec.md   │     │ code      │     │ run  │     │    │     │     │
└──────────┘     └───────────┘     └──────┘     └────┘     └──┬──┘
     ▲                                                         │
     └─────────────────────── REPEAT ──────────────────────────┘
```

### Entry Conditions
- Feature MUST have `specs/<feature>/spec.md` with status: Approved
- Spec MUST have Given-When-Then acceptance scenarios
- Plan MUST exist at `specs/<feature>/plan.md`
- Tasks MUST exist at `specs/<feature>/tasks.md`

### Violation Detection
- Code change without corresponding spec.md → HALT
- Test written without spec acceptance criteria → HALT
- PR opened without QA-Overseer sign-off → REJECT
- Implementation diverges from spec → HALT + reconcile

### Recovery Protocol
1. Stop all current implementation work
2. Identify the missing spec artifact
3. Create spec via /sp.specify
4. Get spec approved
5. Resume implementation from the corrected spec

## Loop 2: Ralph Wiggum Loop (Autonomous Completion)

**Authority**: Backend-Builder, Modular-AI-Architect
**Trigger**: Any task requiring iterative autonomous work
**Safety**: Maximum retry count = 5 (configurable)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ CREATE STATE  │────►│ CLAUDE WORKS │────►│  TRY EXIT    │
│ /Needs_Action │     │ (reason+act) │     │  Check /Done │
└──────────────┘     └──────────────┘     └──────┬───────┘
                           ▲                      │
                           │                 ┌────▼────┐
                           │            NO   │ /Done?  │  YES
                           │◄────────────────│         │─────► EXIT
                           │  Re-inject      └─────────┘
                           │  prompt
```

### State Machine
| State | Location | Meaning |
|-------|----------|---------|
| PENDING | /Needs_Action/ | New work item detected |
| IN_PROGRESS | /Plans/ | Claude is reasoning/acting |
| AWAITING_APPROVAL | /Pending_Approval/ | Sensitive action needs human |
| APPROVED | /Approved/ | Human approved, proceed |
| DONE | /Done/ | Task completed successfully |
| FAILED | /Logs/ | Task failed, logged with RCA |

### Safety Guardrails
- Max iterations: 5 (prevent infinite loops)
- Each iteration MUST produce measurable progress
- No progress after 2 iterations → escalate to human
- All state transitions logged to /Logs/
- Iteration count tracked in YAML frontmatter of task file

## Loop 3: Human-in-the-Loop (Sensitive Actions)

**Authority**: All agents (mandatory check)
**Trigger**: Any action matching sensitive categories
**Violation Response**: Execute without approval → CRITICAL VIOLATION → system lockdown

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────┐
│ DETECT       │────►│ /Pending_Approval/ │────►│ HUMAN        │
│ SENSITIVE    │     │ Create approval    │     │ REVIEWS      │
│ ACTION       │     │ request file       │     │              │
└──────────────┘     └───────────────────┘     └──────┬───────┘
                                                       │
                                                  ┌────▼────┐
                                              NO  │APPROVED?│  YES
                                         ┌────────│         │────────┐
                                         ▼        └─────────┘        ▼
                                    /Rejected/                  /Approved/
                                    Log reason                       │
                                                              ┌──────▼──────┐
                                                              │ MCP EXECUTES│
                                                              │             │
                                                              └──────┬──────┘
                                                                     ▼
                                                                  /Logs/
                                                              Record outcome
```

### Sensitive Action Categories
| Category | Examples | Approval Level |
|----------|----------|---------------|
| **Email** | Send email, reply, forward | Standard |
| **Financial** | Payment, transfer, invoice | Elevated |
| **Social Media** | Post, reply, DM | Standard |
| **Account** | Password change, settings | Elevated |
| **Data Export** | Share data externally | Elevated |
| **System** | Install package, modify config | Standard |

### Approval File Format
```yaml
---
type: approval_request
action: send_email
category: email
priority: standard
agent: backend-builder
created: 2026-02-16T10:00:00Z
details: |
  To: user@example.com
  Subject: Weekly Report
  Body: [summary]
risk_level: low
reversible: false
---
```

### Escalation Rules
- No response in 24 hours → re-notify human
- Urgent items (marked priority: urgent) → notify immediately
- Financial items over threshold → require 2-factor confirmation

## Loop 4: Directory Guard (Path Warden)

**Authority**: Path-Warden agent
**Trigger**: Any file creation, move, or modification
**Violation Response**: STOP immediately. Move file to correct location before resuming.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ FILE         │────►│ VALIDATE     │────►│ CORRECT?     │
│ OPERATION    │     │ PATH         │     │              │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                             ┌────▼────┐
                                         NO  │CORRECT? │  YES
                                    ┌────────│         │────────┐
                                    ▼        └─────────┘        ▼
                               STOP!                        PROCEED
                               Log violation                     │
                               Move to correct                   ▼
                               path                         Continue
                               Resume                       operation
```

### Canonical Directory Map
| Content Type | Correct Location |
|-------------|-----------------|
| Specs | `specs/<feature>/` |
| ADRs | `history/adr/` |
| PHRs | `history/prompts/<category>/` |
| Constitution | `.specify/memory/constitution.md` |
| Agent governance | `ai-control/` |
| Watchers | `watchers/` |
| MCP servers | `mcp-servers/` |
| Orchestrator | `orchestrator/` |
| Tests | `tests/` |
| Vault files | `vault/` |
| Utility scripts | `scripts/` |
| Documentation | `docs/` |
| Templates | `.specify/templates/` |
| Commands | `.claude/commands/` |

### Common Violations
- Writing spec files outside `specs/` directory
- Creating test files in source directories
- Putting governance files in root instead of `ai-control/`
- Writing vault content outside `vault/` directory

## Loop Interaction Matrix

| Loop | Can Trigger | Can Be Triggered By |
|------|------------|-------------------|
| Spec-Driven | Ralph Wiggum, HITL | Any code attempt |
| Ralph Wiggum | HITL, Directory Guard | Spec-Driven (after spec approved) |
| HITL | None (terminal) | Ralph Wiggum, any external action |
| Directory Guard | Spec-Driven (re-spec) | Any file operation |

## Monitoring & Health

- All loops MUST log state transitions to `/Logs/`
- Loop-Controller checks loop compliance every operation
- Dashboard.md MUST show loop health status
- Loop violations are tracked with severity (WARN, HALT, CRITICAL)

---
*Governed by: .specify/memory/constitution.md (Principles I, III, VII, X)*
*Version: 1.0.0 | Date: 2026-02-16*
