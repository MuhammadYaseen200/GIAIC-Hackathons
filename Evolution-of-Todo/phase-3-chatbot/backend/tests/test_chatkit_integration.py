"""Integration Tests for ChatKit REST Wrapper Layer.

Tests verify the full endpoint flow including database interactions and
ChatKit SDK integration. Unit-level ChatKit SDK mocking is used to avoid
real OpenRouter API calls during CI.

Coverage:
- T017f: Full message flow (session -> thread -> message -> SSE stream)
- T017g: Tool call execution (AI triggers task creation)
- T017h: OpenRouter error handling (502 returned)

Spec: specs/features/chatkit-rest-wrapper/spec.md
Phase: Phase 4 (T017f-T017h) - Integration tests for REQ-003
"""

import json
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.api.deps import get_current_user
from app.core.database import get_session
from app.main import app
from app.models.conversation import Conversation
from app.models.user import User

# ---------------------------------------------------------------------------
# Test Database Setup
# Uses SQLite in-memory for isolation (no real Postgres needed)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def async_engine():
    """Create an async SQLite engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


@pytest.fixture()
async def async_session(async_engine):
    """Create an async session bound to the test engine."""
    async_session_factory = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    async with async_session_factory() as session:
        yield session


@pytest.fixture()
async def test_user(async_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user = User(
        id=uuid4(),
        email="integration-test@example.com",
        password_hash=(
            "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12"
        ),
    )
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    return user


@pytest.fixture()
async def override_deps(async_session: AsyncSession, test_user: User):
    """Override FastAPI dependencies for testing.

    Replaces:
    - get_session -> returns test async session
    - get_current_user -> returns test user (bypasses JWT)
    """

    async def _override_get_session():
        yield async_session

    async def _override_get_current_user():
        return test_user

    app.dependency_overrides[get_session] = _override_get_session
    app.dependency_overrides[get_current_user] = _override_get_current_user
    yield
    app.dependency_overrides.clear()


def _make_mock_streaming_result(events: list[bytes] | None = None):
    """Create a mock StreamingResult that yields SSE-formatted bytes.

    Args:
        events: Optional list of byte events. If not provided, uses
                default AI response simulation.
    """
    from chatkit.server import StreamingResult

    if events is None:
        events = [
            b'data: {"type":"thread.item.created"}\n\n',
            b'data: {"type":"thread.item.content.part.added"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":"I\'ll"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":" add"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":" that"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":" task"}\n\n',
            b'data: {"type":"thread.item.content.part.done"}\n\n',
            b'data: {"type":"thread.item.done"}\n\n',
        ]

    async def _mock_stream():
        for event in events:
            yield event

    return StreamingResult(_mock_stream())


# ---------------------------------------------------------------------------
# T017f: Full message flow integration test
# AC-003: POST /chatkit/sessions/{id}/threads/{tid}/runs accepts message
# AC-003: Response is SSE stream (text/event-stream)
# AC-003: SSE events contain deltas with AI response text
# AC-003: Stream ends with data: [DONE]
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_full_message_flow_with_ai_response(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017f: Test complete message flow from session creation to SSE stream.

    Flow:
    1. Create session (POST /sessions)
    2. Create thread (POST /sessions/{id}/threads)
    3. Send message (POST /sessions/{id}/threads/{tid}/runs)
    4. Verify SSE stream received with correct format
    5. Verify stream ends with [DONE]
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Step 1: Create session
        session_response = await client.post(
            "/api/v1/chatkit/sessions"
        )
        assert session_response.status_code == 200, (
            f"Session creation failed: {session_response.text}"
        )
        session_data = session_response.json()["data"]
        session_id = session_data["id"]

        # Step 2: Create thread
        thread_response = await client.post(
            f"/api/v1/chatkit/sessions/{session_id}/threads"
        )
        assert thread_response.status_code == 200, (
            f"Thread creation failed: {thread_response.text}"
        )
        thread_data = thread_response.json()["data"]
        thread_id = thread_data["id"]

        # Step 3: Send message with mocked ChatKit server
        mock_result = _make_mock_streaming_result()

        with patch(
            "app.api.v1.chatkit.server.process",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_process:
            message_response = await client.post(
                f"/api/v1/chatkit/sessions/{session_id}"
                f"/threads/{thread_id}/runs",
                json={
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Add a task: Buy groceries",
                            }
                        ],
                    }
                },
            )

    # Step 4: Verify SSE stream
    assert message_response.status_code == 200, (
        f"Message send failed: {message_response.text}"
    )
    assert "text/event-stream" in message_response.headers["content-type"]

    body = message_response.text
    # Verify SSE data events present
    assert "data:" in body
    # Verify delta events in stream
    assert "thread.item.content.part.delta" in body
    # Step 5: Verify [DONE] termination
    assert "data: [DONE]" in body

    # Verify process() was called with correct JSON-RPC payload
    mock_process.assert_called_once()
    call_args = mock_process.call_args
    payload_bytes = call_args[0][0]
    payload = json.loads(payload_bytes)
    assert payload["type"] == "threads.add_user_message"
    assert payload["params"]["thread_id"] == thread_id
    assert (
        payload["params"]["input"]["content"][0]["text"]
        == "Add a task: Buy groceries"
    )


# ---------------------------------------------------------------------------
# T017g: Tool call execution integration test
# AC-003: Tool calls executed (verified by checking database for new tasks)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tool_call_events_in_stream(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017g: Test that tool call events are passed through in the SSE stream.

    When ChatKit SDK processes a message and the AI invokes a tool,
    the stream should contain tool-call-related events. This test
    verifies that tool call events are present in the SSE output.

    NOTE: Actual database task creation is handled by ChatKit SDK
    internally (via the registered tool handlers in chatkit.py).
    This test verifies the REST wrapper correctly passes through
    the SSE events that include tool call information.
    """
    # Create session
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Tool Call Test",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    thread_id = session.id

    # Mock a streaming result that includes tool-call events
    tool_call_events = [
        b'data: {"type":"thread.item.created"}\n\n',
        b'data: {"type":"thread.item.content.part.added"}\n\n',
        b'data: {"type":"thread.item.content.part.delta","delta":"Adding task..."}\n\n',
        b'data: {"type":"thread.item.content.part.delta",'
        b'"delta":"\\n\\n**add_task:** {\\"success\\": true}"}'
        b"\n\n",
        b'data: {"type":"thread.item.content.part.done"}\n\n',
        b'data: {"type":"thread.item.done"}\n\n',
    ]
    mock_result = _make_mock_streaming_result(tool_call_events)

    with patch(
        "app.api.v1.chatkit.server.process",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/chatkit/sessions/{session.id}"
                f"/threads/{thread_id}/runs",
                json={
                    "message": {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": "Create task: Buy groceries",
                            }
                        ],
                    }
                },
            )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    body = response.text
    # Verify tool call result is present in stream
    assert "add_task" in body
    assert "success" in body
    assert "data: [DONE]" in body


# ---------------------------------------------------------------------------
# T017h: OpenRouter error returns HTTP 502
# AC-008: OpenRouter errors return HTTP 502 with friendly message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openrouter_error_returns_502(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017h: Test that OpenRouter errors return HTTP 502.

    Simulates ChatKit SDK / OpenRouter failure and verifies:
    1. HTTP 502 returned
    2. Error code is OPENROUTER_ERROR
    3. Error message is descriptive
    """
    # Create session
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Error Test",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    thread_id = session.id

    # Mock ChatKit server.process to raise exception
    with patch(
        "app.api.v1.chatkit.server.process",
        new_callable=AsyncMock,
        side_effect=Exception("OpenRouter API unavailable"),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                f"/api/v1/chatkit/sessions/{session.id}"
                f"/threads/{thread_id}/runs",
                json={
                    "message": {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Hello"}
                        ],
                    }
                },
            )

    assert response.status_code == 502, (
        f"Expected 502, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "OPENROUTER_ERROR"
    assert "OpenRouter API unavailable" in body["error"]["message"]
