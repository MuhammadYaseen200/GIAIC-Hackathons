"""AI Agent configuration and execution for Phase 3 chatbot.

Configures the OpenAI Agents SDK to use Google Gemini via OpenAI-compatible
endpoint per ADR-009 (Hybrid AI Engine).

This module provides:
- Gemini model configuration via OpenAI-compatible endpoint
- run_agent function for executing chat interactions
- Tool call processing and result handling
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompts import SYSTEM_PROMPT
from app.core.config import settings
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)


# =============================================================================
# T-314: Gemini Model Configuration
# =============================================================================

# Configure Gemini via OpenAI-compatible endpoint (per ADR-009)
gemini_client = AsyncOpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai",
)


# =============================================================================
# Tool Schema Definitions (OpenAI Function Calling Format)
# =============================================================================

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title (1-200 characters)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional task description (max 1000 chars)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Task priority level (default: medium)",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional list of tags (max 10 tags)",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks for the user",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Toggle the completion status of a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to complete",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task permanently",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to delete",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update a task's title and/or description",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to update",
                    },
                    "title": {
                        "type": "string",
                        "description": "New task title (optional)",
                    },
                    "description": {
                        "type": "string",
                        "description": "New task description (optional)",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tasks",
            "description": "Search and filter tasks by keyword, status, priority, or tag",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword for title/description",
                    },
                    "status": {
                        "type": "boolean",
                        "description": "Filter by completion status (true=completed, false=pending)",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "Filter by priority level",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Filter by tag name",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["created_at", "updated_at", "priority", "title"],
                        "description": "Sort field (default: created_at)",
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort order (default: desc)",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_priority",
            "description": "Update a task's priority level",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task to update",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                        "description": "New priority level",
                    },
                },
                "required": ["task_id", "priority"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_tags",
            "description": "Add tags to a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to add (max 10 total)",
                    },
                },
                "required": ["task_id", "tags"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "remove_tags",
            "description": "Remove tags from a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID of the task",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags to remove",
                    },
                },
                "required": ["task_id", "tags"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tags",
            "description": "List all unique tags used by the user",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]


# =============================================================================
# T-315: Agent Result and Run Function
# =============================================================================


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        response: The text response from the agent.
        tool_calls: List of tool calls made during execution, each containing
            name, arguments, and result.
    """

    response: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


async def handle_tool_call(
    tool_name: str,
    arguments: str,
    user_id: UUID,
    session: AsyncSession,
) -> dict[str, Any]:
    """Execute a tool call and return the result.

    Args:
        tool_name: Name of the tool to execute.
        arguments: JSON string of tool arguments.
        user_id: UUID of the current user.
        session: Database session for queries.

    Returns:
        dict containing the tool execution result.
    """
    from app.models.task import Priority
    from app.services.task_service import TaskService

    service = TaskService(session)
    args = json.loads(arguments) if arguments else {}

    try:
        if tool_name == "add_task":
            priority = None
            if "priority" in args:
                priority = Priority(args["priority"].lower())
            task = await service.create_task(
                user_id=user_id,
                title=args["title"],
                description=args.get("description", ""),
                priority=priority,
                tags=args.get("tags"),
            )
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "priority": task.priority.value,
                "tags": task.tags,
                "message": f"Task '{task.title}' created successfully.",
            }

        elif tool_name == "list_tasks":
            tasks = await service.list_tasks(user_id)
            return {
                "success": True,
                "count": len(tasks),
                "tasks": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "completed": t.completed,
                        "priority": t.priority.value,
                        "tags": t.tags,
                    }
                    for t in tasks
                ],
            }

        elif tool_name == "complete_task":
            task_id = UUID(args["task_id"])
            task = await service.toggle_complete(user_id, task_id)
            if not task:
                return {"success": False, "error": "Task not found."}
            status = "completed" if task.completed else "pending"
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "completed": task.completed,
                "message": f"Task '{task.title}' marked as {status}.",
            }

        elif tool_name == "delete_task":
            task_id = UUID(args["task_id"])
            # Get task title before deletion for confirmation message
            task = await service.get_task(user_id, task_id)
            if not task:
                return {"success": False, "error": "Task not found."}
            title = task.title
            deleted = await service.delete_task(user_id, task_id)
            if not deleted:
                return {"success": False, "error": "Failed to delete task."}
            return {
                "success": True,
                "task_id": str(task_id),
                "message": f"Task '{title}' deleted successfully.",
            }

        elif tool_name == "update_task":
            task_id = UUID(args["task_id"])
            task = await service.update_task(
                user_id=user_id,
                task_id=task_id,
                title=args.get("title"),
                description=args.get("description"),
            )
            if not task:
                return {"success": False, "error": "Task not found."}
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "description": task.description,
                "message": f"Task '{task.title}' updated successfully.",
            }

        elif tool_name == "search_tasks":
            priority = None
            if "priority" in args:
                priority = Priority(args["priority"].lower())
            tasks = await service.search_tasks(
                user_id=user_id,
                keyword=args.get("keyword"),
                status=args.get("status"),
                priority=priority,
                tag=args.get("tag"),
                sort_by=args.get("sort_by", "created_at"),
                sort_order=args.get("sort_order", "desc"),
            )
            return {
                "success": True,
                "count": len(tasks),
                "tasks": [
                    {
                        "id": str(t.id),
                        "title": t.title,
                        "completed": t.completed,
                        "priority": t.priority.value,
                        "tags": t.tags,
                    }
                    for t in tasks
                ],
            }

        elif tool_name == "update_priority":
            task_id = UUID(args["task_id"])
            priority = Priority(args["priority"].lower())
            task = await service.update_priority(user_id, task_id, priority)
            if not task:
                return {"success": False, "error": "Task not found."}
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "priority": task.priority.value,
                "message": f"Task '{task.title}' priority set to {task.priority.value.upper()}.",
            }

        elif tool_name == "add_tags":
            task_id = UUID(args["task_id"])
            task = await service.add_tags(user_id, task_id, args["tags"])
            if not task:
                return {"success": False, "error": "Task not found."}
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "tags": task.tags,
                "message": f"Tags added to '{task.title}'.",
            }

        elif tool_name == "remove_tags":
            task_id = UUID(args["task_id"])
            task = await service.remove_tags(user_id, task_id, args["tags"])
            if not task:
                return {"success": False, "error": "Task not found."}
            return {
                "success": True,
                "task_id": str(task.id),
                "title": task.title,
                "tags": task.tags,
                "message": f"Tags removed from '{task.title}'.",
            }

        elif tool_name == "list_tags":
            tags = await service.list_user_tags(user_id)
            return {
                "success": True,
                "count": len(tags),
                "tags": tags,
            }

        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.exception(f"Tool call failed: {tool_name}")
        return {"success": False, "error": f"Tool execution failed: {str(e)}"}


