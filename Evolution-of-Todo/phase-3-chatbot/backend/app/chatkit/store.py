"""ChatKit Store implementation using SQLModel/SQLAlchemy.

This module provides a Store implementation that persists ChatKit threads
and messages to our PostgreSQL database via SQLModel.
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid5

from chatkit.store import NotFoundError, Store
from chatkit.types import (
    ActiveStatus,
    Page,
    ThreadItem,
    ThreadMetadata,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation

# Namespace for generating deterministic UUIDs from ChatKit string IDs
CHATKIT_NAMESPACE = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def string_to_uuid(string_id: str) -> UUID:
    """Convert a string ID to a deterministic UUID.

    If the string is already a valid UUID, parse it directly.
    Otherwise, generate a UUID v5 from the string using our namespace.
    """
    try:
        # Try to parse as UUID directly
        return UUID(string_id)
    except (ValueError, AttributeError):
        # Generate deterministic UUID from string
        return uuid5(CHATKIT_NAMESPACE, string_id)


def serialize_for_json(obj: Any) -> Any:
    """Recursively convert an object to JSON-serializable format.

    Handles datetime objects, UUIDs, and nested structures.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, "model_dump"):
        return serialize_for_json(obj.model_dump())
    else:
        return obj


class ChatContext:
    """Context object passed through ChatKit operations."""

    def __init__(self, user_id: UUID, db: AsyncSession):
        self.user_id = user_id
        self.db = db


class DatabaseStore(Store[ChatContext]):
    """ChatKit Store backed by our PostgreSQL database."""

    async def load_thread(self, thread_id: str, context: ChatContext) -> ThreadMetadata:
        """Load a thread's metadata by id."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError(f"Thread {thread_id} not found")

        return ThreadMetadata(
            id=str(conversation.id),
            title=conversation.title or "New Chat",
            status=ActiveStatus(),
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )

    async def save_thread(self, thread: ThreadMetadata, context: ChatContext) -> None:
        """Persist thread metadata."""
        from sqlmodel import select

        # Convert string ID to UUID for database operations
        db_id = string_to_uuid(thread.id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if conversation:
            conversation.title = thread.title
            context.db.add(conversation)
        else:
            # Create new conversation with converted UUID
            conversation = Conversation(
                id=db_id,
                user_id=context.user_id,
                title=thread.title,
                messages=[],
            )
            context.db.add(conversation)

        await context.db.commit()

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: str,
        context: ChatContext,
    ) -> Page[ThreadItem]:
        """Load a page of thread items."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return Page(data=[], has_more=False)

        # Convert stored messages to ThreadItems
        items: list[ThreadItem] = []
        messages = conversation.messages or []

        for msg in messages:
            # Messages are stored as dicts with role and content
            if isinstance(msg, dict):
                items.append(msg)

        # Handle pagination
        if after:
            # Find index of 'after' item and slice
            for i, item in enumerate(items):
                if item.get("id") == after:
                    items = items[i + 1 :]
                    break

        if order == "desc":
            items = list(reversed(items))

        has_more = len(items) > limit
        items = items[:limit]

        return Page(data=items, has_more=has_more)

    async def load_threads(
        self,
        after: str | None,
        limit: int,
        order: str,
        context: ChatContext,
    ) -> Page[ThreadMetadata]:
        """Load a page of threads for the user."""
        from sqlmodel import select

        # Determine ordering based on 'order' parameter
        if order == "asc":
            order_clause = Conversation.updated_at.asc()
        else:
            order_clause = Conversation.updated_at.desc()

        statement = (
            select(Conversation)
            .where(Conversation.user_id == context.user_id)
            .order_by(order_clause)
            .limit(limit + 1)
        )

        if after:
            # TODO: Implement proper cursor pagination
            pass

        result = await context.db.execute(statement)
        conversations = result.scalars().all()

        has_more = len(conversations) > limit
        conversations = list(conversations)[:limit]

        threads = [
            ThreadMetadata(
                id=str(conv.id),
                title=conv.title or "New Chat",
                status=ActiveStatus(),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in conversations
        ]

        return Page(data=threads, has_more=has_more)

    async def add_thread_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: ChatContext,
    ) -> None:
        """Add an item to a thread."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError(f"Thread {thread_id} not found")

        messages = conversation.messages or []
        # Convert Pydantic model to dict and serialize datetime/UUID objects
        item_dict = serialize_for_json(item)
        messages.append(item_dict)
        conversation.messages = messages
        context.db.add(conversation)
        await context.db.commit()

    async def save_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: ChatContext,
    ) -> None:
        """Update an existing item in a thread."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError(f"Thread {thread_id} not found")

        messages = conversation.messages or []
        item_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)

        for i, msg in enumerate(messages):
            msg_id = msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None)
            if msg_id == item_id:
                # Serialize to handle datetime/UUID objects
                messages[i] = serialize_for_json(item)
                break

        conversation.messages = messages
        context.db.add(conversation)
        await context.db.commit()

    async def load_item(
        self,
        thread_id: str,
        item_id: str,
        context: ChatContext,
    ) -> ThreadItem:
        """Load a single item from a thread."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise NotFoundError(f"Thread {thread_id} not found")

        for msg in conversation.messages or []:
            msg_id = msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None)
            if msg_id == item_id:
                return msg

        raise NotFoundError(f"Item {item_id} not found")

    async def delete_thread(self, thread_id: str, context: ChatContext) -> None:
        """Delete a thread."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if conversation:
            await context.db.delete(conversation)
            await context.db.commit()

    async def delete_thread_item(
        self,
        thread_id: str,
        item_id: str,
        context: ChatContext,
    ) -> None:
        """Delete an item from a thread."""
        from sqlmodel import select

        # Convert string ID to UUID for database query
        db_id = string_to_uuid(thread_id)

        statement = select(Conversation).where(
            Conversation.id == db_id,
            Conversation.user_id == context.user_id,
        )
        result = await context.db.execute(statement)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return

        messages = conversation.messages or []
        messages = [
            msg
            for msg in messages
            if (msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None))
            != item_id
        ]
        conversation.messages = messages
        context.db.add(conversation)
        await context.db.commit()

    async def load_attachment(
        self, attachment_id: str, context: ChatContext
    ) -> bytes:
        """Load attachment data. Not implemented for this store."""
        raise NotImplementedError("Attachments not supported")

    async def save_attachment(
        self, attachment_id: str, data: bytes, context: ChatContext
    ) -> None:
        """Save attachment data. Not implemented for this store."""
        raise NotImplementedError("Attachments not supported")

    async def delete_attachment(
        self, attachment_id: str, context: ChatContext
    ) -> None:
        """Delete an attachment. Not implemented for this store."""
        raise NotImplementedError("Attachments not supported")
