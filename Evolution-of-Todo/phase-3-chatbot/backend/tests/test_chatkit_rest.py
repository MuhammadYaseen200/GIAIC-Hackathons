"""Unit Tests for ChatKit REST Wrapper Layer.

Tests REST endpoint functionality, JSON-RPC translation,
error handling, and authorization.

Coverage:
- AC-001: Session creation (T006a-T006e)
- AC-002: Thread creation (T012a-T012e)
- AC-003: Message streaming (T017a-T017e)
- AC-004: Session listing (T024a-T024d)
- AC-005: Session history (T028a-T028e)

Spec: specs/features/chatkit-rest-wrapper/spec.md
Phase: Phase 2 (T006a-T006e) - Session creation unit tests
Phase: Phase 3 (T012a-T012e) - Thread creation unit tests
Phase: Phase 4 (T017a-T017e) - Send message unit tests
Phase: Phase 5 (T024a-T024d) - Session listing unit tests
Phase: Phase 6 (T028a-T028e) - Session history unit tests
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, select

from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.rate_limit import limiter
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
        email="testuser@example.com",
        password_hash="$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12",
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


@pytest.fixture()
async def override_deps_no_auth(async_session: AsyncSession):
    """Override only the database dependency (no auth override).

    This forces the real get_current_user to run, which will
    raise 401 when no JWT is provided.
    """

    async def _override_get_session():
        yield async_session

    app.dependency_overrides[get_session] = _override_get_session
    # Deliberately NOT overriding get_current_user
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# T006a: Test session creation with valid JWT returns HTTP 200
# AC-001: POST /chatkit/sessions with empty body creates session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_with_valid_jwt_returns_200(
    override_deps,
    test_user: User,
):
    """T006a: Session creation with valid JWT returns HTTP 200.

    Verifies:
    - HTTP 200 status code
    - Response body has success=true
    - Response data contains id, user_id, created_at
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/chatkit/sessions")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert "id" in body["data"]
    assert "user_id" in body["data"]
    assert "created_at" in body["data"]


