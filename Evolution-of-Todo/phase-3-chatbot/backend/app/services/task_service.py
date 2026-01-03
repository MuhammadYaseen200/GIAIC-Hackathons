"""Task service for CRUD operations on todo items.

Provides business logic for:
- Creating, reading, updating, and deleting tasks
- Task completion toggle
- Multi-tenancy enforcement (user isolation)

Ported from Phase 1 with database persistence and multi-tenancy support.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.task import Task


def utc_now() -> datetime:
    """Return current UTC time as timezone-naive datetime for PostgreSQL compatibility."""
    return datetime.utcnow()


class TaskService:
    """Service for task CRUD operations with multi-tenancy.

    All operations are scoped to a specific user_id to enforce
    data isolation between users.

    Attributes:
        session: Async database session for queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize TaskService with database session.

        Args:
            session: Async database session.
        """
        self.session = session

    async def create_task(
        self,
        user_id: UUID,
        title: str,
        description: str = "",
    ) -> Task:
        """Create a new task for a user.

        Args:
            user_id: UUID of the task owner.
            title: Task title (1-200 characters).
            description: Optional task description (max 1000 chars).

        Returns:
            Task: Newly created task instance.
        """
        task = Task(
            user_id=user_id,
            title=title.strip(),
            description=description.strip() if description else "",
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def list_tasks(self, user_id: UUID) -> list[Task]:
        """List all tasks for a user.

        Args:
            user_id: UUID of the task owner.

        Returns:
            list[Task]: List of tasks belonging to the user.
        """
        statement = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_task(self, user_id: UUID, task_id: UUID) -> Task | None:
        """Get a specific task by ID for a user.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to retrieve.

        Returns:
            Task | None: Task instance if found and owned by user, None otherwise.
        """
        statement = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update_task(
        self,
        user_id: UUID,
        task_id: UUID,
        title: str | None = None,
        description: str | None = None,
    ) -> Task | None:
        """Update a task's title and/or description.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            title: New title (optional).
            description: New description (optional).

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        if title is not None:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip()
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def delete_task(self, user_id: UUID, task_id: UUID) -> bool:
        """Delete a task.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to delete.

        Returns:
            bool: True if task was deleted, False if not found.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return False

        await self.session.delete(task)
        await self.session.flush()
        return True

    async def toggle_complete(self, user_id: UUID, task_id: UUID) -> Task | None:
        """Toggle a task's completion status.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to toggle.

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        task.completed = not task.completed
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task
