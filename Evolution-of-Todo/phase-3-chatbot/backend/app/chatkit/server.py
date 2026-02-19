"""ChatKit Server implementation with OpenRouter AI backend.

This module provides the ChatKitServer that handles user messages
and generates AI responses using OpenRouter API (OpenAI-compatible).
"""

import json
import logging
from collections.abc import AsyncIterator
from datetime import UTC, datetime

from chatkit.server import ChatKitServer
from chatkit.store import default_generate_id
from chatkit.types import (
    AssistantMessageContent,
    AssistantMessageContentPartAdded,
    AssistantMessageContentPartDone,
    AssistantMessageContentPartTextDelta,
    AssistantMessageItem,
    ThreadItemAddedEvent,
    ThreadItemDoneEvent,
    ThreadMetadata,
    ThreadStreamEvent,
    UserMessageItem,
)
from openai import AsyncOpenAI

from app.chatkit.store import ChatContext, DatabaseStore
from app.core.config import settings

logger = logging.getLogger(__name__)

# OpenRouter client via OpenAI-compatible endpoint
openrouter_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
    default_headers={
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
    },
)

# Tool schemas for task management
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Create a new task for the user",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "The task title"},
                    "description": {"type": "string", "description": "Optional task description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority level",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional tags for the task",
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
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "pending", "completed"],
                        "description": "Filter by task status",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a task as completed",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to complete"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to delete"},
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update an existing task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task ID to update"},
                    "title": {"type": "string", "description": "New task title"},
                    "description": {"type": "string", "description": "New task description"},
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority level",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are a helpful task management assistant. You help users manage their todo tasks.

Available actions:
- Add new tasks with titles, descriptions, priorities, and tags
- List tasks (all, pending, or completed)
- Complete tasks by marking them done
- Delete tasks
- Update existing tasks

When a user asks to do something with their tasks, use the appropriate tool.
Be concise and helpful in your responses.
Always confirm actions you've taken."""


