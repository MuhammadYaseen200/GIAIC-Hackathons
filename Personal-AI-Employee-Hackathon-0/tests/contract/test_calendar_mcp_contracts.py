"""Contract tests for Calendar MCP tools — T021.

Contracts verified against specs/008-hitl-whatsapp-silver/contracts/calendar-tools.json:
  - list_events output matches outputSchema (events array, calendar_id, fetched_at)
  - list_events returns empty events list (not error) when no events in window
  - check_availability returns is_available: true for empty slot
  - check_availability returns is_available: false + conflicting_events when overlap
  - health_check returns auth_required error when token file missing
  - All error responses have isError=True + JSON matching errorFormat
  - Event overlap logic: event.start < slot_end AND event.end > slot_start
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Contract schema loading ──────────────────────────────────────────────────

@pytest.fixture(scope="module")
def calendar_contract():
    """Load calendar-tools.json contract for schema validation."""
    contract_path = Path(__file__).parent.parent.parent / "specs" / "008-hitl-whatsapp-silver" / "contracts" / "calendar-tools.json"
    with open(contract_path) as f:
        return json.load(f)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _mock_calendar_service(events_items=None):
    """Create a mock Google Calendar service with configurable events."""
    svc = MagicMock()
    items = events_items if events_items is not None else []
    svc.events.return_value.list.return_value.execute.return_value = {
        "items": items
    }
    svc.calendarList.return_value.get.return_value.execute.return_value = {
        "id": "primary",
        "summary": "user@gmail.com",
    }
    return svc


SAMPLE_EVENT = {
    "id": "evt-001",
    "summary": "Team Standup",
    "start": {"dateTime": "2026-03-03T09:00:00Z"},
    "end": {"dateTime": "2026-03-03T09:30:00Z"},
    "attendees": [{"email": "alice@example.com"}],
    "location": "Room A",
}

SAMPLE_EVENT_2 = {
    "id": "evt-002",
    "summary": "Lunch Meeting",
    "start": {"dateTime": "2026-03-03T12:00:00Z"},
    "end": {"dateTime": "2026-03-03T13:00:00Z"},
    "attendees": [],
}


# ── list_events contract ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_events_success_schema(calendar_contract):
    """list_events success response has events array, calendar_id, fetched_at."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([SAMPLE_EVENT])
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
        )

    # Required fields from outputSchema
    output_schema = calendar_contract["tools"][0]["outputSchema"]
    for field in output_schema["required"]:
        assert field in result, f"Missing required field: {field}"

    assert isinstance(result["events"], list)
    assert isinstance(result["calendar_id"], str)
    assert isinstance(result["fetched_at"], str)


@pytest.mark.asyncio
async def test_list_events_event_fields(calendar_contract):
    """Each event in list_events output has required fields per contract."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([SAMPLE_EVENT])
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
        )

    event_schema = calendar_contract["tools"][0]["outputSchema"]["properties"]["events"]["items"]
    required_fields = event_schema["required"]
    event = result["events"][0]
    for field in required_fields:
        assert field in event, f"Event missing required field: {field}"


@pytest.mark.asyncio
async def test_list_events_empty_returns_empty_list_not_error():
    """list_events returns empty events list (not error) when no events in window."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([])
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
        )

    assert result["events"] == []
    assert "isError" not in result
    assert "calendar_id" in result
    assert "fetched_at" in result


# ── check_availability contract ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_availability_empty_slot_is_available():
    """check_availability returns is_available=True for empty slot."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T14:00:00Z",
            time_slot_end="2026-03-03T15:00:00Z",
        )

    assert result["is_available"] is True
    assert result["conflicting_events"] == []


@pytest.mark.asyncio
async def test_check_availability_overlap_returns_false():
    """check_availability returns is_available=False + conflicting_events when overlap."""
    # Event: 09:00-09:30; Slot: 09:00-10:00 → overlap
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([SAMPLE_EVENT])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T09:00:00Z",
            time_slot_end="2026-03-03T10:00:00Z",
        )

    assert result["is_available"] is False
    assert len(result["conflicting_events"]) > 0


@pytest.mark.asyncio
async def test_check_availability_schema(calendar_contract):
    """check_availability output matches outputSchema required fields."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T14:00:00Z",
            time_slot_end="2026-03-03T15:00:00Z",
        )

    output_schema = calendar_contract["tools"][1]["outputSchema"]
    for field in output_schema["required"]:
        assert field in result, f"Missing required field: {field}"


