#!/usr/bin/env python3
"""Calendar MCP server — FastMCP entry point — T025.

Exposes Google Calendar tools over stdio JSON-RPC:
  - list_events: List calendar events in a time window
  - check_availability: Check if a time slot is available
  - health_check: Verify Calendar API connectivity and OAuth token validity
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # project root

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

from mcp_servers.calendar.models import (
    CalendarEvent,
    EventList,
    AvailabilityResult,
    HealthCheckResult,
)
from mcp_servers.calendar.auth import get_calendar_service

mcp = FastMCP("calendar")


@mcp.tool()
async def list_events(
    time_min: str, time_max: str | None = None, max_results: int = 10
) -> dict:
    """List calendar events between time_min and time_max."""
    try:
        service = get_calendar_service()
        if time_max is None:
            dt = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
            time_max = (dt + timedelta(days=7)).isoformat()
        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = []
        for item in result.get("items", []):
            start = item["start"].get("dateTime", item["start"].get("date", ""))
            end = item["end"].get("dateTime", item["end"].get("date", ""))
            attendees = [a.get("email", "") for a in item.get("attendees", [])]
            events.append(
                CalendarEvent(
                    event_id=item["id"],
                    summary=item.get("summary", "(no title)"),
                    start=start,
                    end=end,
                    attendees=attendees,
                    location=item.get("location"),
                )
            )
        return EventList(
            events=events,
            calendar_id="primary",
            fetched_at=datetime.now(timezone.utc).isoformat(),
        ).model_dump()
    except Exception as e:
        if "auth_required" in str(e).lower():
            return {
                "isError": True,
                "content": json.dumps(
                    {"error": "auth_required", "message": str(e)}
                ),
            }
        return {
            "isError": True,
            "content": json.dumps(
                {"error": "internal_error", "message": str(e)}
            ),
        }


@mcp.tool()
async def check_availability(time_slot_start: str, time_slot_end: str) -> dict:
    """Check if a time slot is available."""
    try:
        events_result = await list_events(
            time_min=time_slot_start, time_max=time_slot_end
        )
        if events_result.get("isError"):
            return events_result
        events = [CalendarEvent(**e) for e in events_result.get("events", [])]
        # Overlap: event.start < slot_end AND event.end > slot_start
        conflicting = [
            e
            for e in events
            if e.start < time_slot_end and e.end > time_slot_start
        ]
        return AvailabilityResult(
            is_available=len(conflicting) == 0,
            conflicting_events=conflicting,
        ).model_dump()
    except Exception as e:
        return {
            "isError": True,
            "content": json.dumps(
                {"error": "internal_error", "message": str(e)}
            ),
        }


@mcp.tool()
async def health_check() -> dict:
    """Check Calendar MCP health."""
    try:
        service = get_calendar_service()
        cal = service.calendarList().get(calendarId="primary").execute()
        return HealthCheckResult(
            status="healthy",
            calendar_id=cal.get("id", "primary"),
            email=cal.get("summary", ""),
        ).model_dump()
    except Exception as e:
        return {
            "isError": True,
            "content": json.dumps(
                {"error": "auth_required", "message": str(e)}
            ),
        }


if __name__ == "__main__":
    mcp.run()
