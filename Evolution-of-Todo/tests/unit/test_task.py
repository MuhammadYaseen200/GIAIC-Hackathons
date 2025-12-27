"""Unit tests for the Task model.

Tests Task dataclass creation, defaults, and field behavior.
"""

from datetime import datetime

import pytest

from src.models.task import Task


class TestTaskCreation:
    """Tests for Task creation and field assignment."""

    def test_task_creation_with_all_fields(self) -> None:
        """Task can be created with all fields specified."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        task = Task(
            id=1,
            title="Test Task",
            description="Test Description",
            completed=True,
            created_at=created,
        )

        assert task.id == 1
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.completed is True
        assert task.created_at == created

    def test_task_creation_with_required_fields_only(self) -> None:
        """Task can be created with only required fields."""
        task = Task(id=1, title="Test Task")

        assert task.id == 1
        assert task.title == "Test Task"

    def test_task_id_is_required(self) -> None:
        """Task creation fails without id."""
        with pytest.raises(TypeError):
            Task(title="Test Task")  # type: ignore

    def test_task_title_is_required(self) -> None:
        """Task creation fails without title."""
        with pytest.raises(TypeError):
            Task(id=1)  # type: ignore


class TestTaskDefaults:
    """Tests for Task default field values."""

    def test_description_defaults_to_empty_string(self) -> None:
        """Description defaults to empty string."""
        task = Task(id=1, title="Test")
        assert task.description == ""

    def test_completed_defaults_to_false(self) -> None:
        """Completed status defaults to False."""
        task = Task(id=1, title="Test")
        assert task.completed is False

    def test_created_at_defaults_to_now(self) -> None:
        """Created_at defaults to current datetime."""
        before = datetime.now()
        task = Task(id=1, title="Test")
        after = datetime.now()

        assert before <= task.created_at <= after


class TestTaskEquality:
    """Tests for Task equality and identity."""

    def test_tasks_with_same_fields_are_equal(self) -> None:
        """Two tasks with identical fields are equal."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        task1 = Task(id=1, title="Test", description="Desc", completed=False, created_at=created)
        task2 = Task(id=1, title="Test", description="Desc", completed=False, created_at=created)

        assert task1 == task2

    def test_tasks_with_different_ids_are_not_equal(self) -> None:
        """Tasks with different IDs are not equal."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        task1 = Task(id=1, title="Test", created_at=created)
        task2 = Task(id=2, title="Test", created_at=created)

        assert task1 != task2

    def test_tasks_with_different_titles_are_not_equal(self) -> None:
        """Tasks with different titles are not equal."""
        created = datetime(2025, 1, 1, 12, 0, 0)
        task1 = Task(id=1, title="Test 1", created_at=created)
        task2 = Task(id=1, title="Test 2", created_at=created)

        assert task1 != task2
