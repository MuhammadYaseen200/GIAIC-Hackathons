"""Demo 3: Calendar MCP — live query of your real Google Calendar."""
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

from mcp_servers.calendar.auth import get_calendar_service


def demo():
    print("\n📅 Calendar MCP — Live Demo")
    print("=" * 50)
    print("Querying your real Google Calendar for the next 7 days...\n")

    try:
        service = get_calendar_service()

        now = datetime.now(timezone.utc)
        time_max = now + timedelta(days=7)

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=time_max.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = result.get("items", [])
        print(f"✅ Found {len(events)} event(s) in the next 7 days:\n")
        if events:
            for e in events:
                start = e["start"].get("dateTime", e["start"].get("date", "?"))
                print(f"  📅  {e.get('summary', 'No title')}")
                print(f"       Start: {start}")
                if e.get("location"):
                    print(f"       Where: {e['location']}")
                if e.get("attendees"):
                    emails = [a.get("email", "") for a in e["attendees"][:3]]
                    print(f"       With:  {', '.join(emails)}")
                print()
        else:
            print("  (No events found — calendar is clear or next 7 days are empty)")

        # Also check availability tomorrow 10am–11am
        print("Checking availability tomorrow 10am–11am...")
        tomorrow = now + timedelta(days=1)
        slot_start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        slot_end = slot_start + timedelta(hours=1)

        avail_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=slot_start.isoformat(),
                timeMax=slot_end.isoformat(),
                singleEvents=True,
            )
            .execute()
        )
        conflicts = avail_result.get("items", [])
        is_free = len(conflicts) == 0
        status = "✅ FREE" if is_free else f"❌ BUSY ({len(conflicts)} conflict(s))"
        print(f"  Tomorrow 10–11am: {status}\n")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Check: is calendar_token.json present? Run: python3 scripts/calendar_auth.py")

    print("=" * 50)
    print("Calendar demo complete.\n")


demo()
