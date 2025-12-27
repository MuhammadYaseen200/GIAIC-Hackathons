"""In-memory repository for Task persistence.

This module implements the Repository pattern for Task storage using
an in-memory dictionary.

ADR-003 Compliance: Uses ONLY dict[int, Task] storage.
NO file I/O methods (save, load, export, import).
"""

from src.models.task import Task


class TodoRepository:
    """In-memory repository for Task CRUD operations.

    Uses a dictionary for O(1) lookup by ID and maintains
    a sequential ID counter for new tasks.

    Attributes:
        _tasks: Internal dictionary storage mapping ID to Task.
        _next_id: Counter for generating sequential task IDs.
    """

    def __init__(self) -> None:
        """Initialize an empty repository with ID counter starting at 1."""
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def add(self, task: Task) -> Task:
        """Add a new task to the repository.

        Assigns a unique sequential ID to the task before storing.

        Args:
            task: The Task to add (id field will be overwritten).

        Returns:
            The task with its assigned ID.
        """
        task.id = self._next_id
        self._tasks[task.id] = task
        self._next_id += 1
        return task

    def get_all(self) -> list[Task]:
        """Retrieve all tasks from the repository.

        Returns:
            List of all stored tasks, in insertion order.
        """
        return list(self._tasks.values())

    def get_by_id(self, task_id: int) -> Task | None:
        """Retrieve a task by its ID.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            The Task if found, None otherwise.
        """
        return self._tasks.get(task_id)

    def update(self, task: Task) -> Task:
        """Update an existing task in the repository.

        Args:
            task: The Task with updated fields (must have valid id).

        Returns:
            The updated task.

        Note:
            Caller should verify task exists before calling update.
        """
        self._tasks[task.id] = task
        return task

    def delete(self, task_id: int) -> bool:
        """Delete a task from the repository.

        Args:
            task_id: The unique identifier of the task to delete.

        Returns:
            True if the task was deleted, False if not found.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
