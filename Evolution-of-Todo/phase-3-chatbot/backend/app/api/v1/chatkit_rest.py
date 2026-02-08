"""ChatKit REST Wrapper Layer.

Translates REST API requests into ChatKit JSON-RPC protocol.
Resolves Phase 3 HTTP 500 blocker by providing REST endpoints for tests/frontend
while maintaining ChatKit SDK compatibility.

Architecture:
- REST endpoints: POST /chatkit/sessions, /sessions/{id}/threads, etc.
- JSON-RPC translation: Convert REST -> ChatKit protocol
- SSE streaming: Passthrough for message responses
- User-scoped: JWT authentication, user_id validation

Spec: specs/features/chatkit-rest-wrapper/spec.md
Tasks: specs/features/chatkit-rest-wrapper/tasks.md
Phase: Phase 2 (T006-T011) - REQ-001 Create Session
Phase: Phase 3 (T012-T016) - REQ-002 Create Thread
Phase: Phase 4 (T017-T023) - REQ-003 Send Message & Stream
Phase: Phase 5 (T024-T027) - REQ-004 List Sessions
Phase: Phase 6 (T028-T031) - REQ-005 Get Session History
"""

import json
import logging
from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from chatkit.store import default_generate_id
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.api.deps import get_current_user
from app.chatkit.store import ChatContext, string_to_uuid
from app.core.database import get_session
from app.core.rate_limit import limiter
from app.models.conversation import Conversation
from app.models.user import User

logger = logging.getLogger(__name__)

# Router for ChatKit REST wrapper endpoints
# Will be registered in app/api/v1/router.py with prefix "/chatkit" in Phase 8 (T036)
router = APIRouter(tags=["chatkit-rest"])


# ---------------------------------------------------------------------------
# T006 [REQ-001] [CRITICAL] - Pydantic Models
# Spec: REQ-001 output format (spec.md lines 86-96)
# AC: AC-001 (spec.md lines 560-567)
# ---------------------------------------------------------------------------

class SessionData(BaseModel):
    """Session creation response data.

    Attributes:
        id: Unique session UUID.
        user_id: Owner user UUID.
        created_at: Session creation timestamp (UTC).
    """

    model_config = ConfigDict(strict=True)

    id: UUID = Field(description="Session UUID")
    user_id: UUID = Field(description="Owner user UUID")
    created_at: datetime = Field(
        description="Session creation timestamp (UTC)"
    )


class SessionResponse(BaseModel):
    """Standard REST response wrapper for session operations.

    Follows spec format: {"success": true, "data": {...}}
    """

    model_config = ConfigDict(strict=True)

    success: bool = Field(default=True)
    data: SessionData


# ---------------------------------------------------------------------------
# T007-T011 [REQ-001] - Create Session Endpoint
# Spec: REQ-001 (spec.md lines 76-131)
# AC: AC-001 (spec.md lines 560-567)
# ---------------------------------------------------------------------------

