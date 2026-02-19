# H0 Swarm: Multi-Agent Orchestration Rules

## Purpose
This file governs how multiple Claude Code instances coordinate parallel work on the H0 project. The swarm pattern enables throughput multiplication while preventing conflicts, race conditions, and cross-domain violations.

## Swarm Principles

1. **No Direct Communication**: Agents MUST NOT communicate directly. The Obsidian vault is the sole message bus.
2. **File Lock Ownership**: Only one agent may modify a file at a time. Conflicts are resolved by authority level.
3. **Domain Isolation**: Each agent operates within its registered domain boundaries (see AGENTS.md).
4. **Coordinator Required**: Parallel execution requires Task-Orchestrator or Imperator coordination.
5. **Merge Point**: All parallel work MUST converge at a defined checkpoint before the next phase.

## Parallel Execution Patterns

### Pattern 1: Fan-Out / Fan-In
```
                    COORDINATOR
                    (Task-Orchestrator)
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         Agent A    Agent B    Agent C
         (domain1)  (domain2)  (domain3)
              │          │          │
              └──────────┼──────────┘
                         ▼
                    MERGE POINT
                    (QA-Overseer verifies)
```

**Use when**: Multiple independent user stories or tasks can proceed simultaneously.
**Example**: Backend-Builder on API, UX-Frontend-Developer on UI, DevOps-RAG-Engineer on Docker — all in parallel.

### Pattern 2: Pipeline
```
    Spec-Architect ──► Backend-Builder ──► QA-Overseer
    (spec.md)         (implementation)    (verification)
```

**Use when**: Work is sequential and each stage depends on the previous.
**Example**: Spec first, then implement, then test.

### Pattern 3: Specialist Pair
```
    ┌─────────────────┐     ┌─────────────────┐
    │ Backend-Builder  │◄───►│ UX-Frontend-Dev │
    │ (API endpoint)   │     │ (UI component)  │
    └─────────────────┘     └─────────────────┘
           │                        │
           └────────┬───────────────┘
                    ▼
              Integration Test
              (QA-Overseer)
```

**Use when**: Frontend and backend must be developed together for a feature.

## Conflict Resolution

### File Conflicts
| Scenario | Resolution |
|----------|-----------|
| Two agents want to edit the same file | Higher authority wins. Lower re-reads and adapts. |
| Merge conflict in git | Task-Orchestrator resolves. If unable, escalate to Lead-Architect. |
| Spec change during implementation | HALT implementation. Re-read updated spec. Resume from delta. |
| Two agents produce contradictory outputs | Imperator decides. Losing output archived in /Logs/. |

### Authority Resolution Order
1. Imperator (supreme)
2. Lead-Architect
3. QA-Overseer / Loop-Controller (quality authority)
4. Spec-Architect / Backend-Builder / Modular-AI-Architect (execution authority)
5. All Sonnet-tier agents (equal, resolved by Task-Orchestrator)

## Swarm Configurations by Phase

### Phase 0: Foundation
```
Agents: imperator + lead-architect (sequential)
Pattern: Pipeline
Parallel: NONE (governance must be serial)
```

### Phase 1: Obsidian Vault
```
Agents: backend-builder + spec-architect
Pattern: Pipeline (spec → build)
Parallel: Template creation can parallel folder structure
```

### Phase 2: First Watcher (Bronze)
```
Agents: backend-builder + devops-rag-engineer
Pattern: Specialist Pair
Parallel: Watcher code || Docker setup || test harness
```

### Phase 3: Reasoning Loop
```
Agents: modular-ai-architect + backend-builder
Pattern: Pipeline (design → implement)
Parallel: Loop design || state machine || hook scripts
```

### Phase 4: MCP Integration
```
Agents: backend-builder + mcp-builder skill
Pattern: Fan-Out (one MCP per parallel track)
Parallel: Gmail MCP || Browser MCP || File System MCP
```

### Phase 5-8: Scale patterns as needed
```
Pattern: Fan-Out/Fan-In with QA-Overseer merge points
Max parallel agents: 4 (to prevent context exhaustion)
```

## Communication via Vault

### Message Format
All inter-agent messages are markdown files with YAML frontmatter:

```yaml
---
type: agent_message
from: backend-builder
to: qa-overseer
priority: normal
created: 2026-02-16T10:00:00Z
subject: "API endpoint implementation complete"
status: pending_review
---

## Content
[Description of work completed, files modified, tests run]

## Files Modified
- watchers/gmail_watcher.py
- tests/test_gmail_watcher.py

## Request
Please verify against spec at specs/002-gmail-watcher/spec.md
```

### Message Locations
| Purpose | Write To | Read From |
|---------|----------|-----------|
| New work request | vault/Needs_Action/ | Assigned agent reads |
| Work completion | vault/Done/ | QA-Overseer reads |
| Approval request | vault/Pending_Approval/ | Human reads |
| Status update | vault/Logs/ | Dashboard reads |
| Plan output | vault/Plans/ | Next agent reads |

## Resource Limits

| Resource | Limit | Rationale |
|----------|-------|-----------|
| Max concurrent agents | 4 | Prevent context overflow |
| Max agent context | 200k tokens | Claude Pro limit |
| Max file locks per agent | 5 | Prevent resource hoarding |
| Agent timeout | 30 minutes | Prevent stuck agents |
| Retry limit | 3 per task | Prevent infinite retry |

## Health Monitoring

- Task-Orchestrator checks agent heartbeats every 5 minutes
- Stuck agent (no output for 10 minutes) → restart or reassign
- Failed agent → log failure → reassign to backup agent
- All swarm state tracked in vault/Logs/swarm-status.md

---
*Governed by: .specify/memory/constitution.md (Principles I, VII, X)*
*See also: AGENTS.md (agent boundaries), LOOP.md (enforcement)*
*Version: 1.0.0 | Date: 2026-02-16*
