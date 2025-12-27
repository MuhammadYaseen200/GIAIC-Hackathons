# Evolution of Todo - Project Overview

## Mission

Master Spec-Driven Development & Cloud-Native AI through iterative evolution from a Python console app to a fully-featured, Kubernetes-deployed AI chatbot.

## Project Goals

1. **Learn Spec-Driven Development** using Claude Code and Spec-Kit Plus
2. **Build Progressively** from console to cloud-native AI
3. **Master Cloud-Native Technologies** including Docker, Kubernetes, Kafka, and Dapr
4. **Create Reusable Intelligence** via agents, skills, and blueprints

## Phase Overview

| Phase | Description | Deadline | Points |
|-------|-------------|----------|--------|
| I | In-Memory Python Console App | Dec 7, 2025 | 100 |
| II | Full-Stack Web Application (Next.js + FastAPI + Neon DB) | Dec 14, 2025 | 150 |
| III | AI-Powered Todo Chatbot (OpenAI Agents SDK + MCP) | Dec 21, 2025 | 200 |
| IV | Local Kubernetes Deployment (Minikube + Helm) | Jan 4, 2026 | 250 |
| V | Advanced Cloud Deployment (Kafka + Dapr + DOKS) | Jan 18, 2026 | 300 |

**Total Points**: 1,000 (+ 600 bonus)

## Current Status

**Active Phase**: Phase I - Core CRUD Console App
**Branch**: `001-core-crud`
**Spec Status**: Complete and validated
**Implementation Status**: SEALED (69 tests passing, all 8 tasks complete)

## Feature Progression

### Basic Level (Phases I-III)
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

## Key Constraint

**No manual code writing.** All code must be generated via Claude Code from approved specifications following the Spec-Driven Development workflow:

> Specify -> Plan -> Tasks -> Implement

## Repository Structure

```
hackathon-todo/
├── .specify/           # Spec-Kit Plus configuration
├── .spec-kit/          # Project phase configuration
├── .claude/            # Claude agent definitions
├── specs/              # Specifications (intelligence layer)
│   ├── 001-core-crud/  # Phase I feature specs
│   └── overview.md     # This file
├── history/            # PHR and ADR records
├── src/                # Source code (generated)
├── AGENTS.md           # Agent behavior rules
├── CLAUDE.md           # Claude Code instructions
└── README.md           # Project documentation
```

## Architecture Decision Records (ADRs)

Significant architectural decisions are documented in `history/adr/`:

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-001](../history/adr/ADR-001-service-repository-pattern.md) | Service-Repository Pattern for In-Memory App | Accepted | 2025-12-27 |
| [ADR-002](../history/adr/ADR-002-cli-standard-library-repl.md) | Python Standard Library REPL for CLI | Accepted | 2025-12-27 |
| [ADR-003](../history/adr/ADR-003-volatile-in-memory-persistence.md) | Volatile In-Memory Persistence (No File I/O) | Accepted | 2025-12-27 |

## Next Steps

1. ~~Run `/sp.plan` to create architectural plan~~ (Complete)
2. ~~Run `/sp.tasks` to break into implementation tasks~~ (Complete)
3. ~~Run `/sp.adr` to document architectural decisions~~ (Complete)
4. ~~Run `/sp.implement` to generate code~~ (Complete - 69 tests passing)
5. ~~Manual verification (T-008)~~ (Complete)
6. ~~Commit and seal Phase I~~ (Complete)

**Phase I SEALED** - Ready for Phase II: Full-Stack Web Application
