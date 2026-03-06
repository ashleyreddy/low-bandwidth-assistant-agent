#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run OAuth consent flow and print Gmail refresh token + JSON snippet."
    )
    parser.add_argument(
        "--client-secrets",
        required=True,
        help="Path to OAuth client JSON downloaded from Google Cloud Console",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8765,
        help="Local redirect port used by run_local_server (default: 8765)",
    )
    parser.add_argument(
        "--account",
        default="",
        help="Optional email override for output JSON entry",
    )
    return parser.parse_args()


def load_client_id_secret(client_secrets_path: Path) -> tuple[str, str]:
    data = json.loads(client_secrets_path.read_text(encoding="utf-8"))
    key = "installed" if "installed" in data else "web"
    section = data.get(key, {})
    client_id = section.get("client_id")
    client_secret = section.get("client_secret")
    if not client_id or not client_secret:
        raise ValueError("client_id/client_secret missing in client secrets JSON")
    return client_id, client_secret


def main() -> int:
    args = parse_args()
    secrets = Path(args.client_secrets).expanduser().resolve()

    if not secrets.exists():
        print(f"Client secrets file not found: {secrets}", file=sys.stderr)
        return 1

    try:
        client_id, client_secret = load_client_id_secret(secrets)
    except Exception as exc:
        print(f"Failed reading client secrets: {exc}", file=sys.stderr)
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), SCOPES)
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=args.port,
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    refresh_token = creds.refresh_token
    if not refresh_token:
        print(
            "No refresh token returned. Revoke prior app access and rerun with prompt=consent.",
            file=sys.stderr,
        )
        return 2

    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    profile = gmail.users().getProfile(userId="me").execute()
    email = args.account.strip() or profile.get("emailAddress") or "unknown@example.com"

    entry = {
        "account": email,
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    print("\\nRefresh token generated successfully.\\n")
    print("Single account JSON entry:")
    print(json.dumps(entry, indent=2))
    print("\\nFor multiple Gmail accounts, combine entries in .env as:")
    print("GMAIL_ACCOUNTS_JSON=[{...},{...}]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
