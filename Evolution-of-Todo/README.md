# Evolution of Todo

A hackathon project demonstrating Spec-Driven Development and Cloud-Native AI, evolving from a simple Python console app to a fully-featured Kubernetes-deployed AI chatbot.

## Project Status

**Current Phase**: Phase I - In-Memory Python Console App
**Branch**: `001-core-crud`
**Deadline**: December 7, 2025

## Quick Start

```bash
# Clone the repository
git clone https://github.com/MuhammadYaseen200/Evolution-of-Todo.git
cd Evolution-of-Todo

# Switch to the feature branch
git checkout 001-core-crud

# (Phase I implementation pending /sp.plan and /sp.implement)
```

## Features (Phase I)

- [x] Add Task (title required, description optional)
- [x] View Task List (display ID, title, status)
- [x] Update Task (modify title/description by ID)
- [x] Delete Task (remove by ID)
- [x] Mark as Complete (toggle status)

## Development Methodology

This project strictly follows **Spec-Driven Development**:

1. **Specify** - Define requirements in `specs/<feature>/spec.md`
2. **Plan** - Create architecture in `specs/<feature>/plan.md`
3. **Tasks** - Break into atomic tasks in `specs/<feature>/tasks.md`
4. **Implement** - Generate code via Claude Code

**Key Constraint**: No manual code writing. All code is generated from approved specifications.

## Project Structure

```
hackathon-todo/
├── .specify/           # Spec-Kit Plus templates
├── .spec-kit/          # Phase configuration
├── specs/              # Specifications
│   └── 001-core-crud/  # Phase I specs
├── history/            # PHR and ADR records
├── src/                # Source code (generated)
├── AGENTS.md           # Agent behavior rules
└── CLAUDE.md           # Claude Code instructions
```

## Technology Stack

### Phase I
- Python 3.13+
- UV package manager
- Claude Code + Spec-Kit Plus

### Phase II (Coming)
- Next.js 16+ (Frontend)
- FastAPI (Backend)
- SQLModel + Neon PostgreSQL
- Better Auth (Authentication)

### Phase III (Coming)
- OpenAI ChatKit
- OpenAI Agents SDK
- MCP SDK

### Phases IV-V (Coming)
- Docker + Kubernetes
- Helm Charts
- Kafka + Dapr

## Hackathon Information

**Event**: GIAIC Hackathon II - The Evolution of Todo
**Total Points**: 1,000 (+ 600 bonus)

| Phase | Points | Deadline |
|-------|--------|----------|
| I | 100 | Dec 7, 2025 |
| II | 150 | Dec 14, 2025 |
| III | 200 | Dec 21, 2025 |
| IV | 250 | Jan 4, 2026 |
| V | 300 | Jan 18, 2026 |

## License

MIT

## Author

Muhammad Yaseen