# ---------------------------------------------------------------------------
# T006b: Test session creation without JWT returns HTTP 401
# AC-001: HTTP 401 returned for unauthenticated request
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_without_jwt_returns_401(
    override_deps_no_auth,
):
    """T006b: Session creation without JWT returns HTTP 401.

    Verifies that the real get_current_user dependency rejects
    requests without a valid Authorization header or cookie.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/chatkit/sessions")

    assert response.status_code == 401, (
        f"Expected 401, got {response.status_code}: {response.text}"
    )


# ---------------------------------------------------------------------------
# T006c: Test session creation at limit (10 sessions) returns HTTP 429
# AC-001: HTTP 429 returned when user has 10 sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session_at_limit_returns_429(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T006c: Session creation at limit (10 sessions) returns HTTP 429.

    Creates 10 existing conversations for the test user, then verifies
    that the 11th session request returns 429 with SESSION_LIMIT code.
    """
    # Create 10 existing sessions
    for _ in range(10):
        conversation = Conversation(
            id=uuid4(),
            user_id=test_user.id,
            title="Existing Chat",
            messages=[],
        )
        async_session.add(conversation)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/chatkit/sessions")

    assert response.status_code == 429, (
        f"Expected 429, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_LIMIT"
    assert "Maximum 10 sessions allowed" in body["error"]["message"]


# ---------------------------------------------------------------------------
# T006d: Test response contains valid UUID for id and user_id
# AC-001: Response contains valid UUID for id; Response contains user_id
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_response_contains_valid_uuid(
    override_deps,
    test_user: User,
):
    """T006d: Response contains valid UUID for id and user_id.

    Verifies:
    - data.id is a valid UUID
    - data.user_id is a valid UUID matching the authenticated user
    - data.created_at is a valid ISO 8601 timestamp
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/chatkit/sessions")

    assert response.status_code == 200
    data = response.json()["data"]

    # Validate UUID format (raises ValueError if invalid)
    session_id = UUID(data["id"])
    assert session_id is not None

    user_id = UUID(data["user_id"])
    assert user_id == test_user.id

    # Validate datetime format
    created_at = datetime.fromisoformat(data["created_at"])
    assert created_at is not None


# ---------------------------------------------------------------------------
# T006e: Test database record created in conversation table
# AC-001: Database record created in conversation table
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_database_record_created(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T006e: Database record created in conversation table.

    Verifies that after session creation:
    - A Conversation row exists in the database
    - The row has the correct user_id
    - The row has a valid created_at timestamp
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/api/v1/chatkit/sessions")

    assert response.status_code == 200
    session_id_str = response.json()["data"]["id"]
    session_id = UUID(session_id_str)

    # Query the database to verify the record exists
    from sqlmodel import select as sqlmodel_select

    result = await async_session.execute(
        sqlmodel_select(Conversation).where(Conversation.id == session_id)
    )
    conversation = result.scalar_one_or_none()

    assert conversation is not None, (
        f"Conversation {session_id} not found in database"
    )
    assert conversation.user_id == test_user.id
    assert conversation.created_at is not None
    assert conversation.title == "New Chat"
    assert conversation.messages == []


# ===========================================================================
# Phase 3: REQ-002 - Create Thread (T012a-T012e)
# AC-002: Thread creation (spec.md lines 569-575)
# ===========================================================================


# ---------------------------------------------------------------------------
# T012a: Test thread creation with valid session returns HTTP 200
# AC-002: POST /chatkit/sessions/{id}/threads with empty body creates thread
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_thread_with_valid_session_returns_200(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T012a: Thread creation with valid session returns HTTP 200.

    Verifies:
    - HTTP 200 status code
    - Response body has success=true
    - Response data contains id, session_id, created_at
    """
    # Create a session first
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/chatkit/sessions/{session.id}/threads"
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is True
    assert "data" in body
    assert "id" in body["data"]
    assert "session_id" in body["data"]
    assert "created_at" in body["data"]
    assert body["data"]["session_id"] == str(session.id)


# ---------------------------------------------------------------------------
# T012b: Test thread creation for non-existent session returns HTTP 404
# AC-002: HTTP 404 returned for non-existent session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_thread_for_nonexistent_session_returns_404(
    override_deps,
    test_user: User,
):
    """T012b: Thread creation for non-existent session returns HTTP 404.

    Verifies:
    - HTTP 404 status code
    - Error code is SESSION_NOT_FOUND
    """
    fake_session_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/chatkit/sessions/{fake_session_id}/threads"
        )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# T012c: Test thread creation for another user's session returns HTTP 403
# AC-002: HTTP 403 returned for session belonging to different user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_thread_for_another_users_session_returns_403(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T012c: Thread creation for another user's session returns HTTP 403.

    Creates a session owned by a different user, then verifies that
    the authenticated test user gets a 403 Forbidden response.
    """
    # Create a session owned by a different user
    other_user_id = uuid4()
    other_user = User(
        id=other_user_id,
        email="otheruser@example.com",
        password_hash="$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12",
    )
    async_session.add(other_user)
    await async_session.commit()

    session = Conversation(
        id=uuid4(),
        user_id=other_user_id,  # Different user
        title="Other User Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/chatkit/sessions/{session.id}/threads"
        )

    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------------------------
# T012d: Test idempotency - creating thread twice returns same thread ID
# AC-002: Idempotent thread creation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_thread_idempotency_returns_same_thread_id(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T012d: Creating thread twice returns same thread ID (idempotency).

    Verifies:
    - Both calls return HTTP 200
    - Thread ID is identical in both responses
    - created_at is identical in both responses
    """
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # First call
        response1 = await client.post(
            f"/api/v1/chatkit/sessions/{session.id}/threads"
        )
        # Second call (idempotent)
        response2 = await client.post(
            f"/api/v1/chatkit/sessions/{session.id}/threads"
        )

    assert response1.status_code == 200
    assert response2.status_code == 200

    thread_id_1 = response1.json()["data"]["id"]
    thread_id_2 = response2.json()["data"]["id"]
    assert thread_id_1 == thread_id_2, (
        f"Thread IDs differ: {thread_id_1} != {thread_id_2}"
    )

    # Verify created_at is also identical (same session timestamp)
    created_at_1 = response1.json()["data"]["created_at"]
    created_at_2 = response2.json()["data"]["created_at"]
    assert created_at_1 == created_at_2


