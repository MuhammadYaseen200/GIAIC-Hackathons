#!/usr/bin/env python3
"""
One-time LinkedIn OAuth2 Authorization Code flow.
Generates linkedin_token.json with offline_access scope.

HT-013b: Run this manually once per account.
Usage: python3 scripts/linkedin_auth.py
"""
import json
import os
import sys
import time
import platform
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

TOKEN_FILE = PROJECT_ROOT / "linkedin_token.json"
REDIRECT_URI = "http://localhost:8765/callback"
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
PROFILE_URL = "https://api.linkedin.com/v2/userinfo"  # OIDC userinfo — returns 'sub' as person ID
SCOPES = "openid profile email w_member_social"

_auth_code = None
_auth_error = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code, _auth_error
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h1>Auth successful! Return to terminal.</h1>")
        elif "error" in params:
            _auth_error = params.get("error_description", ["Unknown error"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h1>Error: {_auth_error}</h1>".encode())

    def log_message(self, *args):
        pass  # Suppress request logging


def main():
    load_dotenv(PROJECT_ROOT / ".env")
    client_id = os.environ.get("LINKEDIN_CLIENT_ID", "")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        print("LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET must be set in .env")
        sys.exit(1)

    state = os.urandom(16).hex()
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
    }
    auth_full_url = f"{AUTH_URL}?{urlencode(auth_params)}"

    print(f"\n{'='*60}")
    print("STEP 1: Open this URL in your browser (copy-paste it):")
    print(f"\n{auth_full_url}\n")
    print(f"{'='*60}")
    # Try to open browser — works on native Linux; WSL2 may fail silently
    try:
        is_wsl = "microsoft" in open("/proc/version").read().lower() if os.path.exists("/proc/version") else False
        if is_wsl:
            # WSL2: use cmd.exe to open the Windows default browser
            subprocess.run(["cmd.exe", "/c", "start", auth_full_url.replace("&", "^&")],
                           capture_output=True, timeout=5)
        else:
            subprocess.Popen(["xdg-open", auth_full_url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass  # URL already printed above — user can copy-paste manually

    print("Waiting for authorization callback on http://localhost:8765/callback ...")
    server = HTTPServer(("localhost", 8765), CallbackHandler)
    server.timeout = 120
    server.handle_request()

    if _auth_error:
        print(f"Authorization error: {_auth_error}")
        sys.exit(1)
    if not _auth_code:
        print("No authorization code received (timeout or user cancelled).")
        sys.exit(1)

    print("Authorization code received. Exchanging for tokens...")
    resp = httpx.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": _auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=15.0,
    )
    if not resp.is_success:
        print(f"Token exchange failed: {resp.status_code} {resp.text}")
        sys.exit(1)

    token_data = resp.json()
    access_token = token_data["access_token"]
    refresh_token = token_data.get("refresh_token")
    expires_at = time.time() + token_data.get("expires_in", 3600)

    # Fetch person URN via OIDC userinfo endpoint — returns 'sub' as the person ID
    profile_resp = httpx.get(
        PROFILE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10.0,
    )
    person_id = profile_resp.json().get("sub", "") if profile_resp.is_success else ""
    person_urn = f"urn:li:person:{person_id}" if person_id else ""

    token_obj = {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": expires_at,
        "person_urn": person_urn,
        "token_type": "Bearer",
    }
    TOKEN_FILE.write_text(json.dumps(token_obj, indent=2))
    TOKEN_FILE.chmod(0o600)  # Restrict to owner only (security: token file is sensitive)

    print(f"\nAuthentication successful!")
    print(f"   person_urn: {person_urn}")
    print(f"   refresh_token: {'PRESENT' if refresh_token else 'MISSING'}")
    print(f"   Token saved to: {TOKEN_FILE}")
    print(f"\nAdd to .env:")
    print(f"   LINKEDIN_PERSON_URN={person_urn}")


if __name__ == "__main__":
    main()
