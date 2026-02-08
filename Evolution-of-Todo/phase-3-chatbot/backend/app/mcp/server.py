"""MCP Server for Evolution of Todo.

This module implements the Model Context Protocol (MCP) server that exposes
task management tools to AI agents. The server wraps the TaskService business
logic per ADR-010 (MCP Service Wrapping Strategy).

Server Name: evolution-of-todo-mcp

Tools Available:
- add_task: Create a new task
- list_tasks: List user's tasks
- complete_task: Toggle task completion
- update_task: Update task title/description
- delete_task: Delete a task
- search_tasks: Search tasks with filters
- update_priority: Change task priority
- add_tags: Add tags to a task
- remove_tags: Remove tags from a task
- list_tags: List user's unique tags

Reference: ADR-010-mcp-service-wrapping.md
"""

from typing import Any
from uuid import UUID

from mcp.server import Server
from mcp.types import TextContent, Tool

from app.core.database import async_session_factory
from app.mcp.tools.task_tools import (
    TOOL_DEFINITIONS,
    TOOL_HANDLERS,
    get_tool_handler,
)

# =============================================================================
# MCP Server Instance
# =============================================================================

mcp_server = Server("evolution-of-todo-mcp")


# =============================================================================
# Tool Registration
# =============================================================================


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools.

    Returns:
        List of 10 Tool definitions for task management.
    """
    return TOOL_DEFINITIONS


# =============================================================================
# Tool Execution
# =============================================================================


async def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    user_id: UUID,
) -> list[TextContent]:
    """Execute an MCP tool with the given arguments.

    This is the main entry point for tool execution. It:
    1. Looks up the tool handler by name
    2. Creates a database session
    3. Calls the handler with the session and user context
    4. Returns the result as a list of TextContent

    Args:
        tool_name: Name of the tool to execute.
        arguments: Tool arguments from the MCP request.
        user_id: Authenticated user's UUID for multi-tenancy.

    Returns:
        List containing a single TextContent with the result.

    Raises:
        ValueError: If the tool is not found.
    """
    handler = get_tool_handler(tool_name)
    if not handler:
        return [
            TextContent(
                type="text",
                text=f"Error: Unknown tool '{tool_name}'",
            )
        ]

    # Execute with database session
    async with async_session_factory() as session:
        try:
            result = await handler(arguments, user_id, session)
            await session.commit()
            return [result]
        except ValueError as e:
            await session.rollback()
            return [
                TextContent(
                    type="text",
                    text=f"Validation error: {str(e)}",
                )
            ]
        except Exception as e:
            await session.rollback()
            return [
                TextContent(
                    type="text",
                    text=f"Error executing tool: {str(e)}",
                )
            ]


# =============================================================================
# Server Utilities
# =============================================================================


def get_mcp_server() -> Server:
    """Get the MCP server instance.

    Returns:
        The configured MCP server.
    """
    return mcp_server


def get_tool_names() -> list[str]:
    """Get list of available tool names.

    Returns:
        List of tool name strings.
    """
    return list(TOOL_HANDLERS.keys())


# =============================================================================
# Server Metadata
# =============================================================================

SERVER_INFO = {
    "name": "evolution-of-todo-mcp",
    "version": "1.0.0",
    "description": "MCP server for Evolution of Todo task management",
    "tools_count": len(TOOL_DEFINITIONS),
    "tools": get_tool_names(),
}
