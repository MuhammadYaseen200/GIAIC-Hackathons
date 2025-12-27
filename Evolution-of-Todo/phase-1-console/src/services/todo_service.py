"""Business logic service for Todo operations.

This module implements the Service layer of the application,
containing all business logic and validation rules.

ADR-001 Compliance: Service layer depends on Repository abstraction.
"""

from src.models.task import Task
from src.repositories.memory_repo import TodoRepository


class TodoService:
    """Service layer for Todo business logic.

    Handles validation, business rules, and coordinates with
    the repository for persistence operations.

    Attributes:
        _repository: The TodoRepository instance for data access.
    """

    MAX_TITLE_LENGTH: int = 200

    def __init__(self, repository: TodoRepository) -> None:
        """Initialize the service with a repository.

        Args:
            repository: The TodoRepository instance for data access.
        """
        self._repository = repository

    def _validate_title(self, title: str) -> str:
        """Validate and normalize a task title.

        Args:
            title: The title to validate.

        Returns:
            The validated and truncated title.

        Raises:
            ValueError: If the title is empty or whitespace only.
        """
        title = title.strip()
        if not title:
            raise ValueError("Title cannot be empty")
        return title[: self.MAX_TITLE_LENGTH]

    def add_task(self, title: str, description: str = "") -> Task:
        """Create and add a new task.

        Args:
            title: The title for the new task.
            description: Optional description for the task.

        Returns:
            The created Task with assigned ID.

        Raises:
            ValueError: If the title is empty.
        """
        validated_title = self._validate_title(title)
        task = Task(id=0, title=validated_title, description=description.strip())
        return self._repository.add(task)

    def list_tasks(self) -> list[Task]:
        """Retrieve all tasks.

        Returns:
            List of all tasks in the repository.
        """
        return self._repository.get_all()

    def get_task(self, task_id: int) -> Task:
        """Retrieve a specific task by ID.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            The requested Task.

        Raises:
            KeyError: If no task exists with the given ID.
        """
        task = self._repository.get_by_id(task_id)
        if task is None:
            raise KeyError(f"Task with ID {task_id} not found")
        return task

    def update_task(
        self, task_id: int, title: str | None = None, description: str | None = None
    ) -> Task:
        """Update an existing task.

        Args:
            task_id: The unique identifier of the task to update.
            title: New title (if provided, must not be empty).
            description: New description (if provided).

        Returns:
            The updated Task.

        Raises:
            KeyError: If no task exists with the given ID.
            ValueError: If a new title is provided but is empty.
        """
        task = self.get_task(task_id)

        if title is not None:
            task.title = self._validate_title(title)

        if description is not None:
            task.description = description.strip()

        return self._repository.update(task)

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID.

        Args:
            task_id: The unique identifier of the task to delete.

        Returns:
            True if deletion was successful.

        Raises:
            KeyError: If no task exists with the given ID.
        """
        # Verify task exists first
        self.get_task(task_id)
        return self._repository.delete(task_id)

    def toggle_complete(self, task_id: int) -> Task:
        """Toggle the completion status of a task.

        Args:
            task_id: The unique identifier of the task.

        Returns:
            The updated Task with toggled completion status.

        Raises:
            KeyError: If no task exists with the given ID.
        """
        task = self.get_task(task_id)
        task.completed = not task.completed
        return self._repository.update(task)