# ---------------------------------------------------------------------------
# T012e: Test thread ID matches session ID (ChatKit 1:1 mapping)
# AC-002: Thread ID == Session ID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_thread_id_matches_session_id(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T012e: Thread ID matches session ID (ChatKit 1:1 mapping).

    Verifies:
    - data.id == data.session_id (1:1 mapping)
    - data.id == the original session UUID
    """
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/chatkit/sessions/{session.id}/threads"
        )

    assert response.status_code == 200
    data = response.json()["data"]

    # Thread ID must equal session ID (ChatKit 1:1 mapping)
    assert data["id"] == data["session_id"], (
        f"Thread ID {data['id']} != session_id {data['session_id']}"
    )
    # Both must match the original session UUID
    assert data["id"] == str(session.id), (
        f"Thread ID {data['id']} != original session {session.id}"
    )


# ===========================================================================
# Phase 4: REQ-003 - Send Message & Stream (T017a-T017e)
# AC-003: Message streaming (spec.md lines 577-585)
# ===========================================================================


def _make_mock_streaming_result():
    """Create a mock StreamingResult that yields SSE-formatted bytes.

    Simulates what ChatKit SDK's StreamingResult yields:
    each event is already ``b"data: {json}\\n\\n"`` formatted.
    """
    from chatkit.server import StreamingResult

    async def _mock_stream():
        events = [
            b'data: {"type":"thread.item.created"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":"Hello"}\n\n',
            b'data: {"type":"thread.item.content.part.delta","delta":" world"}\n\n',
            b'data: {"type":"thread.item.done"}\n\n',
        ]
        for event in events:
            yield event

    return StreamingResult(_mock_stream())


# ---------------------------------------------------------------------------
# T017a: Test sending message with valid session returns SSE stream
# AC-003: POST /chatkit/sessions/{id}/threads/{tid}/runs accepts message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_with_valid_session_returns_sse_stream(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017a: Message sending with valid session returns SSE stream.

    Verifies:
    - HTTP 200 status code
    - Content-Type is text/event-stream
    - Stream contains SSE-formatted data events
    - Stream ends with data: [DONE]
    """
    # Create a session
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    thread_id = session.id  # ChatKit 1:1 mapping

    # Mock ChatKit server.process to return fake streaming result
    mock_result = _make_mock_streaming_result()

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
                            {"type": "input_text", "text": "Hello AI"}
                        ],
                    }
                },
            )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )
    assert "text/event-stream" in response.headers["content-type"]

    # Verify stream contains SSE data events and ends with [DONE]
    body = response.text
    assert "data:" in body
    assert "data: [DONE]" in body


