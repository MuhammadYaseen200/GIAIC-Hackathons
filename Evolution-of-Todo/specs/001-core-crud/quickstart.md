# Quickstart: Phase I Core CRUD Console App

**Feature**: 001-core-crud
**Date**: 2025-12-27

---

## Prerequisites

- Python 3.13+ installed
- `uv` package manager installed
- Git (for version control)

### Verify Installation

```bash
python --version   # Should be 3.13+
uv --version       # Should show uv version
```

---

## Project Setup

### 1. Clone and Navigate

```bash
git clone https://github.com/MuhammadYaseen200/Evolution-of-Todo.git
cd Evolution-of-Todo
git checkout 001-core-crud
```

### 2. Initialize Python Project with UV

```bash
uv init
uv add pytest --dev
```

### 3. Create Project Structure

```bash
mkdir -p src/models src/repositories src/services tests/unit tests/integration
touch src/__init__.py src/models/__init__.py src/repositories/__init__.py src/services/__init__.py
touch tests/__init__.py tests/unit/__init__.py tests/integration/__init__.py
```

---

## Running the Application

```bash
uv run python src/main.py
```

**Expected Output**:
```
=== Todo App ===
1. Add Task
2. View All Tasks
3. Update Task
4. Delete Task
5. Mark Complete/Incomplete
6. Exit
================
Enter choice:
```

---

## Running Tests

```bash
uv run pytest tests/ -v
```

**Expected Output**:
```
tests/unit/test_task.py::test_task_creation PASSED
tests/unit/test_repository.py::test_add_task PASSED
tests/unit/test_service.py::test_add_task_valid PASSED
...
```

---

## Development Workflow

1. **Read the spec**: `specs/001-core-crud/spec.md`
2. **Check the plan**: `specs/001-core-crud/plan.md`
3. **Follow tasks**: `specs/001-core-crud/tasks.md`
4. **Write tests first** (where applicable)
5. **Implement code** per task specifications
6. **Run tests** to verify
7. **Commit** with task reference

---

## File Overview

| File | Purpose |
|------|---------|
| `src/main.py` | Entry point, REPL loop, menu handling |
| `src/models/task.py` | Task dataclass definition |
| `src/repositories/memory_repo.py` | In-memory storage operations |
| `src/services/todo_service.py` | Business logic and validation |
| `tests/unit/*` | Unit tests for each component |
| `tests/integration/*` | Integration tests for flows |

---

## Common Operations

### Add a Task
```
Enter choice: 1
Enter task title: Buy groceries
Enter description (optional): Milk, eggs, bread
Task 1 created: Buy groceries
```

### View All Tasks
```
Enter choice: 2

=== Your Tasks ===
[ ] 1. Buy groceries
[x] 2. Call mom
==================
```

### Mark Complete
```
Enter choice: 5
Enter task ID: 1
Task 1 marked as completed
```

### Delete Task
```
Enter choice: 4
Enter task ID: 1
Task 1 deleted successfully
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run from project root with `uv run python src/main.py` |
| `Python version error` | Ensure Python 3.13+ is installed |
| `uv not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

---

## Next Steps

After implementation is complete:
1. Run all tests: `uv run pytest tests/ -v`
2. Manual verification of acceptance scenarios
3. Record 90-second demo video
4. Submit via hackathon form