@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def create_session(
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    """Create a new chat session via REST API.

    Translates REST request to ChatKit JSON-RPC protocol internally.
    Creates a Conversation record in the database and returns session metadata.

    **Authentication**: JWT required (Bearer token)
    **Rate Limit**: Max 10 active sessions per user

    **Returns**: Session ID, user ID, creation timestamp

    **Errors**:
    - 401: Authentication required (invalid/missing JWT)
    - 429: Session limit reached (user has 10 sessions)
    - 503: Database unavailable

    Spec: REQ-001 (spec.md lines 76-131)
    AC: AC-001 (spec.md lines 560-567)
    Task: T007
    """
    # ------------------------------------------------------------------
    # T008 [REQ-001] - Session Count Validation
    # Spec: REQ-001 preconditions (spec.md lines 98-100), edge case (lines 109-110)
    # ------------------------------------------------------------------
    try:
        count_result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.user_id == current_user.id
            )
        )
        session_count: int = count_result.scalar_one()
    except Exception as exc:
        logger.error(
            "Database error counting sessions for user %s: %s",
            current_user.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable",
            },
        ) from exc

    if session_count >= 10:
        logger.info(
            "Session limit reached for user %s (count=%d)",
            current_user.id,
            session_count,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "SESSION_LIMIT",
                "message": (
                    "Maximum 10 sessions allowed. "
                    "Please delete an old session."
                ),
            },
        )

    # ------------------------------------------------------------------
    # T009 [REQ-001] - JSON-RPC Translation
    # Spec: REQ-001 translation logic (spec.md lines 113-130)
    # ------------------------------------------------------------------
    json_rpc_payload = {
        "type": "threads.create",
        "params": {
            "input": {
                "content": [
                    {"type": "input_text", "text": "Session initialized"}
                ]
            }
        },
    }
    logger.debug(
        "JSON-RPC translation for user %s: %s",
        current_user.id,
        json.dumps(json_rpc_payload),
    )

    # ------------------------------------------------------------------
    # T010 [REQ-001] - Delegate to ChatKitServer
    # Spec: REQ-001 translation logic (spec.md line 127),
    #        postconditions (lines 102-106)
    #
    # ARCHITECTURAL NOTE:
    # ChatKitServer.process() for threads.create is a STREAMING operation
    # that triggers the full AI response flow (OpenRouter call). For REST
    # session creation, we bypass the streaming path and create the
    # Conversation record directly in the database. This matches the
    # DatabaseStore.save_thread() behavior but avoids the expensive AI call.
    # The JSON-RPC payload is logged for traceability but not sent to the
    # ChatKit server for this endpoint.
    # ------------------------------------------------------------------
    try:
        # Generate a thread ID using ChatKit's ID generator (consistent
        # with how ChatKit would generate one internally)
        thread_id_str: str = default_generate_id("thread")
        db_uuid: UUID = string_to_uuid(thread_id_str)

        # Create the Conversation record directly
        conversation = Conversation(
            id=db_uuid,
            user_id=current_user.id,
            title="New Chat",
            messages=[],
        )
        db.add(conversation)
        await db.flush()
        # Refresh to get server-generated defaults (created_at, updated_at)
        await db.refresh(conversation)
    except Exception as exc:
        logger.error(
            "ChatKit session creation failed for user %s: %s",
            current_user.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": f"ChatKit initialization failed: {exc}",
            },
        ) from exc

    logger.info(
        "Session created: id=%s, user_id=%s",
        conversation.id,
        conversation.user_id,
    )

    # ------------------------------------------------------------------
    # T011 [REQ-001] - Format REST Response
    # Spec: REQ-001 output (spec.md lines 86-96)
    # ------------------------------------------------------------------
    return SessionResponse(
        success=True,
        data=SessionData(
            id=conversation.id,
            user_id=conversation.user_id,
            created_at=conversation.created_at,
        ),
    )


# ---------------------------------------------------------------------------
# T012 [REQ-002] - Pydantic Models for Thread Creation
# Spec: REQ-002 output format (spec.md lines 144-151)
# AC: AC-002 (spec.md lines 569-575)
# ---------------------------------------------------------------------------


class ThreadData(BaseModel):
    """Thread creation response data.

    For ChatKit SDK, threads map 1:1 with sessions (thread_id == session_id).

    Attributes:
        id: Thread UUID (same as session ID for ChatKit).
        session_id: Parent session UUID.
        created_at: Thread creation timestamp (UTC).
    """

    model_config = ConfigDict(strict=True)

    id: UUID = Field(description="Thread UUID (same as session ID for ChatKit)")
    session_id: UUID = Field(description="Parent session UUID")
    created_at: datetime = Field(
        description="Thread creation timestamp (UTC)"
    )


class ThreadResponse(BaseModel):
    """Standard REST response wrapper for thread creation.

    Follows spec format: {"success": true, "data": {...}}
    """

    model_config = ConfigDict(strict=True)

    success: bool = Field(default=True)
    data: ThreadData


