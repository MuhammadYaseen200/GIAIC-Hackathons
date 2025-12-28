# Evolution of Todo Constitution

## Project Overview

**Mission**: Master Spec-Driven Development & Cloud-Native AI through iterative evolution from a Python console app to a fully-featured, Kubernetes-deployed AI chatbot.

**Constraint**: No manual code writing. All code must be generated via Claude Code from approved specifications.

---

## Core Principles

### I. Spec-Driven Development (NON-NEGOTIABLE)

Every line of code must trace back to an approved specification. The workflow is immutable:

1. **Specify** → Define WHAT (requirements, journeys, acceptance criteria)
2. **Plan** → Define HOW (architecture, components, interfaces)
3. **Tasks** → Break into ATOMIC, testable work units
4. **Implement** → Generate code ONLY for approved tasks

**Violation Response**: If code is proposed without a referenced Task ID, HALT and request specification.

### II. Iterative Evolution (The Brownfield Protocol)

Each phase builds on the previous. We evolve, not rewrite.

- **Phase I → II**: In-memory logic moves to `backend/app/services/`
- **Phase II → III**: REST API becomes MCP Tool provider
- **Phase III → IV**: App containerized, Helm charts created
- **Phase IV → V**: Monolith decoupled via Kafka/Dapr events

**Pre-Phase Checklist**:
- [ ] Backup `CLAUDE.md` and current specs
- [ ] Verify previous phase acceptance criteria pass
- [ ] Create migration spec before touching code

### III. Test-First Mindset

While not enforcing strict TDD, every feature must have:

1. **Acceptance Criteria** defined in spec BEFORE implementation
2. **Verification Steps** documented for manual testing
3. **Automated Tests** where tooling permits (pytest, Jest)

### IV. Smallest Viable Diff

- Implement ONLY what the task specifies
- No "while I'm here" refactoring
- No premature optimization
- No feature creep within phases

### V. Intelligence Capture (PHR & ADR)

Every significant interaction is recorded:

- **PHR (Prompt History Record)**: Created after EVERY implementation session
- **ADR (Architectural Decision Record)**: Created for decisions with long-term impact (framework choices, data models, API contracts)

---

## Technology Stack (Immutable)

### Phase I: Console App
| Layer | Technology |
|-------|------------|
| Runtime | Python 3.13+ |
| Package Manager | UV |
| AI Tooling | Claude Code, Spec-Kit Plus |

### Phase II: Full-Stack Web
| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16+ (App Router) |
| Backend | Python FastAPI |
| ORM | SQLModel |
| Database | Neon Serverless PostgreSQL |
| Authentication | Better Auth (JWT) |

### Phase III: AI Chatbot
| Layer | Technology |
|-------|------------|
| Chat UI | OpenAI ChatKit |
| AI Framework | OpenAI Agents SDK |
| MCP Server | Official MCP SDK (Python) |
| State | Stateless API + DB persistence |

### Phase IV: Local Kubernetes
| Layer | Technology |
|-------|------------|
| Containers | Docker (Docker Desktop) |
| Orchestration | Kubernetes (Minikube) |
| Package Manager | Helm Charts |
| AIOps | kubectl-ai, Kagent, Gordon (Docker AI) |

### Phase V: Cloud Deployment
| Layer | Technology |
|-------|------------|
| Cloud Platform | DigitalOcean DOKS / Azure AKS / GCP GKE |
| Event Streaming | Kafka (Redpanda/Strimzi) |
| Distributed Runtime | Dapr |
| CI/CD | GitHub Actions |

---

## Feature Progression (Scope Boundaries)

### Basic Level (Phases I-III Core)
- [x] Add Task
- [x] Delete Task
- [x] Update Task
- [x] View Task List
- [x] Mark as Complete

### Intermediate Level (Phase V)
- [ ] Priorities (high/medium/low)
- [ ] Tags/Categories
- [ ] Search & Filter
- [ ] Sort Tasks

### Advanced Level (Phase V)
- [ ] Recurring Tasks
- [ ] Due Dates & Time Reminders

### Bonus Features
- [ ] Multi-language Support (Urdu)
- [ ] Voice Commands
- [ ] Reusable Intelligence (Subagents/Skills)
- [ ] Cloud-Native Blueprints

