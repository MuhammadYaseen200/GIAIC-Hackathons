"""Task service for CRUD operations on todo items.

Provides business logic for:
- Creating, reading, updating, and deleting tasks
- Task completion toggle
- Priority and tags management (Phase 3 extensions)
- Task search and filtering (Phase 3 extensions)
- Multi-tenancy enforcement (user isolation)

Ported from Phase 1 with database persistence and multi-tenancy support.
Extended in Phase 3 with priority, tags, and search capabilities per ADR-011.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.task import Priority, Task

# Constants for tag validation per ADR-011
MAX_TAGS = 10
MAX_TAG_LENGTH = 50


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


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
        priority: Priority | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        """Create a new task for a user.

        Args:
            user_id: UUID of the task owner.
            title: Task title (1-200 characters).
            description: Optional task description (max 1000 chars).
            priority: Optional task priority (defaults to MEDIUM).
            tags: Optional list of tags (max 10 tags, each max 50 chars).

        Returns:
            Task: Newly created task instance.
        """
        # Normalize and validate tags if provided
        normalized_tags: list[str] = []
        if tags:
            normalized_tags = self._normalize_tags(tags)

        task = Task(
            user_id=user_id,
            title=title.strip(),
            description=description.strip() if description else "",
            priority=priority if priority is not None else Priority.medium,
            tags=normalized_tags,
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
        priority: Priority | None = None,
        tags: list[str] | None = None,
    ) -> Task | None:
        """Update a task's fields.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            title: New title (optional).
            description: New description (optional).
            priority: New priority level (optional).
            tags: New tags list (optional, replaces existing).

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
        if priority is not None:
            task.priority = priority
        if tags is not None:
            task.tags = self._normalize_tags(tags)
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

    # Phase 3: Priority and Tags Methods (per ADR-011)

    async def update_priority(
        self,
        user_id: UUID,
        task_id: UUID,
        priority: Priority,
    ) -> Task | None:
        """Update a task's priority.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            priority: New priority level (high/medium/low).

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        task.priority = priority
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def add_tags(
        self,
        user_id: UUID,
        task_id: UUID,
        tags: list[str],
    ) -> Task | None:
        """Add tags to a task.

        Merges new tags with existing tags, respecting limits.
        Duplicate tags (case-insensitive) are removed.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            tags: List of tags to add.

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        # Normalize new tags
        normalized_new_tags = self._normalize_tags(tags)

        # Merge with existing tags (case-insensitive deduplication)
        existing_lower = {tag.lower() for tag in task.tags}
        merged_tags = list(task.tags)

        for tag in normalized_new_tags:
            if tag.lower() not in existing_lower:
                merged_tags.append(tag)
                existing_lower.add(tag.lower())

        # Limit to MAX_TAGS
        task.tags = merged_tags[:MAX_TAGS]
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def remove_tags(
        self,
        user_id: UUID,
        task_id: UUID,
        tags: list[str],
    ) -> Task | None:
        """Remove tags from a task.

        Removes tags that match (case-insensitive) the provided list.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            tags: List of tags to remove.

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        # Normalize tags to remove
        tags_to_remove_lower = {tag.lower() for tag in tags if tag.strip()}

        # Filter out matching tags (case-insensitive)
        task.tags = [
            tag for tag in task.tags
            if tag.lower() not in tags_to_remove_lower
        ]
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update_tags(
        self,
        user_id: UUID,
        task_id: UUID,
        tags: list[str],
    ) -> Task | None:
        """Replace all tags on a task.

        Args:
            user_id: UUID of the task owner.
            task_id: UUID of the task to update.
            tags: New list of tags to set.

        Returns:
            Task | None: Updated task if found, None otherwise.
        """
        task = await self.get_task(user_id, task_id)
        if not task:
            return None

        task.tags = self._normalize_tags(tags)
        task.updated_at = utc_now()

        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def search_tasks(
        self,
        user_id: UUID,
        keyword: str | None = None,
        status: bool | None = None,
        priority: Priority | None = None,
        tag: str | None = None,
        sort_by: Literal["created_at", "updated_at", "priority", "title"] = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> list[Task]:
        """Search and filter tasks with multiple criteria.

        Args:
            user_id: UUID of the task owner (always enforced).
            keyword: Optional keyword to search in title and description.
            status: Optional completion status (True=completed, False=incomplete).
            priority: Optional priority filter (high/medium/low).
            tag: Optional tag filter (tasks must have this tag, case-insensitive).
            sort_by: Field to sort by (created_at, updated_at, priority, title).
            sort_order: Sort order (asc or desc).

        Returns:
            list[Task]: Filtered and sorted list of tasks.
        """
        statement = select(Task).where(Task.user_id == user_id)

        # Filter by keyword (title or description contains)
        if keyword:
            search_term = f"%{keyword}%"
            statement = statement.where(
                (Task.title.ilike(search_term)) | (Task.description.ilike(search_term))
            )

        # Filter by completion status
        if status is not None:
            statement = statement.where(Task.completed == status)

        # Filter by priority
        if priority is not None:
            statement = statement.where(Task.priority == priority)

        # Filter by tag (PostgreSQL JSON containment)
        if tag:
            # Case-insensitive tag search - we need to check if any tag matches
            # Using string comparison on the JSON representation
            search_tag = tag.lower()
            statement = statement.where(
                Task.tags.cast(sa.String).ilike(f"%{search_tag}%")
            )

        # Apply sorting
        if sort_by == "priority":
            # Sort by priority with custom order (high=1, medium=2, low=3)
            priority_order = case(
                (Task.priority == Priority.high, 1),
                (Task.priority == Priority.medium, 2),
                (Task.priority == Priority.low, 3),
            )
            statement = statement.order_by(
                priority_order.asc() if sort_order == "asc" else priority_order.desc()
            )
        elif sort_by == "title":
            statement = statement.order_by(
                Task.title.asc() if sort_order == "asc" else Task.title.desc()
            )
        else:  # created_at or updated_at
            sort_field = getattr(Task, sort_by)
            statement = statement.order_by(
                sort_field.asc() if sort_order == "asc" else sort_field.desc()
            )

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_user_tags(self, user_id: UUID) -> list[str]:
        """List all unique tags used by a user across all tasks.

        Args:
            user_id: UUID of the task owner.

        Returns:
            list[str]: Alphabetically sorted list of unique tags.
        """
        statement = select(Task).where(Task.user_id == user_id)
        result = await self.session.execute(statement)
        tasks = list(result.scalars().all())

        # Collect all unique tags
        all_tags: set[str] = set()
        for task in tasks:
            all_tags.update(task.tags)

        return sorted(all_tags)

    # Helper methods

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        """Normalize and validate tags.

        Normalizes tags by:
        1. Stripping whitespace
        2. Filtering out empty strings
        3. Truncating to MAX_TAG_LENGTH
        4. Case-insensitive deduplication
        5. Limiting to MAX_TAGS

        Args:
            tags: Raw list of tags.

        Returns:
            list[str]: Normalized list of tags.
        """
        # Strip and filter empty strings
        cleaned = [tag.strip() for tag in tags if tag.strip()]

        # Truncate to max length
        truncated = [tag[:MAX_TAG_LENGTH] for tag in cleaned]

        # Case-insensitive deduplication (preserve first occurrence)
        seen: set[str] = set()
        deduped: list[str] = []
        for tag in truncated:
            lower = tag.lower()
            if lower not in seen:
                seen.add(lower)
                deduped.append(tag)

        # Limit to max tags
        return deduped[:MAX_TAGS]
