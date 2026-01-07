"""MCP (Model Context Protocol) module for Evolution of Todo.

This module provides the MCP server and tools for AI agent integration.
All tools wrap the TaskService from app.services.task_service per ADR-010.

Usage:
    from app.mcp.server import mcp_server, execute_tool
    from app.mcp.tools import TOOL_DEFINITIONS

Components:
- server.py: MCP server instance and tool execution
- tools/: Tool definitions and handlers

Reference: ADR-010-mcp-service-wrapping.md
"""

from app.mcp.server import (
    SERVER_INFO,
    execute_tool,
    get_mcp_server,
    get_tool_names,
    mcp_server,
)
from app.mcp.tools import TOOL_DEFINITIONS

__all__ = [
    "mcp_server",
    "execute_tool",
    "get_mcp_server",
    "get_tool_names",
    "TOOL_DEFINITIONS",
    "SERVER_INFO",
]
