#!/usr/bin/env python3
"""One-time Gmail OAuth2 setup helper.

Requests all 3 scopes (readonly, send, modify), opens browser for consent,
saves token.json, and verifies with getProfile().

Usage:
    python scripts/gmail_auth.py [--credentials PATH] [--token PATH]

If paths are not provided, reads from GMAIL_CREDENTIALS_PATH and
GMAIL_TOKEN_PATH environment variables (loaded from .env).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from watchers.utils import atomic_write, load_env

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gmail OAuth2 setup -- authenticates and saves token"
    )
    parser.add_argument(
        "--credentials",
        type=str,
        default=None,
        help="Path to credentials.json (default: from .env)",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Path to save token.json (default: from .env)",
    )
    args = parser.parse_args()

    # Resolve paths
    credentials_path = args.credentials
    token_path = args.token

    if credentials_path is None or token_path is None:
        try:
            env = load_env()
            if credentials_path is None:
                credentials_path = env["GMAIL_CREDENTIALS_PATH"]
            if token_path is None:
                token_path = env["GMAIL_TOKEN_PATH"]
        except Exception as e:
            print(f"Error loading .env: {e}")
            print("Provide --credentials and --token flags, or create .env with:")
            print("  GMAIL_CREDENTIALS_PATH=/path/to/credentials.json")
            print("  GMAIL_TOKEN_PATH=/path/to/token.json")
            return 1

    credentials_path = Path(credentials_path)
    token_path = Path(token_path)

    if not credentials_path.exists():
        print(f"Error: credentials.json not found at {credentials_path}")
        print("Download it from Google Cloud Console (see HT-002).")
        return 1

    # Check for existing token
    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except (ValueError, KeyError):
            print(f"Warning: Existing token at {token_path} is corrupt, re-authenticating.")
            creds = None

    if creds and creds.valid:
        print(f"Token already valid at {token_path}")
    elif creds and creds.expired and creds.refresh_token:
        print("Token expired, refreshing...")
        creds.refresh(Request())
        atomic_write(token_path, creds.to_json())
        print("Token refreshed successfully.")
    else:
        print("Starting OAuth2 browser flow...")
        print("A browser window will open for Google consent.")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(credentials_path), SCOPES
        )
        creds = flow.run_local_server(port=0)
        atomic_write(token_path, creds.to_json())
        print(f"Token saved to {token_path}")

    # Verify with getProfile()
    print("\nVerifying authentication...")
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "unknown")
        total_messages = profile.get("messagesTotal", 0)
        print(f"Authenticated as: {email}")
        print(f"Total messages: {total_messages}")
        print("\nGmail OAuth2 setup complete!")
        return 0
    except Exception as e:
        print(f"Error: Authentication verification failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