---

## API Design Principles

### REST Endpoints (Phase II+)
```
GET    /api/{user_id}/tasks           → List all tasks
POST   /api/{user_id}/tasks           → Create task
GET    /api/{user_id}/tasks/{id}      → Get task details
PUT    /api/{user_id}/tasks/{id}      → Update task
DELETE /api/{user_id}/tasks/{id}      → Delete task
PATCH  /api/{user_id}/tasks/{id}/complete → Toggle completion
```

### MCP Tools (Phase III+)
```
add_task(user_id, title, description?) → {task_id, status, title}
list_tasks(user_id, status?) → [{id, title, completed, ...}]
complete_task(user_id, task_id) → {task_id, status, title}
delete_task(user_id, task_id) → {task_id, status, title}
update_task(user_id, task_id, title?, description?) → {task_id, status, title}
```

### Chat Endpoint (Phase III+)
```
POST /api/{user_id}/chat
  Body: { conversation_id?, message }
  Response: { conversation_id, response, tool_calls[] }
```

---

## Security Principles

1. **No Hardcoded Secrets**: All credentials via `.env` files
2. **JWT Verification**: Backend validates Better Auth tokens
3. **User Isolation**: All queries scoped to authenticated `user_id`
4. **HTTPS Only**: Production endpoints must use TLS

---

## Monorepo Structure

```
hackathon-todo/
├── .specify/                    # Spec-Kit configuration
│   ├── memory/
│   │   └── constitution.md     # THIS FILE
│   └── templates/              # PHR, ADR, Spec templates
├── specs/                       # Specifications
│   ├── overview.md
│   ├── architecture.md
│   ├── features/               # Feature specs
│   ├── api/                    # API specs
│   └── database/               # Schema specs
├── history/                     # Records
│   ├── prompts/                # PHR files
│   │   ├── constitution/
│   │   ├── general/
│   │   └── <feature-name>/
│   └── adr/                    # ADR files
├── frontend/                    # Next.js app (Phase II+)
│   └── CLAUDE.md
├── backend/                     # FastAPI app (Phase II+)
│   └── CLAUDE.md
├── src/                         # Python console app (Phase I)
├── k8s/                         # Kubernetes manifests (Phase IV+)
├── docker-compose.yml
├── CLAUDE.md                    # Root instructions
└── README.md
```

---

## Quality Gates

### Per-Phase Acceptance
| Phase | Gate |
|-------|------|
| I | All 5 basic features work in console |
| II | REST API returns correct data; Auth works |
| III | Chatbot executes MCP tools; State persists |
| IV | Helm charts deploy successfully on Minikube |
| V | Full system runs on DOKS with Kafka/Dapr |

### Per-Feature Acceptance
- [ ] Spec exists in `specs/features/`
- [ ] Plan exists with architectural decisions
- [ ] Tasks exist with atomic steps
- [ ] Implementation matches spec exactly
- [ ] Manual verification steps pass

---

## Agent Orchestration

| Agent | Role | Model |
|-------|------|-------|
| lead-architect | Strategy, constitution, phase transitions | Opus |
| spec-architect | Writing/refining specifications | Opus |
| backend-builder | Python, FastAPI, MCP implementation | Opus |
| ux-frontend-developer | Next.js, Tailwind, Better Auth | Sonnet |
| devops-rag-engineer | Docker, K8s, Helm, Kafka, Dapr | Sonnet |
| qa-overseer | Acceptance criteria validation | Opus |

---

## Governance

1. **Constitution Supremacy**: This document supersedes all other practices
2. **Amendments**: Require documented rationale, PHR creation, and explicit approval
3. **Spec Hierarchy**: Constitution > Specify > Plan > Tasks
4. **Backtracking**: Moving to a previous phase requires a new spec iteration

---

## Deadlines

| Phase | Due Date |
|-------|----------|
| Phase I | Dec 7, 2025 |
| Phase II | Dec 14, 2025 |
| Phase III | Dec 21, 2025 |
| Phase IV | Jan 4, 2026 |
| Phase V | Jan 18, 2026 |

---

**Version**: 1.0.0 | **Ratified**: 2025-12-27 | **Last Amended**: 2025-12-27