async def run_agent(
    user_id: UUID,
    conversation: Conversation,
    message: str,
    session: AsyncSession,
) -> AgentResult:
    """Run the AI agent with a user message.

    This function:
    1. Builds messages from conversation history
    2. Calls Gemini with available tools
    3. Processes any tool calls
    4. Returns the agent's response

    Args:
        user_id: UUID of the current user.
        conversation: Conversation object with message history.
        message: The new user message.
        session: Database session for tool calls.

    Returns:
        AgentResult with response text and tool call details.
    """
    # Build messages from conversation history
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Add conversation history
    for msg in conversation.messages:
        messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })

    # Add the new user message
    messages.append({"role": "user", "content": message})

    tool_calls_made: list[dict[str, Any]] = []
    final_response = ""

    try:
        # Initial call to Gemini
        response = await gemini_client.chat.completions.create(
            model=settings.GEMINI_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            timeout=settings.AGENT_TIMEOUT_SECONDS,
        )

        assistant_message = response.choices[0].message

        # Process tool calls if any
        if assistant_message.tool_calls:
            # Add assistant's tool call message to history
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_message.tool_calls
                ],
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = tool_call.function.arguments

                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

                result = await handle_tool_call(
                    tool_name=tool_name,
                    arguments=tool_args,
                    user_id=user_id,
                    session=session,
                )

                tool_calls_made.append({
                    "name": tool_name,
                    "arguments": json.loads(tool_args) if tool_args else {},
                    "result": result,
                })

                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })

            # Get final response after tool execution
            final_response_obj = await gemini_client.chat.completions.create(
                model=settings.GEMINI_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                timeout=settings.AGENT_TIMEOUT_SECONDS,
            )
            final_response = final_response_obj.choices[0].message.content or ""
        else:
            # No tool calls, use the initial response
            final_response = assistant_message.content or ""

    except Exception as e:
        logger.exception("Agent execution failed")
        final_response = f"I apologize, but I encountered an error: {str(e)}. Please try again."

    return AgentResult(
        response=final_response,
        tool_calls=tool_calls_made,
    )


async def verify_gemini_connection() -> bool:
    """Verify that Gemini API is configured and accessible.

    Returns:
        bool: True if connection is successful.

    Raises:
        Exception: If connection fails.
    """
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not configured")

    response = await gemini_client.chat.completions.create(
        model=settings.GEMINI_MODEL,
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10,
    )

    if response.choices and response.choices[0].message.content:
        logger.info("Gemini connection verified successfully")
        return True

    raise ValueError("Gemini returned empty response")
