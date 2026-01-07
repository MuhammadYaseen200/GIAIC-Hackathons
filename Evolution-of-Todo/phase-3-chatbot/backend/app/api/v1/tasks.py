"""Task API endpoints for CRUD operations.

Provides REST endpoints for managing todo tasks:
- POST /tasks - Create a new task
- GET /tasks - List all tasks for current user
- GET /tasks/{task_id} - Get a specific task
- PUT /tasks/{task_id} - Update a task
- DELETE /tasks/{task_id} - Delete a task
- PATCH /tasks/{task_id}/complete - Toggle task completion

All endpoints require authentication and enforce multi-tenancy.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SessionDep
from app.models.task import Priority
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class CreateTaskRequest(BaseModel):
    """Request body for creating a task."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    priority: Literal["high", "medium", "low"] | None = Field(default=None)
    tags: list[str] = Field(default_factory=list)


class UpdateTaskRequest(BaseModel):
    """Request body for updating a task."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    priority: Literal["high", "medium", "low"] | None = Field(default=None)
    tags: list[str] | None = Field(default=None)


class TaskData(BaseModel):
    """Task data for API responses."""

    id: str
    user_id: str
    title: str
    description: str
    completed: bool
    priority: str
    tags: list[str]
    created_at: str
    updated_at: str


class TaskSuccessResponse(BaseModel):
    """Response for single task operations."""

    success: bool = True
    data: TaskData


class TaskListResponse(BaseModel):
    """Response for task list operations."""

    success: bool = True
    data: list[TaskData]
    meta: dict


class DeleteResponse(BaseModel):
    """Response for delete operations."""

    success: bool = True
    data: dict


# =============================================================================
# Helper Functions
# =============================================================================


def task_to_dict(task) -> TaskData:
    """Convert Task model to response dict."""
    return TaskData(
        id=str(task.id),
        user_id=str(task.user_id),
        title=task.title,
        description=task.description,
        completed=task.completed,
        priority=task.priority.value if task.priority else "medium",
        tags=task.tags or [],
        created_at=task.created_at.isoformat(),
        updated_at=task.updated_at.isoformat(),
    )


# =============================================================================
# Endpoints
# =============================================================================


@router.post("", response_model=TaskSuccessResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    request: CreateTaskRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> TaskSuccessResponse:
    """Create a new task for the authenticated user.

    Args:
        request: Task creation data (title, description, priority, tags).
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        TaskSuccessResponse: Created task data.
    """
    task_service = TaskService(session)

    # Convert string priority to enum if provided
    priority_enum = None
    if request.priority:
        priority_enum = Priority(request.priority)

    task = await task_service.create_task(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
        priority=priority_enum,
        tags=request.tags,
    )
    await session.commit()
    return TaskSuccessResponse(data=task_to_dict(task))


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    session: SessionDep,
    current_user: CurrentUser,
) -> TaskListResponse:
    """List all tasks for the authenticated user.

    Args:
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        TaskListResponse: List of tasks with metadata.
    """
    task_service = TaskService(session)
    tasks = await task_service.list_tasks(user_id=current_user.id)
    return TaskListResponse(
        data=[task_to_dict(t) for t in tasks],
        meta={
            "total": len(tasks),
            "limit": 100,
            "offset": 0,
        },
    )


@router.get("/{task_id}", response_model=TaskSuccessResponse)
async def get_task(
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> TaskSuccessResponse:
    """Get a specific task by ID.

    Args:
        task_id: UUID of the task to retrieve.
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        TaskSuccessResponse: Task data.

    Raises:
        HTTPException: 404 if task not found or not owned by user.
    """
    task_service = TaskService(session)
    task = await task_service.get_task(user_id=current_user.id, task_id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "Task not found"},
        )

    return TaskSuccessResponse(data=task_to_dict(task))


@router.put("/{task_id}", response_model=TaskSuccessResponse)
async def update_task(
    task_id: UUID,
    request: UpdateTaskRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> TaskSuccessResponse:
    """Update a task's fields.

    Args:
        task_id: UUID of the task to update.
        request: Update data (title, description, priority, tags).
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        TaskSuccessResponse: Updated task data.

    Raises:
        HTTPException: 404 if task not found or not owned by user.
    """
    task_service = TaskService(session)

    # Convert string priority to enum if provided
    priority_enum = None
    if request.priority:
        priority_enum = Priority(request.priority)

    task = await task_service.update_task(
        user_id=current_user.id,
        task_id=task_id,
        title=request.title,
        description=request.description,
        priority=priority_enum,
        tags=request.tags,
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "Task not found"},
        )

    await session.commit()
    return TaskSuccessResponse(data=task_to_dict(task))


@router.delete("/{task_id}", response_model=DeleteResponse)
async def delete_task(
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> DeleteResponse:
    """Delete a task.

    Args:
        task_id: UUID of the task to delete.
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        DeleteResponse: Confirmation of deletion.

    Raises:
        HTTPException: 404 if task not found or not owned by user.
    """
    task_service = TaskService(session)
    deleted = await task_service.delete_task(user_id=current_user.id, task_id=task_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "Task not found"},
        )

    await session.commit()
    return DeleteResponse(data={"id": str(task_id), "deleted": True})


@router.patch("/{task_id}/complete", response_model=TaskSuccessResponse)
async def toggle_complete(
    task_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> TaskSuccessResponse:
    """Toggle a task's completion status.

    Args:
        task_id: UUID of the task to toggle.
        session: Database session.
        current_user: Authenticated user from JWT.

    Returns:
        TaskSuccessResponse: Updated task data with new completion status.

    Raises:
        HTTPException: 404 if task not found or not owned by user.
    """
    task_service = TaskService(session)
    task = await task_service.toggle_complete(user_id=current_user.id, task_id=task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TASK_NOT_FOUND", "message": "Task not found"},
        )

    await session.commit()
    return TaskSuccessResponse(data=task_to_dict(task))
