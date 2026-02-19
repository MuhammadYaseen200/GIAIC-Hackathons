"""MCP tool definitions and handlers for task management.

This module implements 10 MCP tools for the Evolution of Todo application:
1. add_task - Create task with title, description, priority, tags
2. list_tasks - List user's tasks with optional status filter
3. complete_task - Toggle task completion
4. update_task - Update title/description
5. delete_task - Delete task permanently
6. search_tasks - Search with keyword, status, priority, tag filters
7. update_priority - Change task priority
8. add_tags - Add tags to task
9. remove_tags - Remove tags from task
10. list_tags - List user's unique tags

All handlers import from app.services.task_service per ADR-010.
No imports from phase-2-web are permitted.

Reference: ADR-010-mcp-service-wrapping.md
"""

from typing import Any, Literal
from uuid import UUID

from mcp.types import TextContent, Tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Priority
from app.services.task_service import TaskService

# =============================================================================
# Tool Definitions (T-310)
# =============================================================================

TOOL_DEFINITIONS: list[Tool] = [
    Tool(
        name="add_task",
        description="Create a new task in the user's todo list. Returns the created task details.",
        inputSchema={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (1-200 characters, required)",
                    "minLength": 1,
                    "maxLength": 200,
                },
                "description": {
                    "type": "string",
                    "description": "Task description (optional, max 1000 characters)",
                    "maxLength": 1000,
                },
                "priority": {
                    "type": "string",
                    "description": "Task priority level (optional, defaults to 'medium')",
                    "enum": ["high", "medium", "low"],
                },
                "tags": {
                    "type": "array",
                    "description": "Task tags for categorization (optional, max 10 tags)",
                    "items": {"type": "string", "maxLength": 50},
                    "maxItems": 10,
                },
            },
            "required": ["title"],
        },
    ),
    Tool(
        name="list_tasks",
        description="List all tasks for the authenticated user. Optionally filter by completion status.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by completion status: 'completed', 'incomplete', or 'all' (default: 'all')",
                    "enum": ["completed", "incomplete", "all"],
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="complete_task",
        description="Toggle a task's completion status. If incomplete, marks as complete. If complete, marks as incomplete.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to toggle (required)",
                    "format": "uuid",
                },
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="update_task",
        description="Update a task's title and/or description. At least one field must be provided.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to update (required)",
                    "format": "uuid",
                },
                "title": {
                    "type": "string",
                    "description": "New task title (optional, 1-200 characters)",
                    "minLength": 1,
                    "maxLength": 200,
                },
                "description": {
                    "type": "string",
                    "description": "New task description (optional, max 1000 characters)",
                    "maxLength": 1000,
                },
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="delete_task",
        description="Permanently delete a task from the user's todo list. This action cannot be undone.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to delete (required)",
                    "format": "uuid",
                },
            },
            "required": ["task_id"],
        },
    ),
    Tool(
        name="search_tasks",
        description="Search and filter tasks with multiple criteria. All filters are optional and combined with AND logic.",
        inputSchema={
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "Search keyword to match in title or description (case-insensitive)",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by completion status",
                    "enum": ["completed", "incomplete"],
                },
                "priority": {
                    "type": "string",
                    "description": "Filter by priority level",
                    "enum": ["high", "medium", "low"],
                },
                "tag": {
                    "type": "string",
                    "description": "Filter by tag (case-insensitive match)",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Field to sort by (default: 'created_at')",
                    "enum": ["created_at", "updated_at", "priority", "title"],
                },
                "sort_order": {
                    "type": "string",
                    "description": "Sort order (default: 'desc')",
                    "enum": ["asc", "desc"],
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="update_priority",
        description="Change a task's priority level to high, medium, or low.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to update (required)",
                    "format": "uuid",
                },
                "priority": {
                    "type": "string",
                    "description": "New priority level (required)",
                    "enum": ["high", "medium", "low"],
                },
            },
            "required": ["task_id", "priority"],
        },
    ),
    Tool(
        name="add_tags",
        description="Add one or more tags to a task. Duplicate tags are ignored. Maximum 10 tags per task.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to update (required)",
                    "format": "uuid",
                },
                "tags": {
                    "type": "array",
                    "description": "Tags to add (required, each max 50 characters)",
                    "items": {"type": "string", "maxLength": 50},
                    "minItems": 1,
                    "maxItems": 10,
                },
            },
            "required": ["task_id", "tags"],
        },
    ),
    Tool(
        name="remove_tags",
        description="Remove one or more tags from a task. Non-existent tags are ignored.",
        inputSchema={
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task to update (required)",
                    "format": "uuid",
                },
                "tags": {
                    "type": "array",
                    "description": "Tags to remove (required, case-insensitive match)",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["task_id", "tags"],
        },
    ),
    Tool(
        name="list_tags",
        description="List all unique tags used across the user's tasks. Returns alphabetically sorted list.",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
]