# ---------------------------------------------------------------------------
# T017b: Test sending empty message (whitespace-only) returns HTTP 400
# AC-003: HTTP 400 returned for empty message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_with_empty_text_returns_400(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017b: Sending empty message (whitespace-only) returns HTTP 400.

    Verifies:
    - HTTP 400 status code
    - Error code is EMPTY_MESSAGE
    """
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    thread_id = session.id

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
                        {"type": "input_text", "text": "   "}
                    ],
                }
            },
        )

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "EMPTY_MESSAGE"


# ---------------------------------------------------------------------------
# T017c: Test sending message >500 chars returns HTTP 400
# AC-003 criterion 6: HTTP 400 returned for message >500 chars
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_with_long_text_returns_400(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017c: Sending message >500 chars returns HTTP 400.

    AC-003 criterion 6 requires HTTP 400 (not 422) for oversized messages.
    The endpoint validates message length explicitly before Pydantic
    validation, returning 400 with MESSAGE_TOO_LONG error code.
    """
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    thread_id = session.id

    long_message = "x" * 501  # 501 chars exceeds 500 char limit

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
                        {"type": "input_text", "text": long_message}
                    ],
                }
            },
        )

    assert response.status_code == 400, (
        f"Expected 400, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "MESSAGE_TOO_LONG"
    assert "500" in body["error"]["message"]


# ---------------------------------------------------------------------------
# T017d: Test non-existent session returns HTTP 404
# AC-003: Implicit (session must exist)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_for_nonexistent_session_returns_404(
    override_deps,
    test_user: User,
):
    """T017d: Sending message for non-existent session returns HTTP 404.

    Verifies:
    - HTTP 404 status code
    - Error code is SESSION_NOT_FOUND
    """
    fake_session_id = uuid4()
    fake_thread_id = fake_session_id  # ChatKit 1:1 mapping

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/v1/chatkit/sessions/{fake_session_id}"
            f"/threads/{fake_thread_id}/runs",
            json={
                "message": {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": "Hello"}
                    ],
                }
            },
        )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# T017e: Test another user's session returns HTTP 403
# AC-003: Implicit (user must own session)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_for_another_users_session_returns_403(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T017e: Sending message for another user's session returns HTTP 403.

    Creates a session owned by a different user, then verifies that
    the authenticated test user gets a 403 Forbidden response.
    """
    # Create a session owned by a different user
    other_user_id = uuid4()
    other_user = User(
        id=other_user_id,
        email="otheruser-msg@example.com",
        password_hash=(
            "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12"
        ),
    )
    async_session.add(other_user)
    await async_session.commit()

    session = Conversation(
        id=uuid4(),
        user_id=other_user_id,  # Different user
        title="Other User Session",
        messages=[],
    )
    async_session.add(session)
    await async_session.commit()
    thread_id = session.id

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

    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


# ===========================================================================
# Phase 5: REQ-004 - List Sessions (T024a-T024d)
# AC-004: Session listing (spec.md lines 585-589)
# ===========================================================================


# ---------------------------------------------------------------------------
# T024a: Test listing sessions returns only user's sessions
# AC-004: GET /chatkit/sessions returns user's sessions only
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_returns_only_users_sessions(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T024a: Listing sessions returns only user's sessions.

    Creates sessions for the test user and a different user, then verifies
    only the test user's sessions are returned. Also validates the
    success/data/meta response structure.
    """
    now = datetime.now(UTC)

    # Create sessions for test user
    session1 = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="User Session 1",
        messages=[],
        created_at=now,
        updated_at=now,
    )
    session2 = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="User Session 2",
        messages=[],
        created_at=now,
        updated_at=now,
    )

    # Create session for different user (must NOT appear in results)
    other_user_id = uuid4()
    other_user = User(
        id=other_user_id,
        email="otheruser-list@example.com",
        password_hash=(
            "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12"
        ),
    )
    async_session.add(other_user)
    await async_session.commit()

    other_session = Conversation(
        id=uuid4(),
        user_id=other_user_id,
        title="Other User Session",
        messages=[],
        created_at=now,
        updated_at=now,
    )

    async_session.add_all([session1, session2, other_session])
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/chatkit/sessions")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 2  # Only user's sessions
    assert data["meta"]["total"] == 2

    # Verify other user's session is NOT included
    session_ids = [item["id"] for item in data["data"]]
    assert str(session1.id) in session_ids
    assert str(session2.id) in session_ids
    assert str(other_session.id) not in session_ids


