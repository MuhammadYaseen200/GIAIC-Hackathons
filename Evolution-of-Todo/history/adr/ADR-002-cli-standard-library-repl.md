# ADR-002: Python Standard Library REPL for CLI

> **Scope**: CLI implementation approach for Phase I, balancing simplicity with zero external dependencies.

- **Status:** Accepted
- **Date:** 2025-12-27
- **Feature:** 001-core-crud
- **Context:** Phase I needs a command-line interface for the Todo application. The Constitution specifies "No external dependencies beyond Python standard library" for Phase I runtime. After `/sp.clarify`, the spec mandates an **Interactive REPL loop** (not single-command CLI). Multiple CLI frameworks exist, but most are external dependencies.

<!-- Significance checklist (ALL must be true to justify this ADR)
     1) Impact: Long-term consequence for architecture/platform/security? YES - defines UX for Phase I
     2) Alternatives: Multiple viable options considered with tradeoffs? YES - typer vs stdlib vs cmd
     3) Scope: Cross-cutting concern (not an isolated detail)? YES - affects entire user interaction
     If any are false, prefer capturing as a PHR note instead of an ADR. -->

## Decision

Implement CLI using **Python standard library only**:

- **Input Handling**: Built-in `input()` function
- **REPL Loop**: `while True` with menu-driven navigation
- **Menu System**: Numbered options (1-6) for operations
- **Output Formatting**: f-strings and print statements
- **Exit Handling**: Clean break on option 6

**Implementation Pattern**:
```python
def main():
    service = TodoService(TodoRepository())
    while True:
        show_menu()
        choice = input("Enter choice: ")
        if choice == "1": handle_add(service)
        # ... more handlers
        elif choice == "6": break
    print("Goodbye!")
```

## Consequences

### Positive

- **Zero Dependencies**: Aligns perfectly with Constitution Phase I constraints
- **Simplicity**: No framework learning curve, familiar Python patterns
- **Control**: Full control over input/output formatting
- **Portability**: Runs on any Python 3.13+ installation without pip install
- **Testing**: Easy to mock `input()` for integration tests

### Negative

- **No Type Hints in CLI**: `typer` would provide automatic type validation
- **Manual Argument Parsing**: No built-in help generation or argument types
- **Limited Features**: No autocomplete, no color output (without external libs)
- **Verbose**: More boilerplate than declarative CLI frameworks
- **Phase II Throwaway**: Web UI in Phase II makes this CLI obsolete

## Alternatives Considered

### Alternative A: Typer Framework

```python
import typer
app = typer.Typer()

@app.command()
def add(title: str, description: str = ""):
    ...
```

**Why Rejected**: External dependency violates Constitution Phase I constraints. Would need `uv add typer` which contradicts "No external dependencies beyond Python standard library".

### Alternative B: Click Framework

Similar to Typer but lower-level.

**Why Rejected**: Same as Typer - external dependency.

### Alternative C: Python `cmd` Module

```python
import cmd

class TodoShell(cmd.Cmd):
    prompt = '(todo) '

    def do_add(self, arg):
        ...
```

**Why Rejected**: While standard library, it's more complex than needed for menu-driven UI. Better suited for shell-style interfaces (e.g., `add Buy groceries`) rather than numbered menus. More learning curve for simple use case.

### Alternative D: argparse (Single-Command)

```python
parser = argparse.ArgumentParser()
parser.add_argument("command", choices=["add", "list", ...])
```

**Why Rejected**: `/sp.clarify` confirmed Interactive REPL is required, not single-command execution. argparse is designed for `python main.py add --title "X"` pattern, not persistent sessions.

## References

- Feature Spec: [specs/001-core-crud/spec.md](../../specs/001-core-crud/spec.md) - Clarifications section
- Implementation Plan: [specs/001-core-crud/plan.md](../../specs/001-core-crud/plan.md)
- Research: [specs/001-core-crud/research.md](../../specs/001-core-crud/research.md) - CLI Framework Selection
- Related ADRs: [ADR-001](./ADR-001-service-repository-pattern.md) - Service-Repository Pattern
- Constitution: [.specify/memory/constitution.md](../../.specify/memory/constitution.md) - Phase I Technology Stack
