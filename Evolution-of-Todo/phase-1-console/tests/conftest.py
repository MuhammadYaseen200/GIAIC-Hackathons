"""Pytest configuration and fixtures for Evolution of Todo tests."""

import pytest
from src.models.task import Task
from src.repositories.memory_repo import TodoRepository
from src.services.todo_service import TodoService


@pytest.fixture
def repository() -> TodoRepository:
    """Provide a fresh TodoRepository for each test."""
    return TodoRepository()


@pytest.fixture
def service(repository: TodoRepository) -> TodoService:
    """Provide a TodoService with a fresh repository."""
    return TodoService(repository)


@pytest.fixture
def sample_task() -> Task:
    """Provide a sample task for testing."""
    return Task(id=1, title="Test Task", description="Test Description")