# ---------------------------------------------------------------------------
# T024b: Test sessions ordered by updated_at DESC (newest first)
# AC-004: Sessions ordered by updated_at DESC (newest first)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_ordered_by_updated_at_desc(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T024b: Sessions are ordered by updated_at DESC (newest first).

    Creates three sessions with different updated_at timestamps and
    verifies the response order is newest-first.
    """
    now = datetime.now(UTC)

    old_session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Old Session",
        messages=[],
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3),
    )
    middle_session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Middle Session",
        messages=[],
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    new_session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="New Session",
        messages=[],
        created_at=now - timedelta(days=1),
        updated_at=now - timedelta(days=1),
    )

    # Add in non-sorted order to ensure DB ordering works
    async_session.add_all([old_session, new_session, middle_session])
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/chatkit/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 3

    # Verify order: newest first
    assert data["data"][0]["id"] == str(new_session.id)
    assert data["data"][1]["id"] == str(middle_session.id)
    assert data["data"][2]["id"] == str(old_session.id)


# ---------------------------------------------------------------------------
# T024c: Test message_count field is accurate
# AC-004: Response includes message_count for each session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_includes_message_count(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T024c: message_count field is accurate.

    Creates a session with 3 messages and verifies the message_count
    in the list response matches the actual count.
    """
    now = datetime.now(UTC)

    session_with_msgs = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Session with Messages",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Message 1"}
                ],
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Response 1"}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Message 2"}
                ],
            },
        ],
        created_at=now,
        updated_at=now,
    )

    async_session.add(session_with_msgs)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/chatkit/sessions")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["message_count"] == 3


# ---------------------------------------------------------------------------
# T024d: Test empty array when user has no sessions
# AC-004: Empty array returned when user has no sessions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions_returns_empty_array_when_no_sessions(
    override_deps,
    test_user: User,
):
    """T024d: Empty array returned when user has no sessions.

    Verifies the response structure is correct with empty data array
    and meta.total == 0.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/chatkit/sessions")

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert data["success"] is True
    assert data["data"] == []
    assert data["meta"]["total"] == 0


# ===========================================================================
# Phase 6: REQ-005 - Get Session History (T028a-T028e)
# AC-005: Session history retrieval (spec.md lines 591-596)
# ===========================================================================


# ---------------------------------------------------------------------------
# T028a: Test get session returns session with messages
# AC-005: GET /chatkit/sessions/{id} returns session with messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_returns_session_with_messages(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T028a: Get session returns session with messages.

    Verifies:
    - HTTP 200 status code
    - Response body has success=true
    - Response data contains session metadata and messages
    - Messages include both user and assistant messages
    """
    now = datetime.now(UTC)
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[
            {
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}],
                "created_at": now.isoformat(),
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}],
                "created_at": (now + timedelta(seconds=1)).isoformat(),
            },
        ],
        created_at=now,
        updated_at=now,
    )
    async_session.add(session)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/chatkit/sessions/{session.id}"
        )

    assert response.status_code == 200, (
        f"Expected 200, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == str(session.id)
    assert data["data"]["user_id"] == str(test_user.id)
    assert data["data"]["title"] == "Test Session"
    assert len(data["data"]["messages"]) == 2
    assert data["data"]["messages"][0]["role"] == "user"
    assert data["data"]["messages"][1]["role"] == "assistant"


# ---------------------------------------------------------------------------
# T028b: Test messages ordered by created_at ASC (oldest first)
# AC-005: Messages ordered by created_at ASC (oldest first)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_messages_ordered_by_created_at_asc(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T028b: Messages ordered by created_at ASC (oldest first).

    Creates a session with 3 messages at different timestamps and verifies
    the response returns them in chronological order (oldest first).
    """
    base_time = datetime.now(UTC)
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Message 1"},
                ],
                "created_at": base_time.isoformat(),
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Response 1"}],
                "created_at": (
                    base_time + timedelta(seconds=1)
                ).isoformat(),
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Message 2"},
                ],
                "created_at": (
                    base_time + timedelta(seconds=2)
                ).isoformat(),
            },
        ],
        created_at=base_time,
        updated_at=base_time,
    )
    async_session.add(session)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/chatkit/sessions/{session.id}"
        )

    assert response.status_code == 200
    data = response.json()
    messages = data["data"]["messages"]
    assert len(messages) == 3

    # Verify chronological order (ASC - oldest first)
    assert messages[0]["content"][0]["text"] == "Message 1"
    assert messages[1]["content"][0]["text"] == "Response 1"
    assert messages[2]["content"][0]["text"] == "Message 2"


# ---------------------------------------------------------------------------
# T028c: Test tool calls included in assistant messages
# AC-005: Tool calls included in assistant messages
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_includes_tool_calls(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T028c: Tool calls included in assistant messages.

    Verifies that assistant messages with tool_calls have the tool call
    details preserved in the response, including function name and arguments.
    """
    now = datetime.now(UTC)
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Test Session",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Create a task"},
                ],
                "created_at": now.isoformat(),
            },
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "I'll create that task for you.",
                    },
                ],
                "tool_calls": [
                    {
                        "id": "call_123",
                        "type": "function",
                        "function": {
                            "name": "add_task",
                            "arguments": (
                                '{"title": "New Task",'
                                ' "completed": false}'
                            ),
                        },
                    }
                ],
                "created_at": (now + timedelta(seconds=1)).isoformat(),
            },
        ],
        created_at=now,
        updated_at=now,
    )
    async_session.add(session)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/chatkit/sessions/{session.id}"
        )

    assert response.status_code == 200
    data = response.json()
    messages = data["data"]["messages"]
    assert len(messages) == 2

    # User message should have no tool_calls
    assert messages[0]["role"] == "user"
    assert messages[0]["tool_calls"] is None

    # Assistant message should have tool_calls
    assistant_msg = messages[1]
    assert assistant_msg["role"] == "assistant"
    assert assistant_msg["tool_calls"] is not None
    assert len(assistant_msg["tool_calls"]) == 1
    assert assistant_msg["tool_calls"][0]["id"] == "call_123"
    assert assistant_msg["tool_calls"][0]["type"] == "function"
    assert assistant_msg["tool_calls"][0]["function"]["name"] == "add_task"


