"""Pydantic v2 I/O models for Calendar MCP tools — T023.

Used for input validation and output schema documentation.
Follows same pattern as mcp_servers/gmail/models.py.
"""
from typing import Literal, Optional

from pydantic import BaseModel

MCPErrorCode = Literal[
    "auth_required",
    "not_found",
    "rate_limited",
    "permission_denied",
    "parse_error",
    "send_failed",
    "mcp_unavailable",
    "internal_error",
]


class MCPError(BaseModel):
    """Standard error response returned by all Calendar MCP tools."""

    error: MCPErrorCode
    message: str
    details: Optional[dict] = None


class ListEventsInput(BaseModel):
    time_min: str
    time_max: Optional[str] = None
    max_results: int = 10


class CheckAvailabilityInput(BaseModel):
    time_slot_start: str
    time_slot_end: str


class CalendarEvent(BaseModel):
    event_id: str
    summary: str
    start: str
    end: str
    attendees: list[str] = []
    location: Optional[str] = None


class EventList(BaseModel):
    events: list[CalendarEvent]
    calendar_id: str
    fetched_at: str


class AvailabilityResult(BaseModel):
    is_available: bool
    conflicting_events: list[CalendarEvent] = []
    suggested_alternatives: Optional[list[str]] = None


class HealthCheckResult(BaseModel):
    status: str
    calendar_id: str
    email: str