# =============================================================================
# Tool Handlers (T-312 & T-313)
# =============================================================================


async def handle_add_task(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle add_task tool call.

    Creates a new task with the provided title, description, priority, and tags.

    Args:
        arguments: Tool arguments containing title, description, priority, tags.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with success message and task details.
    """
    task_service = TaskService(session)

    # Parse priority if provided
    priority = None
    if "priority" in arguments and arguments["priority"]:
        priority = Priority(arguments["priority"])

    task = await task_service.create_task(
        user_id=user_id,
        title=arguments["title"],
        description=arguments.get("description", ""),
        priority=priority,
        tags=arguments.get("tags", []),
    )

    # Format response
    priority_str = task.priority.value if task.priority else "medium"
    tags_str = ", ".join(task.tags) if task.tags else "none"

    return TextContent(
        type="text",
        text=(
            f"Created task: {task.title}\n"
            f"ID: {task.id}\n"
            f"Priority: {priority_str}\n"
            f"Tags: {tags_str}"
        ),
    )


async def handle_list_tasks(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle list_tasks tool call.

    Lists all tasks for the user, optionally filtered by completion status.

    Args:
        arguments: Tool arguments containing optional status filter.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with formatted task list.
    """
    task_service = TaskService(session)

    # Get status filter
    status_filter = arguments.get("status", "all")

    # Use search_tasks for filtering capability
    if status_filter == "completed":
        tasks = await task_service.search_tasks(user_id=user_id, status=True)
    elif status_filter == "incomplete":
        tasks = await task_service.search_tasks(user_id=user_id, status=False)
    else:
        tasks = await task_service.list_tasks(user_id=user_id)

    if not tasks:
        return TextContent(type="text", text="No tasks found.")

    # Format task list
    lines = [f"Found {len(tasks)} task(s):\n"]
    for i, task in enumerate(tasks, 1):
        status_icon = "[x]" if task.completed else "[ ]"
        priority_badge = f"[{task.priority.value.upper()}]" if task.priority else ""
        tags_str = f" #{' #'.join(task.tags)}" if task.tags else ""
        lines.append(
            f"{i}. {status_icon} {priority_badge} {task.title}{tags_str}\n"
            f"   ID: {task.id}"
        )

    return TextContent(type="text", text="\n".join(lines))


async def handle_complete_task(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle complete_task tool call.

    Toggles the completion status of a task.

    Args:
        arguments: Tool arguments containing task_id.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with completion status change.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])
    task = await task_service.toggle_complete(user_id=user_id, task_id=task_id)

    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    status_text = "completed" if task.completed else "incomplete"
    return TextContent(
        type="text",
        text=f"Task '{task.title}' marked as {status_text}.",
    )


async def handle_update_task(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle update_task tool call.

    Updates a task's title and/or description.

    Args:
        arguments: Tool arguments containing task_id, optional title and description.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with update confirmation.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])
    title = arguments.get("title")
    description = arguments.get("description")

    # Validate at least one field is provided
    if title is None and description is None:
        return TextContent(
            type="text",
            text="Error: At least one of 'title' or 'description' must be provided.",
        )

    task = await task_service.update_task(
        user_id=user_id,
        task_id=task_id,
        title=title,
        description=description,
    )

    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    return TextContent(
        type="text",
        text=f"Task updated: {task.title}",
    )


async def handle_delete_task(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle delete_task tool call.

    Permanently deletes a task.

    Args:
        arguments: Tool arguments containing task_id.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with deletion confirmation.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])

    # Get task details before deletion for confirmation message
    task = await task_service.get_task(user_id=user_id, task_id=task_id)
    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    task_title = task.title
    deleted = await task_service.delete_task(user_id=user_id, task_id=task_id)

    if not deleted:
        return TextContent(type="text", text=f"Failed to delete task: {task_id}")

    return TextContent(
        type="text",
        text=f"Task deleted: {task_title}",
    )