# ---------------------------------------------------------------------------
# T028d: Test HTTP 404 for non-existent session
# AC-005: HTTP 404 returned for non-existent session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_returns_404_for_nonexistent_session(
    override_deps,
    test_user: User,
):
    """T028d: HTTP 404 for non-existent session.

    Verifies:
    - HTTP 404 status code
    - Error code is SESSION_NOT_FOUND
    """
    fake_session_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/chatkit/sessions/{fake_session_id}"
        )

    assert response.status_code == 404, (
        f"Expected 404, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


# ---------------------------------------------------------------------------
# T028e: Test HTTP 403 for unauthorized access
# AC-005: HTTP 403 returned for unauthorized access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_returns_403_for_unauthorized_access(
    override_deps,
    async_session: AsyncSession,
    test_user: User,
):
    """T028e: HTTP 403 for unauthorized access.

    Creates a session owned by a different user, then verifies that
    the authenticated test user gets a 403 Forbidden response.
    """
    # Create a session owned by a different user
    other_user_id = uuid4()
    other_user = User(
        id=other_user_id,
        email="otheruser-history@example.com",
        password_hash=(
            "$2b$12$fakehashfakehashfakehashfakehashfakehashfakehash12"
        ),
    )
    async_session.add(other_user)
    await async_session.commit()

    session = Conversation(
        id=uuid4(),
        user_id=other_user_id,  # Different user
        title="Other User Session",
        messages=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    async_session.add(session)
    await async_session.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            f"/api/v1/chatkit/sessions/{session.id}"
        )

    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )

    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


# ============================================================================
# Phase 7: REQ-006 - Delete Session Tests (T032a-T032e)
# ============================================================================

