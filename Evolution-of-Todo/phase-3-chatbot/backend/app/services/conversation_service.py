"""Conversation service for AI chatbot history management.

Provides business logic for:
- Creating, reading, updating, and deleting conversations
- Adding messages to conversations
- Multi-tenancy enforcement (user isolation)
- Conversation retrieval for AI context
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.conversation import Conversation


def utc_now() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(UTC)


class ConversationNotFoundError(Exception):
    """Raised when a conversation is not found or does not belong to the user."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize exception.

        Args:
            conversation_id: ID of the conversation that was not found.
        """
        self.conversation_id = conversation_id
        super().__init__(f"Conversation {conversation_id} not found")


class ConversationService:
    """Service for conversation CRUD operations with multi-tenancy.

    All operations are scoped to a specific user_id to enforce
    data isolation between users.

    Attributes:
        session: Async database session for queries.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize ConversationService with database session.

        Args:
            session: Async database session.
        """
        self.session = session

    async def get_or_create_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID | None = None,
    ) -> Conversation:
        """Get an existing conversation or create a new one.

        If conversation_id is provided, retrieve the conversation belonging to
        the user. If not found or conversation_id is None, create a new conversation.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: Optional UUID of an existing conversation.

        Returns:
            Conversation: Retrieved or newly created conversation instance.
        """
        if conversation_id:
            conversation = await self.get_conversation(user_id, conversation_id)
            if conversation:
                return conversation

        # Create new conversation
        conversation = Conversation(user_id=user_id)
        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> Conversation | None:
        """Get a specific conversation by ID for a user.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: UUID of the conversation to retrieve.

        Returns:
            Conversation | None: Conversation instance if found and owned by user,
                None otherwise.
        """
        statement = select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_conversations(self, user_id: UUID) -> list[Conversation]:
        """List all conversations for a user.

        Args:
            user_id: UUID of the conversation owner.

        Returns:
            list[Conversation]: List of conversations belonging to the user,
                ordered by most recently updated first.
        """
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def add_message(
        self,
        user_id: UUID,
        conversation_id: UUID,
        role: str,
        content: str,
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> Conversation:
        """Add a message to a conversation.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: UUID of the conversation to update.
            role: Message role (user/assistant/system).
            content: Message content text.
            tool_calls: Optional list of tool calls made by the assistant.

        Returns:
            Conversation: Updated conversation instance.

        Raises:
            ConversationNotFoundError: If conversation does not exist or
                does not belong to the user.
        """
        conversation = await self.get_conversation(user_id, conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        # Create message object
        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "timestamp": utc_now().isoformat(),
        }
        if tool_calls:
            message["tool_calls"] = tool_calls

        # Add message to conversation
        conversation.messages.append(message)
        conversation.updated_at = utc_now()

        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def update_messages(
        self,
        user_id: UUID,
        conversation_id: UUID,
        messages: list[dict[str, Any]],
    ) -> Conversation:
        """Replace the entire messages list for a conversation.

        Use this when you need to update the full conversation state,
        such as when the AI processes multiple messages at once.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: UUID of the conversation to update.
            messages: New list of messages to set.

        Returns:
            Conversation: Updated conversation instance.

        Raises:
            ConversationNotFoundError: If conversation does not exist or
                does not belong to the user.
        """
        conversation = await self.get_conversation(user_id, conversation_id)
        if not conversation:
            raise ConversationNotFoundError(conversation_id)

        conversation.messages = messages
        conversation.updated_at = utc_now()

        self.session.add(conversation)
        await self.session.flush()
        await self.session.refresh(conversation)
        return conversation

    async def delete_conversation(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> bool:
        """Delete a conversation.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: UUID of the conversation to delete.

        Returns:
            bool: True if conversation was deleted, False if not found.
        """
        conversation = await self.get_conversation(user_id, conversation_id)
        if not conversation:
            return False

        await self.session.delete(conversation)
        await self.session.flush()
        return True

    async def get_conversation_messages(
        self,
        user_id: UUID,
        conversation_id: UUID,
    ) -> list[dict[str, Any]] | None:
        """Get only the messages from a conversation.

        This is a convenience method for retrieving just the message list
        when building the AI context.

        Args:
            user_id: UUID of the conversation owner.
            conversation_id: UUID of the conversation.

        Returns:
            list[dict[str, Any]] | None: List of messages if conversation exists,
                None otherwise.
        """
        conversation = await self.get_conversation(user_id, conversation_id)
        return conversation.messages if conversation else None
