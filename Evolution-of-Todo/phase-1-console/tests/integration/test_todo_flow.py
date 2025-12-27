"""Integration tests for the Todo application workflow.

Tests end-to-end CRUD operations through Service + Repository.
Includes ADR-003 compliance test for no file persistence.
"""

import glob
import os

import pytest

from src.repositories.memory_repo import TodoRepository
from src.services.todo_service import TodoService


class TestAddAndListFlow:
    """Tests for User Story 1 & 2: Add and view tasks."""

    def test_add_single_task_and_list(self) -> None:
        """User can add a task and see it in the list."""
        repository = TodoRepository()
        service = TodoService(repository)

        # Add a task
        task = service.add_task("Buy groceries", "Milk, eggs, bread")

        # Verify it appears in list
        tasks = service.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].id == task.id
        assert tasks[0].title == "Buy groceries"
        assert tasks[0].description == "Milk, eggs, bread"
        assert tasks[0].completed is False

    def test_add_multiple_tasks_and_list(self) -> None:
        """User can add multiple tasks and see all in the list."""
        repository = TodoRepository()
        service = TodoService(repository)

        # Add multiple tasks
        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2", "With description")
        task3 = service.add_task("Task 3")

        # Verify all appear in list
        tasks = service.list_tasks()
        assert len(tasks) == 3

        ids = [t.id for t in tasks]
        assert task1.id in ids
        assert task2.id in ids
        assert task3.id in ids

    def test_empty_list_message(self) -> None:
        """Empty repository returns empty list."""
        repository = TodoRepository()
        service = TodoService(repository)

        tasks = service.list_tasks()
        assert tasks == []


class TestCompleteToggleFlow:
    """Tests for User Story 3: Mark tasks complete/incomplete."""

    def test_mark_pending_task_complete(self) -> None:
        """User can mark a pending task as completed."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Test Task")
        assert task.completed is False

        toggled = service.toggle_complete(task.id)
        assert toggled.completed is True

        # Verify persistence in repository
        retrieved = service.get_task(task.id)
        assert retrieved.completed is True

    def test_toggle_completed_task_back_to_pending(self) -> None:
        """User can mark a completed task as pending again."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Test Task")
        service.toggle_complete(task.id)  # Mark complete

        toggled = service.toggle_complete(task.id)  # Toggle back
        assert toggled.completed is False

    def test_toggle_nonexistent_task_shows_error(self) -> None:
        """Toggling nonexistent task raises KeyError with message."""
        repository = TodoRepository()
        service = TodoService(repository)

        with pytest.raises(KeyError) as excinfo:
            service.toggle_complete(999)

        assert "999" in str(excinfo.value)
        assert "not found" in str(excinfo.value).lower()