@pytest.mark.asyncio
async def test_delete_session_returns_200(
    async_session, test_user, override_deps
):
    """T032a: Test delete session returns HTTP 200"""
    # Create session
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Session to Delete",
        messages=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    async_session.add(session)
    await async_session.flush()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/api/v1/chatkit/sessions/{session.id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["deleted"] is True
    assert data["data"]["session_id"] == str(session.id)


@pytest.mark.asyncio
async def test_delete_session_cascades_messages(
    async_session, test_user, override_deps
):
    """T032b: Test messages cascade deleted"""
    # Create session with messages
    session = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Session with Messages",
        messages=[
            {"role": "user", "content": [{"type": "input_text", "text": "Test"}]},
            {"role": "assistant", "content": [{"type": "text", "text": "Response"}]}
        ],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    async_session.add(session)
    await async_session.flush()
    session_id = session.id

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Delete session
        response = await client.delete(
            f"/api/v1/chatkit/sessions/{session_id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

    assert response.status_code == 200

    # Verify session no longer exists
    result = await async_session.execute(
        select(Conversation).where(Conversation.id == session_id)
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_nonexistent_session_returns_404(
    async_session, test_user, override_deps
):
    """T032c: Test HTTP 404 for non-existent session"""
    fake_session_id = uuid4()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/api/v1/chatkit/sessions/{fake_session_id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "SESSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_unauthorized_session_returns_403(
    async_session, test_user, override_deps
):
    """T032d: Test HTTP 403 for unauthorized deletion"""
    other_user_id = uuid4()
    session = Conversation(
        id=uuid4(),
        user_id=other_user_id,  # Different user
        title="Other User Session",
        messages=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    async_session.add(session)
    await async_session.flush()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.delete(
            f"/api/v1/chatkit/sessions/{session.id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_deleted_session_not_in_list(
    async_session, test_user, override_deps
):
    """T032e: Test deleted session no longer in session list"""
    # Create two sessions
    session1 = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Session 1",
        messages=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    session2 = Conversation(
        id=uuid4(),
        user_id=test_user.id,
        title="Session 2",
        messages=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    async_session.add_all([session1, session2])
    await async_session.flush()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Delete session1
        await client.delete(
            f"/api/v1/chatkit/sessions/{session1.id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

        # Get session list
        response = await client.get(
            "/api/v1/chatkit/sessions",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1  # Only session2 remains
    assert data["data"][0]["id"] == str(session2.id)


# ============================================================================
# Rate Limiting Tests (slowapi)
# Security: Prevents API abuse and OpenRouter cost exposure
# ============================================================================


@pytest.fixture(autouse=False)
def reset_rate_limiter():
    """Reset the rate limiter storage before and after rate limit tests.

    The in-memory storage accumulates hits across tests. This fixture
    ensures a clean state for rate limit tests and cleans up afterwards
    so other tests are not affected.
    """
    limiter.reset()
    yield
    limiter.reset()


# ---------------------------------------------------------------------------
# Test: Rate limiter configured on the FastAPI app
# Verifies that app.state.limiter is set (structural check)
# ---------------------------------------------------------------------------


def test_rate_limiter_configured_on_app():
    """Verify that the rate limiter is attached to app.state.

    This is a structural test ensuring the slowapi limiter is properly
    registered on the FastAPI application instance.
    """
    assert hasattr(app.state, "limiter"), (
        "app.state.limiter not found - rate limiter not configured"
    )
    assert app.state.limiter is not None


# ---------------------------------------------------------------------------
# Test: Rate limiter returns HTTP 429 when limit exceeded
# Uses a low limit override to avoid sending 31 requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rate_limit_returns_429_when_exceeded(
    override_deps,
    test_user: User,
    reset_rate_limiter,
):
    """Verify that exceeding the rate limit returns HTTP 429.

    Sends 31 GET requests to /chatkit/sessions (limit is 30/minute)
    and verifies that the 31st request is rejected with 429 status.

    This test resets the limiter storage before and after to ensure
    isolation from other tests.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        # Send 30 requests (all should succeed)
        for i in range(30):
            response = await client.get("/api/v1/chatkit/sessions")
            assert response.status_code == 200, (
                f"Request {i + 1}/30 failed with {response.status_code}"
            )

        # The 31st request should be rate-limited
        response = await client.get("/api/v1/chatkit/sessions")
        assert response.status_code == 429, (
            f"Expected 429 on request 31, got {response.status_code}: "
            f"{response.text}"
        )
