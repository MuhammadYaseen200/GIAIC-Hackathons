"""MCP tool definitions for Evolution of Todo.

This module exports all MCP tool handlers and definitions for task management.
All tools are designed to integrate with the TaskService from app.services.task_service.

Tools available:
- add_task: Create a new task
- list_tasks: List user's tasks with optional status filter
- complete_task: Toggle task completion status
- update_task: Update task title/description
- delete_task: Delete a task permanently
- search_tasks: Search tasks with multiple filters
- update_priority: Change task priority
- add_tags: Add tags to a task
- remove_tags: Remove tags from a task
- list_tags: List user's unique tags
"""

from app.mcp.tools.task_tools import (
    TOOL_DEFINITIONS,
    handle_add_tags,
    handle_add_task,
    handle_complete_task,
    handle_delete_task,
    handle_list_tags,
    handle_list_tasks,
    handle_remove_tags,
    handle_search_tasks,
    handle_update_priority,
    handle_update_task,
)

__all__ = [
    "TOOL_DEFINITIONS",
    "handle_add_task",
    "handle_list_tasks",
    "handle_complete_task",
    "handle_update_task",
    "handle_delete_task",
    "handle_search_tasks",
    "handle_update_priority",
    "handle_add_tags",
    "handle_remove_tags",
    "handle_list_tags",
]