class TestUpdateTaskFlow:
    """Tests for User Story 4: Update task details."""

    def test_update_task_title(self) -> None:
        """User can update a task's title."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Original Title", "Description")
        updated = service.update_task(task.id, title="New Title")

        assert updated.title == "New Title"
        assert updated.description == "Description"  # Unchanged

    def test_update_task_description(self) -> None:
        """User can update a task's description."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Title", "Original Description")
        updated = service.update_task(task.id, description="New Description")

        assert updated.title == "Title"  # Unchanged
        assert updated.description == "New Description"

    def test_update_with_empty_title_shows_error(self) -> None:
        """Updating with empty title raises ValueError."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Original Title")

        with pytest.raises(ValueError) as excinfo:
            service.update_task(task.id, title="")

        assert "empty" in str(excinfo.value).lower()

        # Verify task unchanged
        retrieved = service.get_task(task.id)
        assert retrieved.title == "Original Title"

    def test_update_nonexistent_task_shows_error(self) -> None:
        """Updating nonexistent task raises KeyError."""
        repository = TodoRepository()
        service = TodoService(repository)

        with pytest.raises(KeyError):
            service.update_task(999, title="New Title")


class TestDeleteTaskFlow:
    """Tests for User Story 5: Delete tasks."""

    def test_delete_existing_task(self) -> None:
        """User can delete an existing task."""
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("To Delete")
        task_id = task.id

        result = service.delete_task(task_id)
        assert result is True

        # Verify task is gone
        with pytest.raises(KeyError):
            service.get_task(task_id)

    def test_delete_nonexistent_task_shows_error(self) -> None:
        """Deleting nonexistent task raises KeyError."""
        repository = TodoRepository()
        service = TodoService(repository)

        with pytest.raises(KeyError):
            service.delete_task(999)

    def test_deleted_task_not_in_list(self) -> None:
        """Deleted task does not appear in list."""
        repository = TodoRepository()
        service = TodoService(repository)

        task1 = service.add_task("Task 1")
        task2 = service.add_task("Task 2")
        task3 = service.add_task("Task 3")

        service.delete_task(task2.id)

        tasks = service.list_tasks()
        assert len(tasks) == 2
        ids = [t.id for t in tasks]
        assert task1.id in ids
        assert task2.id not in ids
        assert task3.id in ids


class TestErrorMessages:
    """Tests for FR-009: Clear error messages."""

    def test_empty_title_error_message(self) -> None:
        """Empty title error message is clear."""
        repository = TodoRepository()
        service = TodoService(repository)

        with pytest.raises(ValueError) as excinfo:
            service.add_task("")

        message = str(excinfo.value).lower()
        assert "title" in message or "empty" in message

    def test_task_not_found_error_message(self) -> None:
        """Task not found error includes the ID."""
        repository = TodoRepository()
        service = TodoService(repository)

        with pytest.raises(KeyError) as excinfo:
            service.get_task(42)

        message = str(excinfo.value)
        assert "42" in message


class TestFullCRUDWorkflow:
    """End-to-end workflow tests."""

    def test_complete_crud_cycle(self) -> None:
        """Full create, read, update, toggle, delete cycle."""
        repository = TodoRepository()
        service = TodoService(repository)

        # CREATE
        task = service.add_task("Test Task", "Initial description")
        assert task.id == 1
        assert task.completed is False

        # READ
        retrieved = service.get_task(task.id)
        assert retrieved.title == "Test Task"

        # UPDATE
        updated = service.update_task(task.id, title="Updated Task", description="New desc")
        assert updated.title == "Updated Task"
        assert updated.description == "New desc"

        # TOGGLE
        toggled = service.toggle_complete(task.id)
        assert toggled.completed is True

        # DELETE
        deleted = service.delete_task(task.id)
        assert deleted is True

        # VERIFY DELETED
        tasks = service.list_tasks()
        assert len(tasks) == 0


class TestADR003Compliance:
    """ADR-003: Verify no file I/O persistence occurs."""

    def test_no_file_persistence(self) -> None:
        """ADR-003: Verify no file I/O occurs during operations."""
        # Capture files before
        before_json = set(glob.glob("*.json"))
        before_csv = set(glob.glob("*.csv"))
        before_pkl = set(glob.glob("*.pkl"))
        before_db = set(glob.glob("*.db"))
        before_sqlite = set(glob.glob("*.sqlite"))
        before_sqlite3 = set(glob.glob("*.sqlite3"))

        # Run full CRUD cycle
        repository = TodoRepository()
        service = TodoService(repository)

        task = service.add_task("Test", "Description")
        service.list_tasks()
        service.get_task(task.id)
        service.update_task(task.id, title="Updated")
        service.toggle_complete(task.id)
        service.delete_task(task.id)

        # Verify no new files created
        after_json = set(glob.glob("*.json"))
        after_csv = set(glob.glob("*.csv"))
        after_pkl = set(glob.glob("*.pkl"))
        after_db = set(glob.glob("*.db"))
        after_sqlite = set(glob.glob("*.sqlite"))
        after_sqlite3 = set(glob.glob("*.sqlite3"))

        assert before_json == after_json, "ADR-003 VIOLATION: JSON file created!"
        assert before_csv == after_csv, "ADR-003 VIOLATION: CSV file created!"
        assert before_pkl == after_pkl, "ADR-003 VIOLATION: Pickle file created!"
        assert before_db == after_db, "ADR-003 VIOLATION: DB file created!"
        assert before_sqlite == after_sqlite, "ADR-003 VIOLATION: SQLite file created!"
        assert before_sqlite3 == after_sqlite3, "ADR-003 VIOLATION: SQLite3 file created!"

    def test_data_volatility(self) -> None:
        """ADR-003: Data is volatile and not persisted between instances."""
        # Create first instance with data
        repository1 = TodoRepository()
        service1 = TodoService(repository1)
        service1.add_task("Task 1")
        service1.add_task("Task 2")
        service1.add_task("Task 3")

        assert len(service1.list_tasks()) == 3

        # Create new instance (simulating app restart)
        repository2 = TodoRepository()
        service2 = TodoService(repository2)

        # New instance should have no data
        assert len(service2.list_tasks()) == 0

    def test_no_file_io_imports_in_repository(self) -> None:
        """ADR-003: Repository module should not import file I/O modules."""
        import src.repositories.memory_repo as repo_module

        # Get the module's globals
        repo_imports = set(repo_module.__dict__.keys())

        # Check that no file I/O modules are imported
        forbidden_modules = {"json", "csv", "sqlite3", "pickle", "shelve"}
        for mod in forbidden_modules:
            assert mod not in repo_imports, f"ADR-003 VIOLATION: {mod} imported in repository!"