async def handle_search_tasks(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle search_tasks tool call.

    Searches tasks with multiple filter criteria.

    Args:
        arguments: Tool arguments containing optional keyword, status, priority, tag, sort options.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with formatted search results.
    """
    task_service = TaskService(session)

    # Parse arguments
    keyword = arguments.get("keyword")
    status_str = arguments.get("status")
    priority_str = arguments.get("priority")
    tag = arguments.get("tag")
    sort_by = arguments.get("sort_by", "created_at")
    sort_order = arguments.get("sort_order", "desc")

    # Convert status string to boolean
    status: bool | None = None
    if status_str == "completed":
        status = True
    elif status_str == "incomplete":
        status = False

    # Convert priority string to enum
    priority: Priority | None = None
    if priority_str:
        priority = Priority(priority_str)

    # Cast sort_by and sort_order to literals
    sort_by_literal: Literal["created_at", "updated_at", "priority", "title"] = sort_by  # type: ignore
    sort_order_literal: Literal["asc", "desc"] = sort_order  # type: ignore

    tasks = await task_service.search_tasks(
        user_id=user_id,
        keyword=keyword,
        status=status,
        priority=priority,
        tag=tag,
        sort_by=sort_by_literal,
        sort_order=sort_order_literal,
    )

    if not tasks:
        return TextContent(type="text", text="No tasks match the search criteria.")

    # Format search results
    lines = [f"Found {len(tasks)} matching task(s):\n"]
    for i, task in enumerate(tasks, 1):
        status_icon = "[x]" if task.completed else "[ ]"
        priority_badge = f"[{task.priority.value.upper()}]" if task.priority else ""
        tags_str = f" #{' #'.join(task.tags)}" if task.tags else ""
        lines.append(
            f"{i}. {status_icon} {priority_badge} {task.title}{tags_str}\n"
            f"   ID: {task.id}"
        )

    return TextContent(type="text", text="\n".join(lines))


async def handle_update_priority(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle update_priority tool call.

    Changes a task's priority level.

    Args:
        arguments: Tool arguments containing task_id and priority.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with priority update confirmation.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])
    priority = Priority(arguments["priority"])

    task = await task_service.update_priority(
        user_id=user_id,
        task_id=task_id,
        priority=priority,
    )

    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    return TextContent(
        type="text",
        text=f"Task '{task.title}' priority changed to {priority.value}.",
    )


async def handle_add_tags(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle add_tags tool call.

    Adds tags to a task.

    Args:
        arguments: Tool arguments containing task_id and tags.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with tag update confirmation.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])
    tags = arguments["tags"]

    task = await task_service.add_tags(
        user_id=user_id,
        task_id=task_id,
        tags=tags,
    )

    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    current_tags = ", ".join(task.tags) if task.tags else "none"
    return TextContent(
        type="text",
        text=f"Tags added to '{task.title}'. Current tags: {current_tags}",
    )


async def handle_remove_tags(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle remove_tags tool call.

    Removes tags from a task.

    Args:
        arguments: Tool arguments containing task_id and tags.
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with tag removal confirmation.
    """
    task_service = TaskService(session)

    task_id = UUID(arguments["task_id"])
    tags = arguments["tags"]

    task = await task_service.remove_tags(
        user_id=user_id,
        task_id=task_id,
        tags=tags,
    )

    if not task:
        return TextContent(type="text", text=f"Task not found: {task_id}")

    remaining_tags = ", ".join(task.tags) if task.tags else "none"
    return TextContent(
        type="text",
        text=f"Tags removed from '{task.title}'. Remaining tags: {remaining_tags}",
    )


async def handle_list_tags(
    arguments: dict[str, Any],
    user_id: UUID,
    session: AsyncSession,
) -> TextContent:
    """Handle list_tags tool call.

    Lists all unique tags used by the user.

    Args:
        arguments: Tool arguments (none required).
        user_id: Authenticated user's UUID.
        session: Async database session.

    Returns:
        TextContent with alphabetically sorted tag list.
    """
    task_service = TaskService(session)

    tags = await task_service.list_user_tags(user_id=user_id)

    if not tags:
        return TextContent(type="text", text="No tags found.")

    return TextContent(
        type="text",
        text=f"Your tags ({len(tags)}): {', '.join(tags)}",
    )


# =============================================================================
# Tool Handler Registry
# =============================================================================

TOOL_HANDLERS: dict[str, Any] = {
    "add_task": handle_add_task,
    "list_tasks": handle_list_tasks,
    "complete_task": handle_complete_task,
    "update_task": handle_update_task,
    "delete_task": handle_delete_task,
    "search_tasks": handle_search_tasks,
    "update_priority": handle_update_priority,
    "add_tags": handle_add_tags,
    "remove_tags": handle_remove_tags,
    "list_tags": handle_list_tags,
}


def get_tool_handler(tool_name: str):
    """Get the handler function for a tool by name.

    Args:
        tool_name: Name of the MCP tool.

    Returns:
        Handler function or None if not found.
    """
    return TOOL_HANDLERS.get(tool_name)
