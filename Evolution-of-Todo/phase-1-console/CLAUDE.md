# Phase 1: Console Todo App

## Overview

This is **Phase I** of the Evolution of Todo hackathon project - an in-memory Python console application.

## Quick Start

```bash
cd phase-1-console
uv sync
uv run python src/main.py
```

## Run Tests

```bash
cd phase-1-console
uv run pytest tests/ -v
```

## Architecture

```
phase-1-console/
├── src/
│   ├── models/task.py          # Task dataclass
│   ├── repositories/memory_repo.py  # In-memory storage
│   ├── services/todo_service.py     # Business logic
│   └── main.py                 # CLI REPL
├── tests/
│   ├── unit/                   # Unit tests (50)
│   └── integration/            # Integration tests (19)
└── specs/001-core-crud/        # Feature specifications
```

## Architecture Decision Records

- **ADR-001**: Service-Repository Pattern
- **ADR-002**: Python stdlib CLI (no external libs)
- **ADR-003**: Volatile in-memory persistence

## Completion Status

**SEALED** - 69 tests passing, all 8 tasks complete.
