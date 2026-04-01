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

    import os as _os
    _os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # allow http://localhost in WSL2
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)

    # WSL2-safe: Windows browser can't reach WSL2 localhost.
    # Instead: user authorizes, browser shows "connection refused" at localhost:8085,
    # user copies the full URL from the address bar and pastes it here.
    flow.redirect_uri = f"http://localhost:{PORT}/"
    auth_url, _ = flow.authorization_url(
        prompt="consent",
        access_type="offline",
    )

    print("\n" + "="*60)
    print("STEP 1 — Open this URL in your Windows browser:")
    print(f"\n  {auth_url}\n")
    print("STEP 2 — Sign in and click Allow.")
    print("STEP 3 — Browser will show 'connection refused' — that's normal.")
    print("STEP 4 — Copy the FULL URL from the browser address bar.")
    print("         It starts with:  http://localhost:8085/?state=...&code=...")
    print("="*60 + "\n")

    redirect_response = input("Paste the full redirect URL here: ").strip()

    flow.fetch_token(authorization_response=redirect_response)
    creds = flow.credentials

    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())

    print(f"\n✅ Calendar token saved to: {TOKEN_PATH}")
    print("HT-011 complete — Calendar MCP is now authorized.")


if __name__ == "__main__":
    main()