class TodoChatKitServer(ChatKitServer[ChatContext]):
    """ChatKit Server implementation for Todo application."""

    def __init__(self, store: DatabaseStore):
        super().__init__(store)
        self._tool_handlers = {}

    def register_tool_handler(self, name: str, handler):
        """Register a handler for a tool."""
        self._tool_handlers[name] = handler

    async def respond(
        self,
        thread: ThreadMetadata,
        input_user_message: UserMessageItem | None,
        context: ChatContext,
    ) -> AsyncIterator[ThreadStreamEvent]:
        """Generate AI response for user messages.

        Args:
            thread: Metadata for the current thread.
            input_user_message: The incoming user message to respond to.
            context: Request context with user_id and db session.

        Yields:
            ThreadStreamEvent instances for the response.
        """
        # Build conversation messages
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Load thread items to build conversation history
        try:
            thread_items = await self.store.load_thread_items(
                thread_id=thread.id,
                after=None,
                limit=50,
                order="asc",
                context=context,
            )
            for item in thread_items.data:
                # Handle both dict and object access for items from database
                item_type = item.get("type") if isinstance(item, dict) else getattr(item, "type", None)
                item_content = item.get("content", []) if isinstance(item, dict) else getattr(item, "content", [])

                if item_type == "user_message":
                    text_parts = []
                    for part in item_content:
                        part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
                        part_text = part.get("text") if isinstance(part, dict) else getattr(part, "text", "")
                        if part_type == "input_text" and part_text:
                            text_parts.append(part_text)
                    if text_parts:
                        messages.append({"role": "user", "content": " ".join(text_parts)})
                elif item_type == "assistant_message":
                    text_parts = []
                    for part in item_content:
                        part_type = part.get("type") if isinstance(part, dict) else getattr(part, "type", None)
                        part_text = part.get("text") if isinstance(part, dict) else getattr(part, "text", "")
                        # Handle both 'text' and 'output_text' types
                        if part_type in ("text", "output_text") and part_text:
                            text_parts.append(part_text)
                    if text_parts:
                        messages.append({"role": "assistant", "content": " ".join(text_parts)})
        except Exception as e:
            logger.warning(f"Could not load thread history: {e}")

        # Add the current user message
        if input_user_message:
            text_parts = []
            for part in getattr(input_user_message, "content", []):
                if hasattr(part, "type") and part.type == "input_text":
                    text_parts.append(getattr(part, "text", ""))
            if text_parts:
                messages.append({"role": "user", "content": " ".join(text_parts)})

        if len(messages) <= 1:
            # No user messages to respond to
            return

        try:
            # Call OpenRouter API
            response = await openrouter_client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                timeout=settings.AGENT_TIMEOUT_SECONDS,
                stream=True,
            )

            # Generate a message ID and timestamp
            msg_id = default_generate_id("message")
            created_at = datetime.now(UTC)

            # Start the assistant message
            # Note: AssistantMessageItem requires thread_id and created_at
            assistant_item = AssistantMessageItem(
                id=msg_id,
                thread_id=thread.id,
                created_at=created_at,
                content=[],
            )

            yield ThreadItemAddedEvent(item=assistant_item)

            # Track content parts
            current_text = ""
            part_added = False
            accumulated_tool_calls = {}

            async for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                # Handle text content
                if delta.content:
                    if not part_added:
                        # Use AssistantMessageContent with correct type='output_text'
                        yield AssistantMessageContentPartAdded(
                            content_index=0,
                            content=AssistantMessageContent(text=""),
                        )
                        part_added = True

                    current_text += delta.content
                    yield AssistantMessageContentPartTextDelta(
                        content_index=0,
                        delta=delta.content,
                    )

                # Accumulate tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "name": "",
                                "arguments": "",
                            }
                        if tool_call.function:
                            if tool_call.function.name:
                                accumulated_tool_calls[idx]["name"] = tool_call.function.name
                            if tool_call.function.arguments:
                                accumulated_tool_calls[idx]["arguments"] += tool_call.function.arguments

            # Execute accumulated tool calls
            for idx, tool_data in accumulated_tool_calls.items():
                tool_name = tool_data["name"]
                tool_args_str = tool_data["arguments"]

                try:
                    tool_args = json.loads(tool_args_str) if tool_args_str else {}
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute the tool
                if tool_name in self._tool_handlers:
                    try:
                        result = await self._tool_handlers[tool_name](context, **tool_args)
                        tool_result_text = f"\n\n**{tool_name}:** {json.dumps(result)}"
                    except Exception as e:
                        logger.exception(f"Tool {tool_name} failed")
                        tool_result_text = f"\n\n**{tool_name}:** Error - {str(e)}"

                    if not part_added:
                        yield AssistantMessageContentPartAdded(
                            content_index=0,
                            content=AssistantMessageContent(text=""),
                        )
                        part_added = True

                    current_text += tool_result_text
                    yield AssistantMessageContentPartTextDelta(
                        content_index=0,
                        delta=tool_result_text,
                    )

            # Complete the text part
            if current_text and part_added:
                yield AssistantMessageContentPartDone(
                    content_index=0,
                    content=AssistantMessageContent(text=current_text),
                )

            # Complete the message
            final_text = current_text or "I'm not sure how to help with that."
            yield ThreadItemDoneEvent(
                item=AssistantMessageItem(
                    id=msg_id,
                    thread_id=thread.id,
                    created_at=created_at,
                    content=[AssistantMessageContent(text=final_text)],
                )
            )

        except Exception as e:
            logger.exception("Error generating response")
            # Yield error message
            error_msg_id = default_generate_id("message")
            error_created_at = datetime.now(UTC)

            error_item = AssistantMessageItem(
                id=error_msg_id,
                thread_id=thread.id,
                created_at=error_created_at,
                content=[AssistantMessageContent(text=f"I apologize, but I encountered an error: {str(e)}")],
            )
            yield ThreadItemAddedEvent(item=error_item)
            yield ThreadItemDoneEvent(item=error_item)