# ---------------------------------------------------------------------------
# T013-T016 [REQ-002] - Create Thread Endpoint
# Spec: REQ-002 (spec.md lines 134-192)
# AC: AC-002 (spec.md lines 569-575)
# ---------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/threads",
    response_model=ThreadResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def create_thread(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ThreadResponse:
    """Create a thread within an existing session.

    For ChatKit SDK, threads map 1:1 with sessions (thread_id == session_id).
    This endpoint is idempotent - calling it multiple times returns the same
    thread ID.

    **Authentication**: JWT required (Bearer token)
    **Authorization**: User must own the session

    **Returns**: Thread ID (same as session ID), session ID, creation timestamp

    **Errors**:
    - 401: Authentication required (invalid/missing JWT)
    - 403: Forbidden (session belongs to different user)
    - 404: Session not found
    - 503: Database unavailable

    Spec: REQ-002 (spec.md lines 134-192)
    AC: AC-002 (spec.md lines 569-575)
    Task: T013
    """
    # ------------------------------------------------------------------
    # T014 [REQ-002] - Validate Session Ownership
    # Spec: REQ-002 preconditions (spec.md lines 153-156),
    #        edge cases (lines 160-165)
    # ------------------------------------------------------------------
    logger.info(
        "Thread creation request for session %s by user %s",
        session_id,
        current_user.id,
    )

    try:
        # Query session with user_id filter for authorization
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == session_id,
                Conversation.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

        if session is None:
            # Check if session exists at all (for correct error code)
            result_exists = await db.execute(
                select(Conversation).where(Conversation.id == session_id)
            )
            if result_exists.scalar_one_or_none() is not None:
                # Session exists but belongs to a different user
                logger.warning(
                    "User %s attempted to access session %s "
                    "owned by different user",
                    current_user.id,
                    session_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": "You do not have access to this session",
                    },
                )
            else:
                # Session does not exist
                logger.warning("Session %s not found", session_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "SESSION_NOT_FOUND",
                        "message": f"Session {session_id} not found",
                    },
                )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as exc:
        logger.error(
            "Database error during session validation: %s",
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable",
            },
        ) from exc

    # ------------------------------------------------------------------
    # T015 [REQ-002] - Idempotent Thread Creation
    # Spec: REQ-002 translation logic (spec.md lines 171-189)
    #
    # ARCHITECTURAL NOTE:
    # For ChatKit SDK, threads map 1:1 with sessions. The thread ID is
    # always the same as the session ID. This endpoint is idempotent by
    # design - calling it multiple times returns the same thread ID
    # without creating any additional database records.
    # ------------------------------------------------------------------
    thread_id = session_id  # ChatKit 1:1 mapping: thread_id == session_id

    logger.debug(
        "Thread ID for session %s: %s "
        "(ChatKit 1:1 mapping: thread_id == session_id)",
        session_id,
        thread_id,
    )

    # ------------------------------------------------------------------
    # T016 [REQ-002] - Format REST Response
    # Spec: REQ-002 output (spec.md lines 144-151)
    # ------------------------------------------------------------------
    logger.info(
        "Thread %s returned for session %s (user: %s)",
        thread_id,
        session_id,
        current_user.id,
    )

    return ThreadResponse(
        success=True,
        data=ThreadData(
            id=thread_id,
            session_id=session_id,
            created_at=session.created_at,
        ),
    )


# ============================================================================
# Phase 4: REQ-003 - Send Message & Stream (T017-T023)
# Spec: REQ-003 (spec.md lines 194-294)
# AC: AC-003 (spec.md lines 577-585)
# ============================================================================


# ---------------------------------------------------------------------------
# T017 [REQ-003] [CRITICAL] - Pydantic Models
# Spec: REQ-003 input format (spec.md lines 196-221), data models (lines 430-451)
# ---------------------------------------------------------------------------


class InputTextContent(BaseModel):
    """Text content input for user message.

    Attributes:
        type: Content type discriminator, always "input_text".
        text: User message text (1-500 chars).
    """

    model_config = ConfigDict(strict=True)

    type: Literal["input_text"] = Field(default="input_text")
    text: str = Field(
        min_length=1,
        description="User message text (1-500 chars)",
    )


class UserMessage(BaseModel):
    """User message wrapper.

    Attributes:
        role: Message sender role, always "user".
        content: List of content parts (at least one required).
    """

    model_config = ConfigDict(strict=True)

    role: Literal["user"] = Field(default="user")
    content: list[InputTextContent] = Field(
        min_length=1,
        description="Message content parts",
    )


class SendMessageRequest(BaseModel):
    """Request body for sending a message.

    Attributes:
        message: User message to send to the AI assistant.
    """

    model_config = ConfigDict(strict=True)

    message: UserMessage = Field(description="User message to send")


# ---------------------------------------------------------------------------
# T018-T023 [REQ-003] - Send Message & Stream Endpoint
# Spec: REQ-003 (spec.md lines 194-294)
# AC: AC-003 (spec.md lines 577-585)
# ---------------------------------------------------------------------------


