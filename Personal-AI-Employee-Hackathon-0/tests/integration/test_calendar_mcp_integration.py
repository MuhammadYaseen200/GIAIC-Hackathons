"""Integration tests for Calendar MCP with mocked Google APIs — T022.

Tests:
  - list_events calls service.events().list() with correct timeMin/timeMax
  - time_max defaults to time_min + 7 days when not provided
  - check_availability with one overlapping event → is_available=False
  - check_availability with no overlapping events → is_available=True
  - Token refresh: mock expired access_token → verify credentials.refresh() called
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock, call
from datetime import datetime, timedelta, timezone


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_calendar_service():
    """A pre-configured MagicMock Google Calendar service."""
    svc = MagicMock()
    svc.events.return_value.list.return_value.execute.return_value = {"items": []}
    svc.calendarList.return_value.get.return_value.execute.return_value = {
        "id": "primary",
        "summary": "user@gmail.com",
    }
    return svc


SAMPLE_EVENTS = [
    {
        "id": "evt-001",
        "summary": "Morning Standup",
        "start": {"dateTime": "2026-03-03T09:00:00Z"},
        "end": {"dateTime": "2026-03-03T09:30:00Z"},
        "attendees": [{"email": "alice@example.com"}, {"email": "bob@example.com"}],
        "location": "Zoom",
    },
    {
        "id": "evt-002",
        "summary": "Lunch Meeting",
        "start": {"dateTime": "2026-03-03T12:00:00Z"},
        "end": {"dateTime": "2026-03-03T13:00:00Z"},
        "attendees": [],
    },
]


# ── list_events integration ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_events_calls_service_with_correct_params(mock_calendar_service):
    """list_events calls service.events().list() with correct timeMin/timeMax."""
    mock_calendar_service.events.return_value.list.return_value.execute.return_value = {
        "items": SAMPLE_EVENTS
    }
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
            max_results=10,
        )

    # Verify the service was called with correct parameters
    mock_calendar_service.events.return_value.list.assert_called_once_with(
        calendarId="primary",
        timeMin="2026-03-03T00:00:00Z",
        timeMax="2026-03-10T00:00:00Z",
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    )

    # Verify result structure
    assert len(result["events"]) == 2
    assert result["events"][0]["event_id"] == "evt-001"
    assert result["events"][0]["summary"] == "Morning Standup"
    assert result["events"][0]["attendees"] == ["alice@example.com", "bob@example.com"]
    assert result["events"][0]["location"] == "Zoom"
    assert result["calendar_id"] == "primary"
    assert "fetched_at" in result


@pytest.mark.asyncio
async def test_list_events_time_max_defaults_to_7_days(mock_calendar_service):
    """time_max defaults to time_min + 7 days when not provided."""
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import list_events
        result = await list_events(time_min="2026-03-03T00:00:00+00:00")

    # Verify time_max was set to time_min + 7 days
    call_args = mock_calendar_service.events.return_value.list.call_args
    time_max_used = call_args.kwargs.get("timeMax") or call_args[1].get("timeMax")

    expected_max = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc)
    actual_max = datetime.fromisoformat(time_max_used)
    assert abs((actual_max - expected_max).total_seconds()) < 5, (
        f"time_max should be ~7 days from time_min, got {time_max_used}"
    )


@pytest.mark.asyncio
async def test_list_events_parses_date_only_events(mock_calendar_service):
    """list_events handles all-day events (date instead of dateTime)."""
    all_day_event = {
        "id": "evt-allday",
        "summary": "Company Holiday",
        "start": {"date": "2026-03-05"},
        "end": {"date": "2026-03-06"},
        "attendees": [],
    }
    mock_calendar_service.events.return_value.list.return_value.execute.return_value = {
        "items": [all_day_event]
    }
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
        )

    assert len(result["events"]) == 1
    assert result["events"][0]["start"] == "2026-03-05"
    assert result["events"][0]["end"] == "2026-03-06"


@pytest.mark.asyncio
async def test_list_events_handles_no_title(mock_calendar_service):
    """list_events uses '(no title)' when event has no summary."""
    no_title_event = {
        "id": "evt-notitle",
        "start": {"dateTime": "2026-03-03T10:00:00Z"},
        "end": {"dateTime": "2026-03-03T11:00:00Z"},
    }
    mock_calendar_service.events.return_value.list.return_value.execute.return_value = {
        "items": [no_title_event]
    }
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import list_events
        result = await list_events(
            time_min="2026-03-03T00:00:00Z",
            time_max="2026-03-10T00:00:00Z",
        )

    assert result["events"][0]["summary"] == "(no title)"


# ── check_availability integration ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_check_availability_with_overlap(mock_calendar_service):
    """check_availability with overlapping event returns is_available=False."""
    # Event: 09:00-09:30, Slot: 09:00-10:00 → overlap
    mock_calendar_service.events.return_value.list.return_value.execute.return_value = {
        "items": [SAMPLE_EVENTS[0]]
    }
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T09:00:00Z",
            time_slot_end="2026-03-03T10:00:00Z",
        )

    assert result["is_available"] is False
    assert len(result["conflicting_events"]) == 1
    assert result["conflicting_events"][0]["event_id"] == "evt-001"


@pytest.mark.asyncio
async def test_check_availability_no_overlap(mock_calendar_service):
    """check_availability with no overlapping events returns is_available=True."""
    mock_calendar_service.events.return_value.list.return_value.execute.return_value = {
        "items": []
    }
    with patch("mcp_servers.calendar.server.get_calendar_service", return_value=mock_calendar_service):
        from mcp_servers.calendar.server import check_availability
        result = await check_availability(
            time_slot_start="2026-03-03T14:00:00Z",
            time_slot_end="2026-03-03T15:00:00Z",
        )

    assert result["is_available"] is True
    assert result["conflicting_events"] == []


# ── Token refresh integration ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_refresh_called_when_expired():
    """Token refresh: mock expired access_token → verify credentials.refresh() called."""
    mock_creds = MagicMock()
    mock_creds.valid = False
    mock_creds.expired = True
    mock_creds.refresh_token = "mock-refresh-token"
    mock_creds.to_json.return_value = '{"token": "refreshed"}'

    with patch("mcp_servers.calendar.auth.Path") as mock_path_cls, \
         patch("mcp_servers.calendar.auth.Credentials") as mock_creds_cls, \
         patch("mcp_servers.calendar.auth.Request") as mock_request_cls, \
         patch("mcp_servers.calendar.auth.build") as mock_build, \
         patch.dict("os.environ", {
             "CALENDAR_TOKEN_PATH": "/tmp/test_calendar_token.json",
             "CALENDAR_CREDENTIALS_PATH": "/tmp/test_creds.json",
         }):
        # Token file exists
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        mock_creds_cls.from_authorized_user_file.return_value = mock_creds
        mock_build.return_value = MagicMock()

        from mcp_servers.calendar.auth import get_calendar_service, reset_service_cache
        reset_service_cache()
        service = get_calendar_service()

        # Verify refresh was called
        mock_creds.refresh.assert_called_once()
        mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds)
