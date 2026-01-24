"""ChatKit API endpoint.

This module provides the FastAPI endpoint for ChatKit integration.
"""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_session
from app.chatkit.server import TodoChatKitServer
from app.chatkit.store import ChatContext, DatabaseStore
from app.models.user import User
from app.models.task import Priority
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
    priority_str = kwargs.get("priority", "medium")

    # Convert string priority to Priority enum
    try:
        priority = Priority(priority_str.lower())
    except ValueError:
        priority = Priority.medium
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
    status_filter = kwargs.get("status", "all")

    # Use search_tasks for filtering support
    is_completed = None
    if status_filter == "completed":
        is_completed = True
    elif status_filter == "pending":
        is_completed = False

    tasks = await service.search_tasks(
        user_id=context.user_id,
        status=is_completed,
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
    task_id_str = kwargs.get("task_id")
    if not task_id_str:
        return {"success": False, "error": "task_id is required"}

    try:
        task_id = UUID(task_id_str)
    except ValueError:
        return {"success": False, "error": "Invalid task_id format"}

    task = await service.toggle_complete(user_id=context.user_id, task_id=task_id)
    if task:
        return {"success": True, "task_id": str(task.id), "completed": task.completed}
    return {"success": False, "error": "Task not found"}


async def delete_task_handler(context: ChatContext, **kwargs):
    """Handle delete_task tool call."""
    service = TaskService(context.db)
    task_id_str = kwargs.get("task_id")
    if not task_id_str:
        return {"success": False, "error": "task_id is required"}

    try:
        task_id = UUID(task_id_str)
    except ValueError:
        return {"success": False, "error": "Invalid task_id format"}

    result = await service.delete_task(user_id=context.user_id, task_id=task_id)
    if result:
        return {"success": True, "task_id": task_id}
    return {"success": False, "error": "Task not found"}


async def update_task_handler(context: ChatContext, **kwargs):
    """Handle update_task tool call."""
    service = TaskService(context.db)
    task_id_str = kwargs.get("task_id")
    if not task_id_str:
        return {"success": False, "error": "task_id is required"}

    try:
        task_id = UUID(task_id_str)
    except ValueError:
        return {"success": False, "error": "Invalid task_id format"}

    update_data = {}
    if "title" in kwargs:
        update_data["title"] = kwargs["title"]
    if "description" in kwargs:
        update_data["description"] = kwargs["description"]
    if "priority" in kwargs:
        try:
            update_data["priority"] = Priority(kwargs["priority"].lower())
        except ValueError:
            pass

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


@router.get("/health")
async def chatkit_health():
    """Simple health check for ChatKit router."""
    return {"status": "healthy", "message": "ChatKit router is working"}


@router.api_route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def chatkit_handler(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    path: str = "",
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
    try:
        result = await server.process(body, context)
    except Exception as e:
        logger.error(f"ChatKit processing error: {type(e).__name__}: {e}", exc_info=True)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": {"message": f"{type(e).__name__}: {str(e)}"}}
        )

    if isinstance(result, StreamingResult):
        # Streaming response - return as SSE
        # IMPORTANT: StreamingResult already yields properly formatted SSE bytes
        # in the format: b"data: {json}\n\n"
        # We just need to decode and yield, NOT re-format
        async def generate():
            async for event in result:
                # StreamingResult yields bytes that are already SSE-formatted
                if isinstance(event, bytes):
                    yield event.decode('utf-8')
                else:
                    # Fallback for non-bytes (shouldn't happen with ChatKit)
                    yield str(event)

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