# ── health_check contract ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_check_auth_required_when_token_missing():
    """health_check returns auth_required error when token file missing."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.side_effect = Exception("auth_required: calendar_token.json missing")
        from mcp_servers.calendar.server import health_check
        result = await health_check()

    assert result.get("isError") is True
    content = json.loads(result["content"])
    assert content["error"] == "auth_required"
    assert "message" in content


@pytest.mark.asyncio
async def test_health_check_success_schema(calendar_contract):
    """health_check success returns status, calendar_id, email."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service()
        from mcp_servers.calendar.server import health_check
        result = await health_check()

    output_schema = calendar_contract["tools"][2]["outputSchema"]
    for field in output_schema["required"]:
        assert field in result, f"Missing required field: {field}"

    assert result["status"] == "healthy"


# ── Error format contract ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_responses_have_iserror_flag():
    """All error responses have isError=True + JSON content matching errorFormat."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.side_effect = Exception("auth_required: token missing")
        from mcp_servers.calendar.server import health_check
        result = await health_check()

    assert result["isError"] is True
    content = json.loads(result["content"])
    assert "error" in content
    assert "message" in content


@pytest.mark.asyncio
async def test_list_events_error_format():
    """list_events error response follows errorFormat schema."""
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.side_effect = Exception("auth_required: no token")
        from mcp_servers.calendar.server import list_events
        result = await list_events(time_min="2026-03-03T00:00:00Z")

    assert result["isError"] is True
    content = json.loads(result["content"])
    assert content["error"] in [
        "auth_required", "not_found", "rate_limited", "permission_denied",
        "parse_error", "send_failed", "mcp_unavailable", "internal_error",
    ]


# ── Event overlap logic ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_overlap_logic_event_starts_before_slot_ends():
    """Overlap: event.start < slot_end AND event.end > slot_start."""
    # Event: 09:00-09:30, Slot: 09:15-10:00 → partial overlap
    event = {
        "id": "evt-overlap",
        "summary": "Overlap Test",
        "start": {"dateTime": "2026-03-03T09:00:00Z"},
        "end": {"dateTime": "2026-03-03T09:30:00Z"},
        "attendees": [],
    }
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([event])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T09:15:00Z",
            time_slot_end="2026-03-03T10:00:00Z",
        )

    assert result["is_available"] is False
    assert len(result["conflicting_events"]) == 1


@pytest.mark.asyncio
async def test_no_overlap_event_ends_before_slot_starts():
    """No overlap: event ends exactly at slot start (adjacent, not overlapping)."""
    event = {
        "id": "evt-adjacent",
        "summary": "Adjacent Event",
        "start": {"dateTime": "2026-03-03T08:00:00Z"},
        "end": {"dateTime": "2026-03-03T09:00:00Z"},
        "attendees": [],
    }
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([event])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T09:00:00Z",
            time_slot_end="2026-03-03T10:00:00Z",
        )

    assert result["is_available"] is True
    assert result["conflicting_events"] == []


@pytest.mark.asyncio
async def test_no_overlap_event_starts_after_slot_ends():
    """No overlap: event starts exactly at slot end."""
    event = {
        "id": "evt-after",
        "summary": "After Slot",
        "start": {"dateTime": "2026-03-03T10:00:00Z"},
        "end": {"dateTime": "2026-03-03T11:00:00Z"},
        "attendees": [],
    }
    with patch("mcp_servers.calendar.server.get_calendar_service") as mock_auth:
        mock_auth.return_value = _mock_calendar_service([event])
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T09:00:00Z",
            time_slot_end="2026-03-03T10:00:00Z",
        )

    assert result["is_available"] is True
    assert result["conflicting_events"] == []
