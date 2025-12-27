"""Unit tests for the TodoService.

Tests business logic, validation, and error handling.
"""

import pytest

from src.models.task import Task
from src.repositories.memory_repo import TodoRepository
from src.services.todo_service import TodoService


class TestAddTask:
    """Tests for TodoService.add_task() method."""

    def test_add_task_valid_title(self, service: TodoService) -> None:
        """Adding task with valid title succeeds."""
        task = service.add_task("Buy groceries", "Milk, eggs, bread")

        assert task.id == 1
        assert task.title == "Buy groceries"
        assert task.description == "Milk, eggs, bread"
        assert task.completed is False

    def test_add_task_empty_title_raises_error(self, service: TodoService) -> None:
        """Adding task with empty title raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            service.add_task("", "Description")

        assert "empty" in str(excinfo.value).lower()

    def test_add_task_whitespace_title_raises_error(self, service: TodoService) -> None:
        """Adding task with whitespace-only title raises ValueError."""
        with pytest.raises(ValueError) as excinfo:
            service.add_task("   ", "Description")

        assert "empty" in str(excinfo.value).lower()

    def test_add_task_strips_whitespace(self, service: TodoService) -> None:
        """Title and description whitespace is stripped."""
        task = service.add_task("  Test Task  ", "  Description  ")

        assert task.title == "Test Task"
        assert task.description == "Description"

    def test_add_task_truncates_long_title(self, service: TodoService) -> None:
        """Titles longer than 200 chars are truncated."""
        long_title = "A" * 300
        task = service.add_task(long_title)

        assert len(task.title) == 200
        assert task.title == "A" * 200

    def test_add_task_without_description(self, service: TodoService) -> None:
        """Adding task without description uses empty string."""
        task = service.add_task("Test Task")

        assert task.description == ""


class TestListTasks:
    """Tests for TodoService.list_tasks() method."""

    def test_list_tasks_empty(self, service: TodoService) -> None:
        """Empty service returns empty list."""
        result = service.list_tasks()
        assert result == []

    def test_list_tasks_returns_all(self, service: TodoService) -> None:
        """list_tasks returns all added tasks."""
        service.add_task("Task 1")
        service.add_task("Task 2")
        service.add_task("Task 3")

        result = service.list_tasks()
        assert len(result) == 3


class TestGetTask:
    """Tests for TodoService.get_task() method."""

    def test_get_task_existing(self, service: TodoService) -> None:
        """get_task returns existing task."""
        added = service.add_task("Test Task")
        retrieved = service.get_task(added.id)

        assert retrieved.id == added.id
        assert retrieved.title == "Test Task"

    def test_get_task_not_found(self, service: TodoService) -> None:
        """get_task raises KeyError for nonexistent ID."""
        with pytest.raises(KeyError) as excinfo:
            service.get_task(999)

        assert "999" in str(excinfo.value)
        assert "not found" in str(excinfo.value).lower()


class TestUpdateTask:
    """Tests for TodoService.update_task() method."""

    def test_update_task_title(self, service: TodoService) -> None:
        """Updating task title succeeds."""
        task = service.add_task("Original Title")
        updated = service.update_task(task.id, title="New Title")

        assert updated.title == "New Title"

    def test_update_task_description(self, service: TodoService) -> None:
        """Updating task description succeeds."""
        task = service.add_task("Title", "Old Description")
        updated = service.update_task(task.id, description="New Description")

        assert updated.description == "New Description"
        assert updated.title == "Title"  # Unchanged

    def test_update_task_both_fields(self, service: TodoService) -> None:
        """Updating both title and description succeeds."""
        task = service.add_task("Old Title", "Old Description")
        updated = service.update_task(task.id, title="New Title", description="New Description")

        assert updated.title == "New Title"
        assert updated.description == "New Description"

    def test_update_task_empty_title_raises_error(self, service: TodoService) -> None:
        """Updating with empty title raises ValueError."""
        task = service.add_task("Original Title")

        with pytest.raises(ValueError) as excinfo:
            service.update_task(task.id, title="")

        assert "empty" in str(excinfo.value).lower()

    def test_update_task_not_found(self, service: TodoService) -> None:
        """Updating nonexistent task raises KeyError."""
        with pytest.raises(KeyError):
            service.update_task(999, title="New Title")

    def test_update_task_no_changes(self, service: TodoService) -> None:
        """Updating with no parameters returns unchanged task."""
        task = service.add_task("Title", "Description")
        updated = service.update_task(task.id)

        assert updated.title == "Title"
        assert updated.description == "Description"


class TestDeleteTask:
    """Tests for TodoService.delete_task() method."""

    def test_delete_task_existing(self, service: TodoService) -> None:
        """Deleting existing task succeeds."""
        task = service.add_task("To Delete")
        result = service.delete_task(task.id)

        assert result is True
        with pytest.raises(KeyError):
            service.get_task(task.id)

    def test_delete_task_not_found(self, service: TodoService) -> None:
        """Deleting nonexistent task raises KeyError."""
        with pytest.raises(KeyError) as excinfo:
            service.delete_task(999)

        assert "999" in str(excinfo.value)


class TestToggleComplete:
    """Tests for TodoService.toggle_complete() method."""

    def test_toggle_complete_pending_to_completed(self, service: TodoService) -> None:
        """Toggling pending task marks it completed."""
        task = service.add_task("Test Task")
        assert task.completed is False

        toggled = service.toggle_complete(task.id)
        assert toggled.completed is True

    def test_toggle_complete_completed_to_pending(self, service: TodoService) -> None:
        """Toggling completed task marks it pending."""
        task = service.add_task("Test Task")
        service.toggle_complete(task.id)  # Mark complete

        toggled = service.toggle_complete(task.id)  # Toggle back
        assert toggled.completed is False

    def test_toggle_complete_not_found(self, service: TodoService) -> None:
        """Toggling nonexistent task raises KeyError."""
        with pytest.raises(KeyError):
            service.toggle_complete(999)

    def test_toggle_complete_multiple_times(self, service: TodoService) -> None:
        """Toggling multiple times alternates status."""
        task = service.add_task("Test Task")

        toggled1 = service.toggle_complete(task.id)
        assert toggled1.completed is True

        toggled2 = service.toggle_complete(task.id)
        assert toggled2.completed is False

        toggled3 = service.toggle_complete(task.id)
        assert toggled3.completed is True


class TestValidation:
    """Tests for input validation."""

    def test_title_max_length(self, service: TodoService) -> None:
        """Title is truncated at exactly 200 characters."""
        title_200 = "X" * 200
        title_201 = "X" * 201

        task1 = service.add_task(title_200)
        assert len(task1.title) == 200

        task2 = service.add_task(title_201)
        assert len(task2.title) == 200

    def test_empty_string_after_strip_raises_error(self, service: TodoService) -> None:
        """Title that becomes empty after strip raises error."""
        with pytest.raises(ValueError):
            service.add_task("\t\n  \r")
