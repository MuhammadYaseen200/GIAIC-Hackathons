"""ChatKit API endpoint.

This module provides the FastAPI endpoint for ChatKit integration.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.chatkit.server import TodoChatKitServer
from app.chatkit.store import ChatContext, DatabaseStore
from app.models.user import User
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chatkit", tags=["chatkit"])

# Create the store and server instances
store = DatabaseStore()
server = TodoChatKitServer(store)


# Register tool handlers
async def add_task_handler(context: ChatContext, **kwargs):
    """Handle add_task tool call."""
    service = TaskService(context.db)
    title = kwargs.get("title", "Untitled Task")
    description = kwargs.get("description")
    priority = kwargs.get("priority", "medium")
    tags = kwargs.get("tags", [])

    task = await service.create_task(
        user_id=context.user_id,
        title=title,
        description=description,
        priority=priority,
        tags=tags,
    )
    return {"success": True, "task_id": str(task.id), "title": task.title}


async def list_tasks_handler(context: ChatContext, **kwargs):
    """Handle list_tasks tool call."""
    service = TaskService(context.db)
    status = kwargs.get("status", "all")

    tasks = await service.get_tasks(
        user_id=context.user_id,
        status=None if status == "all" else status,
    )
    return {
        "success": True,
        "count": len(tasks),
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "completed": t.completed,
                "priority": t.priority,
                "tags": t.tags or [],
            }
            for t in tasks
        ],
    }


async def complete_task_handler(context: ChatContext, **kwargs):
    """Handle complete_task tool call."""
    service = TaskService(context.db)
    task_id = kwargs.get("task_id")

    task = await service.toggle_complete(user_id=context.user_id, task_id=task_id)
    if task:
        return {"success": True, "task_id": str(task.id), "completed": task.completed}
    return {"success": False, "error": "Task not found"}


async def delete_task_handler(context: ChatContext, **kwargs):
    """Handle delete_task tool call."""
    service = TaskService(context.db)
    task_id = kwargs.get("task_id")

    result = await service.delete_task(user_id=context.user_id, task_id=task_id)
    if result:
        return {"success": True, "task_id": task_id}
    return {"success": False, "error": "Task not found"}


async def update_task_handler(context: ChatContext, **kwargs):
    """Handle update_task tool call."""
    service = TaskService(context.db)
    task_id = kwargs.get("task_id")

    update_data = {}
    if "title" in kwargs:
        update_data["title"] = kwargs["title"]
    if "description" in kwargs:
        update_data["description"] = kwargs["description"]
    if "priority" in kwargs:
        update_data["priority"] = kwargs["priority"]

    task = await service.update_task(
        user_id=context.user_id,
        task_id=task_id,
        **update_data,
    )
    if task:
        return {"success": True, "task_id": str(task.id), "title": task.title}
    return {"success": False, "error": "Task not found"}


# Register handlers
server.register_tool_handler("add_task", add_task_handler)
server.register_tool_handler("list_tasks", list_tasks_handler)
server.register_tool_handler("complete_task", complete_task_handler)
server.register_tool_handler("delete_task", delete_task_handler)
server.register_tool_handler("update_task", update_task_handler)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def chatkit_handler(
    request: Request,
    path: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    """Handle all ChatKit API requests.

    ChatKit uses a specific protocol with multiple endpoints.
    This handler delegates to the ChatKitServer.process() method.
    """
    from chatkit.server import StreamingResult, NonStreamingResult
    from fastapi.responses import Response

    # Create context with user and db session
    context = ChatContext(user_id=current_user.id, db=db)

    # Get request body
    body = await request.body()

    # Process the request through ChatKitServer
    result = await server.process(body, context)

    if isinstance(result, StreamingResult):
        # Streaming response - return as SSE
        async def generate():
            async for event in result:
                # Convert event to proper SSE format
                event_data = event.json() if hasattr(event, 'json') else str(event)
                yield f"data: {event_data}\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming response - return as JSON
        return Response(
            content=result.json,
            media_type="application/json",
        )
