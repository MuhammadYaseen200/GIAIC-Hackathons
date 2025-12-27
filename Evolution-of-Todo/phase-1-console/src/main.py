"""CLI REPL for the Todo application.

This module implements the interactive command-line interface
using only Python standard library (input/print).

ADR-002 Compliance: Uses ONLY input() and print().
NO external CLI libraries (typer, click, cmd, argparse).

ADR-003 Compliance: NO save/load menu options.
Data is volatile and lost on exit.
"""

import sys
from pathlib import Path

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.memory_repo import TodoRepository
from src.services.todo_service import TodoService


# ANSI Color Codes (stdlib compliant - no external dependencies)
class Colors:
    """ANSI escape codes for terminal colors."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Foreground colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Background colors
    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"


def color(text: str, *codes: str) -> str:
    """Apply color codes to text."""
    return f"{''.join(codes)}{text}{Colors.RESET}"


def display_menu() -> None:
    """Display the main menu options."""
    print(f"\n{color('=== Todo App ===', Colors.CYAN, Colors.BOLD)}")
    print(f"  {color('1.', Colors.YELLOW)} Add Task")
    print(f"  {color('2.', Colors.YELLOW)} View All Tasks")
    print(f"  {color('3.', Colors.YELLOW)} Update Task")
    print(f"  {color('4.', Colors.YELLOW)} Delete Task")
    print(f"  {color('5.', Colors.YELLOW)} Mark Complete/Incomplete")
    print(f"  {color('6.', Colors.YELLOW)} Exit")
    print(color("================", Colors.CYAN))


def display_tasks(service: TodoService) -> None:
    """Display all tasks with status indicators.

    Args:
        service: The TodoService instance.
    """
    tasks = service.list_tasks()
    if not tasks:
        print(f"\n{color('No tasks found.', Colors.DIM)}")
        return

    print(f"\n{color('--- Tasks ---', Colors.BLUE, Colors.BOLD)}")
    for task in tasks:
        if task.completed:
            status = color("[x]", Colors.GREEN, Colors.BOLD)
            title = color(task.title, Colors.GREEN)
        else:
            status = color("[ ]", Colors.YELLOW)
            title = color(task.title, Colors.WHITE)

        task_id = color(f"{task.id}.", Colors.CYAN)
        desc = color(f" - {task.description}", Colors.DIM) if task.description else ""
        print(f"  {status} {task_id} {title}{desc}")
    print(color("-------------", Colors.BLUE))


def add_task(service: TodoService) -> None:
    """Handle adding a new task.

    Args:
        service: The TodoService instance.
    """
    print(f"\n{color('--- Add Task ---', Colors.MAGENTA, Colors.BOLD)}")
    title = input(f"{color('Enter title:', Colors.CYAN)} ")
    description = input(f"{color('Enter description (optional):', Colors.CYAN)} ")

    try:
        task = service.add_task(title, description)
        print(f"\n{color('✓', Colors.GREEN, Colors.BOLD)} Task created with ID {color(str(task.id), Colors.CYAN)}: {color(task.title, Colors.WHITE)}")
    except ValueError as e:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} {e}")


def update_task(service: TodoService) -> None:
    """Handle updating an existing task.

    Args:
        service: The TodoService instance.
    """
    print(f"\n{color('--- Update Task ---', Colors.MAGENTA, Colors.BOLD)}")
    try:
        task_id = int(input(f"{color('Enter task ID:', Colors.CYAN)} "))
    except ValueError:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} Invalid ID format")
        return

    new_title = input(f"{color('Enter new title (leave empty to keep current):', Colors.CYAN)} ")
    new_description = input(f"{color('Enter new description (leave empty to keep current):', Colors.CYAN)} ")

    try:
        # Only pass values if user provided input
        title_arg = new_title if new_title else None
        desc_arg = new_description if new_description else None

        task = service.update_task(task_id, title=title_arg, description=desc_arg)
        print(f"\n{color('✓', Colors.GREEN, Colors.BOLD)} Task {color(str(task.id), Colors.CYAN)} updated: {color(task.title, Colors.WHITE)}")
    except KeyError as e:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} {e}")
    except ValueError as e:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} {e}")


def delete_task(service: TodoService) -> None:
    """Handle deleting a task.

    Args:
        service: The TodoService instance.
    """
    print(f"\n{color('--- Delete Task ---', Colors.MAGENTA, Colors.BOLD)}")
    try:
        task_id = int(input(f"{color('Enter task ID:', Colors.CYAN)} "))
    except ValueError:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} Invalid ID format")
        return

    try:
        service.delete_task(task_id)
        print(f"\n{color('✓', Colors.GREEN, Colors.BOLD)} Task {color(str(task_id), Colors.CYAN)} deleted successfully.")
    except KeyError as e:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} {e}")


def toggle_complete(service: TodoService) -> None:
    """Handle toggling task completion status.

    Args:
        service: The TodoService instance.
    """
    print(f"\n{color('--- Toggle Complete ---', Colors.MAGENTA, Colors.BOLD)}")
    try:
        task_id = int(input(f"{color('Enter task ID:', Colors.CYAN)} "))
    except ValueError:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} Invalid ID format")
        return

    try:
        task = service.toggle_complete(task_id)
        if task.completed:
            status = color("completed", Colors.GREEN, Colors.BOLD)
        else:
            status = color("pending", Colors.YELLOW)
        print(f"\n{color('✓', Colors.GREEN, Colors.BOLD)} Task {color(str(task.id), Colors.CYAN)} marked as {status}.")
    except KeyError as e:
        print(f"\n{color('✗ Error:', Colors.RED, Colors.BOLD)} {e}")


def main() -> None:
    """Main REPL loop for the Todo application."""
    repository = TodoRepository()
    service = TodoService(repository)

    print(f"\n{color('Welcome to the Todo App!', Colors.GREEN, Colors.BOLD)}")
    print(f"{color('Note:', Colors.YELLOW)} All data is stored in memory and will be lost on exit.")

    while True:
        display_menu()
        choice = input(f"{color('Enter choice:', Colors.CYAN)} ").strip()

        if choice == "1":
            add_task(service)
        elif choice == "2":
            display_tasks(service)
        elif choice == "3":
            update_task(service)
        elif choice == "4":
            delete_task(service)
        elif choice == "5":
            toggle_complete(service)
        elif choice == "6":
            print(f"\n{color('Goodbye!', Colors.GREEN, Colors.BOLD)}")
            break
        else:
            print(f"\n{color('Invalid choice.', Colors.RED)} Please enter 1-6.")


if __name__ == "__main__":
    main()
