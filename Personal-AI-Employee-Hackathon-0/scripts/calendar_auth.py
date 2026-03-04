"""One-time Google Calendar OAuth2 authorization script — T026.

Run this to generate calendar_token.json for HT-011.
Usage: python3 scripts/calendar_auth.py

WSL2 note: uses a fixed port (8085) with open_browser=False so you can
copy-paste the URL into your Windows browser manually.
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CREDENTIALS_PATH = os.getenv("CALENDAR_CREDENTIALS_PATH", "./credentials.json")
TOKEN_PATH = os.getenv("CALENDAR_TOKEN_PATH", "./calendar_token.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
PORT = 8085


def main():
    if not Path(CREDENTIALS_PATH).exists():
        print(f"ERROR: credentials.json not found at {CREDENTIALS_PATH}")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials")
        sys.exit(1)

    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)

    print(f"\nStarting local OAuth server on port {PORT}...")
    print("WSL2 instructions:")
    print("  1. Copy the URL printed below")
    print("  2. Paste it into your Windows browser and authorize")
    print(f"  3. Google will redirect to localhost:{PORT} — the script captures it automatically\n")

    creds = flow.run_local_server(
        port=PORT,
        open_browser=False,   # don't try gio/xdg-open — fails in WSL2
        prompt="consent",
        access_type="offline",
    )

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"\nCalendar token saved to: {TOKEN_PATH}")
    print("HT-011 complete -- Calendar MCP is now authorized.")


if __name__ == "__main__":
    main()
