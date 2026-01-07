"""Chat API endpoint for AI chatbot integration.

Provides the main chat interface for the AI assistant to interact with users.
Handles conversation persistence and agent invocation with authentication.

Dependencies:
- Layer 2: MCP Server (for tool definitions)
- Layer 3: AI Engine (for agent execution)

User Stories:
- US-301: Add Task via Chat
- US-302: List Tasks via Chat
- US-303: Complete Task via Chat
- US-304: Update Task via Chat
- US-305: Delete Task via Chat
- US-306: Conversation Persistence
"""

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, SessionDep
from app.models.conversation import Conversation
from app.models.user import User

# Try to import Layer 3 dependencies - these will be available after
# T-314, T-315, T-316 are completed
try:
    from app.agent.chat_agent import run_agent
    AGENT_AVAILABLE = True
except ImportError:
    # Agent not yet implemented - will use placeholder
    AGENT_AVAILABLE = False

from app.services.conversation_service import ConversationService

# ============================================================================
# Request/Response Schemas
# ============================================================================


class ChatRequest(BaseModel):
    """Request model for chat endpoint.

    Attributes:
        conversation_id: Optional existing conversation ID to continue a chat.
        message: User's message content to the AI assistant.
    """

    conversation_id: str | None = Field(
        None,
        description="Existing conversation ID to continue the chat session",
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message content (1-5000 characters)",
    )


class ToolCall(BaseModel):
    """Represents a tool call made by the AI agent.

    Attributes:
        name: Name of the tool that was called.
        arguments: Dictionary of arguments passed to the tool.
        result: Optional result returned by the tool.
    """

    name: str = Field(..., description="Name of the tool called")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")
    result: Any = Field(None, description="Optional result from tool execution")


class ChatResponse(BaseModel):
    """Response model for chat endpoint.

    Attributes:
        conversation_id: Unique identifier for the conversation session.
        response: The AI assistant's response to the user's message.
        tool_calls: List of tools called during message processing.
    """

    conversation_id: str = Field(..., description="Conversation session identifier")
    response: str = Field(..., description="AI assistant's response")
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of tool calls made by the agent",
    )


# ============================================================================
# Router
# ============================================================================

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with AI Assistant",
    description="Send a message to the AI assistant and receive a response. "
    "Supports conversation continuation via conversation_id.",
)
async def chat(
    request: ChatRequest,
    current_user: CurrentUser,
    session: SessionDep,
) -> ChatResponse:
    """Process a chat message from the authenticated user.

    This endpoint:
    1. Retrieves or creates a conversation for the user
    2. Invokes the AI agent with the message and conversation context
    3. Persists the conversation history including tool calls
    4. Returns the assistant's response

    Args:
        request: Chat request with message and optional conversation_id.
        current_user: Authenticated user from JWT token.
        session: Database session for conversation persistence.

    Returns:
        ChatResponse: Assistant's response with conversation metadata.

    Raises:
        HTTPException: 500 Internal Server Error if agent execution fails.
    """
    conversation_service = ConversationService(session)

    # Step 1: Get or create conversation (T-308, T-317)
    conversation_id = (
        UUID(request.conversation_id) if request.conversation_id else None
    )
    conversation = await conversation_service.get_or_create_conversation(
        user_id=current_user.id,
        conversation_id=conversation_id,
    )

    # Step 2: Add user message to conversation (US-306)
    await conversation_service.add_message(
        user_id=current_user.id,
        conversation_id=conversation.id,
        role="user",
        content=request.message,
    )

    # Step 3: Run agent with conversation context (T-319)
    if AGENT_AVAILABLE:
        try:
            result = await run_agent(
                user_id=current_user.id,
                conversation=conversation,
                message=request.message,
                session=session,
            )
            response_text = result.response
            tool_calls = result.tool_calls
        except Exception as e:
            # Log error but return a helpful response
            response_text = f"I encountered an error while processing your request: {e}"
            tool_calls = []
    else:
        # Placeholder response when agent is not yet available
        response_text = (
            "AI agent integration pending. "
            "Please complete Layer 3 tasks (T-314, T-315, T-316) first."
        )
        tool_calls = []

    # Step 4: Add assistant response to conversation
    await conversation_service.add_message(
        user_id=current_user.id,
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        tool_calls=tool_calls,
    )

    # Commit all changes
    await session.commit()

    return ChatResponse(
        conversation_id=str(conversation.id),
        response=response_text,
        tool_calls=tool_calls,
    )