@router.post(
    "/sessions/{session_id}/threads/{thread_id}/runs",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def send_message(
    request: Request,
    session_id: UUID,
    thread_id: UUID,
    request_body: SendMessageRequest,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Send a message to an AI assistant and stream the response via SSE.

    This endpoint:
    1. Validates session and thread exist and belong to the user
    2. Translates REST request to ChatKit JSON-RPC format
    3. Calls ChatKitServer.process() to get AI response stream
    4. Passes through SSE events to the client
    5. Handles tool calls (e.g., task creation via MCP)

    **Authentication**: JWT required (Bearer token)
    **Authorization**: User must own the session

    **Returns**: Server-Sent Events (SSE) stream with AI response deltas

    **SSE Format**::

        data: {"type": "thread.item.content.part.delta", "delta": "Hello"}
        data: {"type": "thread.item.content.part.delta", "delta": " world"}
        data: [DONE]

    **Errors**:
    - 400: Empty message or message >500 chars
    - 401: Authentication required (invalid/missing JWT)
    - 403: Forbidden (session belongs to different user)
    - 404: Session or thread not found
    - 502: OpenRouter error

    Spec: REQ-003 (spec.md lines 194-294)
    AC: AC-003 (spec.md lines 577-585)
    Task: T018
    """
    # ------------------------------------------------------------------
    # T019 [REQ-003] - Validate Session/Thread Ownership
    # Spec: REQ-003 preconditions (spec.md lines 223-227),
    #        edge cases (lines 260-268)
    # ------------------------------------------------------------------
    logger.info(
        "Send message request: session=%s, thread=%s, user=%s, "
        "message_length=%d",
        session_id,
        thread_id,
        current_user.id,
        len(request_body.message.content[0].text),
    )

    # ------------------------------------------------------------------
    # AC-003 criterion 6: Message >500 chars must return HTTP 400
    # (not Pydantic's default 422). We removed max_length from the model
    # and validate explicitly here to control the status code and format.
    # ------------------------------------------------------------------
    raw_text = request_body.message.content[0].text
    if len(raw_text) > 500:
        logger.warning(
            "Message too long (%d chars) rejected for session %s",
            len(raw_text),
            session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "MESSAGE_TOO_LONG",
                "message": (
                    f"Message exceeds 500 character limit "
                    f"(received {len(raw_text)})"
                ),
            },
        )

    # Validate message is not empty after stripping whitespace
    # (Pydantic min_length=1 catches truly empty strings, but whitespace-only
    # strings need an explicit check)
    message_text = raw_text.strip()
    if not message_text:
        logger.warning(
            "Empty message (whitespace only) rejected for session %s",
            session_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMPTY_MESSAGE",
                "message": "Message text cannot be empty",
            },
        )

    try:
        # Query session with user_id filter for authorization
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == session_id,
                Conversation.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

        if session is None:
            # Check if session exists at all (for better error message)
            result_exists = await db.execute(
                select(Conversation).where(Conversation.id == session_id)
            )
            if result_exists.scalar_one_or_none() is not None:
                # Session exists but belongs to different user
                logger.warning(
                    "User %s attempted to access session %s "
                    "owned by different user",
                    current_user.id,
                    session_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": "You do not have access to this session",
                    },
                )
            else:
                # Session does not exist
                logger.warning("Session %s not found", session_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "SESSION_NOT_FOUND",
                        "message": f"Session {session_id} not found",
                    },
                )

        # Validate thread_id matches session_id (ChatKit 1:1 mapping)
        if thread_id != session_id:
            logger.warning(
                "Thread ID %s does not match session ID %s "
                "(ChatKit 1:1 mapping violation)",
                thread_id,
                session_id,
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "THREAD_NOT_FOUND",
                    "message": (
                        f"Thread {thread_id} not found "
                        "(must match session ID)"
                    ),
                },
            )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as exc:
        logger.error(
            "Database error during session validation: %s",
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable",
            },
        ) from exc

    # ------------------------------------------------------------------
    # T020 [REQ-003] - Translate REST Request to JSON-RPC
    # Spec: REQ-003 translation logic (spec.md lines 239-255)
    # ------------------------------------------------------------------
    jsonrpc_payload = {
        "type": "threads.add_user_message",
        "params": {
            "thread_id": str(thread_id),
            "input": {
                "content": [
                    {
                        "type": "input_text",
                        "text": message_text,
                    }
                ],
                "attachments": [],
                "inference_options": {
                    "tool_choice": None,
                    "model": None,
                },
            },
        },
    }

    logger.debug(
        "JSON-RPC params for ChatKit: thread_id=%s, "
        "message_text_preview=%.50s...",
        thread_id,
        message_text,
    )

    # ------------------------------------------------------------------
    # T021 [REQ-003] - Call ChatKitServer.process()
    # Spec: REQ-003 translation logic (spec.md lines 244-252)
    #
    # ARCHITECTURAL NOTE:
    # We import the server instance from chatkit.py (which has all tool
    # handlers registered) rather than creating a new instance. This
    # ensures tool calls (add_task, list_tasks, etc.) work correctly.
    # ------------------------------------------------------------------
    try:
        from app.api.v1.chatkit import server as chatkit_server

        chat_context = ChatContext(user_id=current_user.id, db=db)

        # DEBUG: Log the exact payload being sent to ChatKit SDK
        payload_json = json.dumps(jsonrpc_payload)
        logger.info(
            "DEBUG: Sending to ChatKit SDK: %s",
            payload_json,
        )

        # Process the message through ChatKit SDK
        # server.process() expects JSON bytes and returns StreamingResult
        streaming_result = await chatkit_server.process(
            payload_json.encode("utf-8"),
            chat_context,
        )

        # Verify we got a streaming result (ThreadsAddUserMessageReq
        # is a streaming request type in ChatKit SDK)
        if not hasattr(streaming_result, "__aiter__"):
            logger.error(
                "ChatKit SDK returned non-streaming result for thread %s",
                thread_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "INTERNAL_ERROR",
                    "message": "Expected streaming response from ChatKit SDK",
                },
            )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as exc:
        logger.error(
            "ChatKit SDK error for thread %s: %s",
            thread_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "code": "OPENROUTER_ERROR",
                "message": f"AI service error: {exc}",
            },
        ) from exc

    # ------------------------------------------------------------------
    # T022 [REQ-003] - Implement SSE Passthrough
    # Spec: REQ-003 output (spec.md lines 203-221)
    # ------------------------------------------------------------------
    async def event_generator():
        """Generator that yields SSE events from ChatKit SDK.

        The ChatKit SDK's StreamingResult already yields bytes in SSE
        format: ``b"data: {json}\\n\\n"``. We decode and pass through.

        After the stream completes, we send a ``data: [DONE]`` sentinel
        so the client knows to close the connection.
        """
        try:
            async for event in streaming_result:
                # StreamingResult yields bytes already SSE-formatted
                if isinstance(event, bytes):
                    yield event.decode("utf-8")
                else:
                    yield str(event)

            # Send termination signal
            yield "data: [DONE]\n\n"

            logger.info(
                "SSE stream completed for session %s, thread %s",
                session_id,
                thread_id,
            )

        except Exception as exc:
            logger.error(
                "Error during SSE streaming for thread %s: %s",
                thread_id,
                exc,
                exc_info=True,
            )
            # Send error event before closing
            error_event = json.dumps(
                {
                    "type": "error",
                    "error": {
                        "code": "STREAMING_ERROR",
                        "message": "Stream interrupted",
                    },
                }
            )
            yield f"data: {error_event}\n\n"
            yield "data: [DONE]\n\n"

    # ------------------------------------------------------------------
    # T023 [REQ-003] - Return StreamingResponse
    # Spec: REQ-003 output headers (spec.md lines 209-221)
    # ------------------------------------------------------------------
    logger.info(
        "Starting SSE stream for session %s, thread %s, user %s",
        session_id,
        thread_id,
        current_user.id,
    )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================================================
# Phase 5: REQ-004 - List Sessions (T024-T027)
# Spec: REQ-004 (spec.md lines 259-306)
# AC: AC-004 (spec.md lines 585-589)
# ============================================================================


# ---------------------------------------------------------------------------
# T024 [P] [REQ-004] - Pydantic Models
# Spec: REQ-004 output format (spec.md lines 268-288)
# ---------------------------------------------------------------------------


class SessionListItem(BaseModel):
    """Session item in list response.

    Attributes:
        id: Unique session UUID.
        user_id: Owner user UUID.
        title: Session title for display.
        created_at: Session creation timestamp (UTC).
        updated_at: Last update timestamp (UTC).
        message_count: Number of messages in session.
    """

    model_config = ConfigDict(strict=True)

    id: UUID = Field(description="Session UUID")
    user_id: UUID = Field(description="Owner user UUID")
    title: str = Field(description="Session title")
    created_at: datetime = Field(
        description="Session creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        description="Last update timestamp (UTC)"
    )
    message_count: int = Field(
        description="Number of messages in session", ge=0
    )


class SessionListResponse(BaseModel):
    """Response wrapper for session list.

    Follows spec format: {"success": true, "data": [...], "meta": {"total": N}}
    """

    model_config = ConfigDict(strict=True)

    success: bool = Field(default=True)
    data: list[SessionListItem] = Field(description="Array of sessions")
    meta: dict[str, int] = Field(
        description="Metadata with total count",
        default_factory=lambda: {"total": 0},
    )


# ---------------------------------------------------------------------------
# T025-T027 [REQ-004] - List Sessions Endpoint
# Spec: REQ-004 (spec.md lines 259-306)
# AC: AC-004 (spec.md lines 585-589)
# ---------------------------------------------------------------------------


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def list_sessions(
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SessionListResponse:
    """List all sessions belonging to the authenticated user.

    Returns sessions ordered by updated_at DESC (newest first) with
    message counts.

    **Authentication**: JWT required (Bearer token)
    **Authorization**: Returns only sessions owned by the authenticated user

    **Returns**: Array of sessions with metadata

    **Response Format**::

        {
          "success": true,
          "data": [
            {
              "id": "uuid",
              "user_id": "uuid",
              "title": "Session title",
              "created_at": "2024-01-01T00:00:00Z",
              "updated_at": "2024-01-01T00:00:00Z",
              "message_count": 5
            }
          ],
          "meta": {"total": 1}
        }

    **Errors**:
    - 401: Authentication required (invalid/missing JWT)
    - 503: Database unavailable

    Spec: REQ-004 (spec.md lines 259-306)
    AC: AC-004 (spec.md lines 585-589)
    Task: T025
    """
    # ------------------------------------------------------------------
    # T026 [REQ-004] - Query Database
    # Spec: REQ-004 translation logic (spec.md lines 290-304)
    # ------------------------------------------------------------------
    logger.info("List sessions request for user %s", current_user.id)

    try:
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.updated_at.desc())
        )
        sessions = result.scalars().all()

        logger.debug(
            "Found %d sessions for user %s",
            len(sessions),
            current_user.id,
        )

    except Exception as exc:
        logger.error(
            "Database error listing sessions for user %s: %s",
            current_user.id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable",
            },
        ) from exc

    # ------------------------------------------------------------------
    # T027 [REQ-004] - Format Response
    # Spec: REQ-004 output (spec.md lines 268-288)
    # ------------------------------------------------------------------
    session_items = [
        SessionListItem(
            id=session.id,
            user_id=session.user_id,
            title=session.title if session.title is not None else "Untitled",
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=(
                len(session.messages) if session.messages else 0
            ),
        )
        for session in sessions
    ]

    logger.info(
        "Returning %d sessions for user %s (total messages: %d)",
        len(session_items),
        current_user.id,
        sum(item.message_count for item in session_items),
    )

    return SessionListResponse(
        success=True,
        data=session_items,
        meta={"total": len(session_items)},
    )


# ============================================================================
# Phase 6: REQ-005 - Get Session History (T028-T031)
# Spec: REQ-005 (spec.md lines 310-369)
# AC: AC-005 (spec.md lines 591-596)
# ============================================================================


# ---------------------------------------------------------------------------
# T028 [P] [REQ-005] [CRITICAL] - Pydantic Models
# Spec: REQ-005 output format (spec.md lines 319-345),
#        data models (lines 494-519)
# ---------------------------------------------------------------------------


class MessageContent(BaseModel):
    """Message content part.

    Represents a single content element within a message (e.g., text input,
    response text).

    Attributes:
        type: Content type discriminator (input_text, text, etc.).
        text: Content text value.
    """

    model_config = ConfigDict(strict=True)

    type: str = Field(description="Content type (input_text, text, etc.)")
    text: str = Field(description="Content text")


class ToolCall(BaseModel):
    """Tool call information for assistant messages.

    Represents a tool invocation made by the assistant during response
    generation (e.g., add_task, list_tasks).

    Attributes:
        id: Unique tool call identifier.
        type: Tool type (e.g., 'function').
        function: Function call details (name, arguments).
    """

    model_config = ConfigDict(strict=True)

    id: str = Field(description="Tool call ID")
    type: str = Field(description="Tool type (e.g., 'function')")
    function: dict[str, Any] = Field(description="Function call details")


class MessageDetail(BaseModel):
    """Single message in conversation history.

    Represents one message exchange in the session, including user inputs
    and assistant responses with optional tool calls.

    Attributes:
        role: Message sender role (user, assistant).
        content: Message content parts.
        tool_calls: Tool calls made by assistant (None if no tool calls).
        created_at: Message timestamp (UTC).
    """

    model_config = ConfigDict(strict=True)

    role: str = Field(description="Message role (user, assistant)")
    content: list[MessageContent] = Field(
        description="Message content parts"
    )
    tool_calls: list[ToolCall] | None = Field(
        default=None,
        description="Tool calls made by assistant (if any)",
    )
    created_at: datetime = Field(description="Message timestamp (UTC)")


class SessionDetailData(BaseModel):
    """Session detail with full message history.

    Contains session metadata and the complete ordered list of messages
    for displaying conversation history.

    Attributes:
        id: Session UUID.
        user_id: Owner user UUID.
        title: Session title for display.
        created_at: Session creation timestamp (UTC).
        updated_at: Last update timestamp (UTC).
        messages: Message history ordered by created_at ASC.
    """

    model_config = ConfigDict(strict=True)

    id: UUID = Field(description="Session UUID")
    user_id: UUID = Field(description="Owner user UUID")
    title: str = Field(description="Session title")
    created_at: datetime = Field(
        description="Session creation timestamp (UTC)"
    )
    updated_at: datetime = Field(
        description="Last update timestamp (UTC)"
    )
    messages: list[MessageDetail] = Field(
        description="Message history ordered by created_at ASC"
    )


class SessionDetailResponse(BaseModel):
    """Response wrapper for session detail.

    Follows spec format: {"success": true, "data": {...}}
    """

    model_config = ConfigDict(strict=True)

    success: bool = Field(default=True)
    data: SessionDetailData


# ---------------------------------------------------------------------------
# T029-T031 [P] [REQ-005] - Get Session History Endpoint
# Spec: REQ-005 (spec.md lines 310-369)
# AC: AC-005 (spec.md lines 591-596)
# ---------------------------------------------------------------------------


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def get_session_detail(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SessionDetailResponse:
    """Get a session with full message history.

    Returns session metadata and all messages ordered by created_at ASC
    (oldest first, chronological order).

    **Authentication**: JWT required (Bearer token)
    **Authorization**: User must own the session

    **Returns**: Session detail with messages array

    **Response Format**::

        {
          "success": true,
          "data": {
            "id": "uuid",
            "user_id": "uuid",
            "title": "Session title",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "messages": [
              {
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}],
                "tool_calls": null,
                "created_at": "2024-01-01T00:00:00Z"
              }
            ]
          }
        }

    **Errors**:
    - 401: Authentication required (invalid/missing JWT)
    - 403: Forbidden (session belongs to different user)
    - 404: Session not found
    - 503: Database unavailable

    Spec: REQ-005 (spec.md lines 310-369)
    AC: AC-005 (spec.md lines 591-596)
    Task: T029
    """
    # ------------------------------------------------------------------
    # T030 [REQ-005] - Query Database with User Authorization
    # Spec: REQ-005 preconditions (spec.md lines 348-350),
    #        edge cases (lines 355-358)
    # ------------------------------------------------------------------
    logger.info(
        "Get session request: session_id=%s, user=%s",
        session_id,
        current_user.id,
    )

    try:
        # Query session with user_id filter for authorization
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == session_id,
                Conversation.user_id == current_user.id,
            )
        )
        session = result.scalar_one_or_none()

        if session is None:
            # Check if session exists at all (for correct error code)
            result_exists = await db.execute(
                select(Conversation).where(Conversation.id == session_id)
            )
            if result_exists.scalar_one_or_none() is not None:
                # Session exists but belongs to a different user
                logger.warning(
                    "User %s attempted to access session %s "
                    "owned by different user",
                    current_user.id,
                    session_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": (
                            "You do not have access to this session"
                        ),
                    },
                )
            else:
                # Session does not exist
                logger.warning("Session %s not found", session_id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "SESSION_NOT_FOUND",
                        "message": f"Session {session_id} not found",
                    },
                )

    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except Exception as exc:
        logger.error(
            "Database error fetching session %s: %s",
            session_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable",
            },
        ) from exc

    # ------------------------------------------------------------------
    # T031 [REQ-005] - Format Response with Ordered Messages
    # Spec: REQ-005 output (spec.md lines 319-345)
    #
    # Messages are stored as a JSON column on the Conversation model.
    # Parse each message dict into a MessageDetail Pydantic model,
    # then sort by created_at ASC (oldest first, chronological order).
    # ------------------------------------------------------------------
    messages_raw: list[dict[str, Any]] = (
        session.messages if session.messages else []
    )

    # Convert raw JSON messages to MessageDetail objects
    message_details: list[MessageDetail] = []
    for msg in messages_raw:
        # Parse content parts
        content_parts = [
            MessageContent(
                type=part.get("type", "text"),
                text=part.get("text", ""),
            )
            for part in msg.get("content", [])
        ]

        # Parse tool_calls if present (for assistant messages)
        tool_calls: list[ToolCall] | None = None
        if msg.get("tool_calls"):
            tool_calls = [
                ToolCall(
                    id=tc.get("id", ""),
                    type=tc.get("type", "function"),
                    function=tc.get("function", {}),
                )
                for tc in msg["tool_calls"]
            ]

        # Parse created_at timestamp (fall back to session created_at)
        msg_created_at_raw = msg.get("created_at")
        if msg_created_at_raw:
            msg_created_at = datetime.fromisoformat(msg_created_at_raw)
        else:
            msg_created_at = session.created_at

        message_details.append(
            MessageDetail(
                role=msg.get("role", "user"),
                content=content_parts,
                tool_calls=tool_calls,
                created_at=msg_created_at,
            )
        )

    # Sort messages by created_at ASC (oldest first, chronological order)
    message_details.sort(key=lambda m: m.created_at)

    logger.info(
        "Returning session %s with %d messages for user %s",
        session_id,
        len(message_details),
        current_user.id,
    )

    return SessionDetailResponse(
        success=True,
        data=SessionDetailData(
            id=session.id,
            user_id=session.user_id,
            title=session.title if session.title is not None else "Untitled",
            created_at=session.created_at,
            updated_at=session.updated_at,
            messages=message_details,
        ),
    )


# ============================================================================
# Phase 7: REQ-006 - Delete Session (T032-T035)
# ============================================================================

class DeletedSessionData(BaseModel):
    """Data returned after successful deletion"""
    model_config = ConfigDict(strict=True)

    deleted: bool = Field(default=True, description="Deletion confirmation")
    session_id: UUID = Field(description="ID of deleted session")


class DeleteResponse(BaseModel):
    """Response wrapper for delete operations"""
    model_config = ConfigDict(strict=True)

    success: bool = Field(default=True)
    data: DeletedSessionData


@router.delete(
    "/sessions/{session_id}",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def delete_session(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DeleteResponse:
    """
    Delete a session and all its messages (CASCADE).

    **Authentication**: JWT required (Bearer token)
    **Authorization**: User must own the session

    **Returns**: Deletion confirmation with session ID

    **Errors**:
    - 401: Authentication required (invalid/missing JWT)
    - 403: Forbidden (session belongs to different user)
    - 404: Session not found
    - 503: Database unavailable

    Spec: REQ-006 (spec.md lines 371-419)
    AC: AC-006 (spec.md lines 598-603)
    """
    logger.info(
        f"Delete session request: session_id={session_id}, "
        f"user={current_user.id}"
    )

    try:
        # Query session with user_id filter for authorization
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == session_id,
                Conversation.user_id == current_user.id
            )
        )
        session = result.scalar_one_or_none()

        if session is None:
            # Check if session exists at all (for better error message)
            result_exists = await db.execute(
                select(Conversation).where(Conversation.id == session_id)
            )
            if result_exists.scalar_one_or_none() is not None:
                # Session exists but belongs to different user
                logger.warning(
                    f"User {current_user.id} attempted to delete session {session_id} "
                    f"owned by different user"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "FORBIDDEN",
                        "message": "You do not have access to this session"
                    }
                )
            else:
                # Session does not exist
                logger.warning(f"Session {session_id} not found for deletion")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "SESSION_NOT_FOUND",
                        "message": f"Session {session_id} not found"
                    }
                )

        # Delete the session (messages cascade automatically via SQLModel relationship)
        await db.delete(session)
        await db.commit()

        logger.info(
            f"Session {session_id} deleted successfully for user {current_user.id}"
        )

        return DeleteResponse(
            success=True,
            data=DeletedSessionData(
                deleted=True,
                session_id=session_id
            )
        )

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(
            f"Database error deleting session {session_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "SERVICE_UNAVAILABLE",
                "message": "Database unavailable"
            }
        )
