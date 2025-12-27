"""Unit tests for the TodoRepository.

Tests CRUD operations and ID generation for in-memory storage.
ADR-003 Compliance: Verifies repository uses dict storage only.
"""

import pytest

from src.models.task import Task
from src.repositories.memory_repo import TodoRepository


class TestRepositoryAdd:
    """Tests for TodoRepository.add() method."""

    def test_add_task_assigns_id(self, repository: TodoRepository) -> None:
        """Adding a task assigns a sequential ID."""
        task = Task(id=0, title="Test Task")
        added = repository.add(task)

        assert added.id == 1

    def test_add_task_stores_task(self, repository: TodoRepository) -> None:
        """Added task is stored and retrievable."""
        task = Task(id=0, title="Test Task")
        added = repository.add(task)

        retrieved = repository.get_by_id(added.id)
        assert retrieved is not None
        assert retrieved.title == "Test Task"

    def test_add_multiple_tasks_increments_id(self, repository: TodoRepository) -> None:
        """Adding multiple tasks generates sequential IDs."""
        task1 = repository.add(Task(id=0, title="Task 1"))
        task2 = repository.add(Task(id=0, title="Task 2"))
        task3 = repository.add(Task(id=0, title="Task 3"))

        assert task1.id == 1
        assert task2.id == 2
        assert task3.id == 3


class TestRepositoryGetAll:
    """Tests for TodoRepository.get_all() method."""

    def test_get_all_empty_repository(self, repository: TodoRepository) -> None:
        """Empty repository returns empty list."""
        result = repository.get_all()
        assert result == []

    def test_get_all_returns_all_tasks(self, repository: TodoRepository) -> None:
        """get_all returns all stored tasks."""
        repository.add(Task(id=0, title="Task 1"))
        repository.add(Task(id=0, title="Task 2"))
        repository.add(Task(id=0, title="Task 3"))

        result = repository.get_all()
        assert len(result) == 3
        titles = [t.title for t in result]
        assert "Task 1" in titles
        assert "Task 2" in titles
        assert "Task 3" in titles


class TestRepositoryGetById:
    """Tests for TodoRepository.get_by_id() method."""

    def test_get_by_id_existing_task(self, repository: TodoRepository) -> None:
        """get_by_id returns the correct task."""
        added = repository.add(Task(id=0, title="Test Task"))
        retrieved = repository.get_by_id(added.id)

        assert retrieved is not None
        assert retrieved.id == added.id
        assert retrieved.title == "Test Task"

    def test_get_by_id_nonexistent_task(self, repository: TodoRepository) -> None:
        """get_by_id returns None for nonexistent ID."""
        result = repository.get_by_id(999)
        assert result is None

    def test_get_by_id_after_add(self, repository: TodoRepository) -> None:
        """get_by_id works correctly after adding tasks."""
        repository.add(Task(id=0, title="Task 1"))
        task2 = repository.add(Task(id=0, title="Task 2"))
        repository.add(Task(id=0, title="Task 3"))

        retrieved = repository.get_by_id(task2.id)
        assert retrieved is not None
        assert retrieved.title == "Task 2"


class TestRepositoryUpdate:
    """Tests for TodoRepository.update() method."""

    def test_update_task_changes_fields(self, repository: TodoRepository) -> None:
        """Update modifies task fields in storage."""
        task = repository.add(Task(id=0, title="Original Title"))

        task.title = "Updated Title"
        task.description = "New Description"
        repository.update(task)

        retrieved = repository.get_by_id(task.id)
        assert retrieved is not None
        assert retrieved.title == "Updated Title"
        assert retrieved.description == "New Description"

    def test_update_returns_task(self, repository: TodoRepository) -> None:
        """Update returns the updated task."""
        task = repository.add(Task(id=0, title="Original"))
        task.completed = True

        result = repository.update(task)
        assert result.completed is True


class TestRepositoryDelete:
    """Tests for TodoRepository.delete() method."""

    def test_delete_existing_task(self, repository: TodoRepository) -> None:
        """Delete removes task from storage."""
        task = repository.add(Task(id=0, title="To Delete"))

        result = repository.delete(task.id)
        assert result is True
        assert repository.get_by_id(task.id) is None

    def test_delete_nonexistent_task(self, repository: TodoRepository) -> None:
        """Delete returns False for nonexistent task."""
        result = repository.delete(999)
        assert result is False

    def test_delete_does_not_affect_other_tasks(self, repository: TodoRepository) -> None:
        """Delete only removes the specified task."""
        task1 = repository.add(Task(id=0, title="Task 1"))
        task2 = repository.add(Task(id=0, title="Task 2"))
        task3 = repository.add(Task(id=0, title="Task 3"))

        repository.delete(task2.id)

        assert repository.get_by_id(task1.id) is not None
        assert repository.get_by_id(task2.id) is None
        assert repository.get_by_id(task3.id) is not None


class TestIdGeneration:
    """Tests for sequential ID generation."""

    def test_ids_start_at_one(self, repository: TodoRepository) -> None:
        """First task gets ID 1."""
        task = repository.add(Task(id=0, title="First"))
        assert task.id == 1

    def test_ids_are_sequential(self, repository: TodoRepository) -> None:
        """IDs are assigned sequentially."""
        tasks = [repository.add(Task(id=0, title=f"Task {i}")) for i in range(5)]
        ids = [t.id for t in tasks]
        assert ids == [1, 2, 3, 4, 5]

    def test_ids_continue_after_delete(self, repository: TodoRepository) -> None:
        """ID counter continues after deletion (no reuse)."""
        task1 = repository.add(Task(id=0, title="Task 1"))
        repository.delete(task1.id)
        task2 = repository.add(Task(id=0, title="Task 2"))

        assert task2.id == 2  # ID 1 not reused
