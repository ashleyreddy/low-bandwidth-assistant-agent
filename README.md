# Low Bandwidth Assistant Agent

A two-part assistant system:
- `server/`: FastAPI backend with connector adapters (Gmail, Slack, Google Drive, Google Photos).
- `ios/LowBandwidthAssistant/`: iOS SwiftUI client with feed actions and voice commands.
- `desktop/`: Python Tkinter desktop client for feed/actions/voice-command execution.

The backend auto-uses real Gmail and Slack connectors when credentials are set, and falls back to mocks when not configured.

## Features

- Unified feed across multiple Gmail accounts, Slack, GDrive, and Google Photos.
- Low-bandwidth content mode: returns summary or full message, whichever is shorter.
- Message actions: reply, forward, mark spam, archive.
- Image actions: forward to `receipts@ramp.com`, move to another account.
- Voice command parsing pipeline (`/v1/voice/command`) and iOS speech capture.

## Server Quickstart

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Connector behavior:
- Gmail: live via `GMAIL_ACCOUNTS_JSON` (multi-account OAuth refresh tokens), otherwise mock.
- Slack: live via `SLACK_BOT_TOKEN` + `SLACK_CHANNEL_IDS`, otherwise mock.

### Gmail OAuth Token Bootstrap

Use the included script to generate a Gmail refresh token for each account.

1. Create OAuth credentials in Google Cloud (Desktop app), then download `client_secret.json`.
2. Run:

```bash
cd server
source .venv/bin/activate
python scripts/gmail_oauth_bootstrap.py --client-secrets ~/Downloads/client_secret.json
```

3. Sign in with the Gmail account and approve access.
4. Copy the printed JSON entry and append it into your `.env` `GMAIL_ACCOUNTS_JSON` array.

Example:

```env
GMAIL_ACCOUNTS_JSON=[{"account":"ops@company.com","client_id":"...","client_secret":"...","refresh_token":"..."},{"account":"finance@company.com","client_id":"...","client_secret":"...","refresh_token":"..."}]
```

Endpoints:
- `GET /healthz`
- `GET /v1/feed`
- `GET /v1/connectors` (shows live vs mock connector mode)
- `POST /v1/items/{item_id}/action`
- `POST /v1/voice/command`

## iOS Quickstart

This project uses XcodeGen for reproducible project files.

```bash
cd ios/LowBandwidthAssistant
xcodegen generate
open LowBandwidthAssistant.xcodeproj
```

Update `baseURL` in `APIClient.swift` to your server address before running on device.

## Desktop Quickstart

```bash
cd /home/ros2/low-bandwidth-assistant
python3 desktop/client.py
```

The desktop app defaults to `http://127.0.0.1:8000` and supports:
- feed refresh + auto-refresh
- message actions (reply/forward/spam/archive)
- image actions (send to Ramp/move account)
- running transcript-based voice commands via `/v1/voice/command`

## Voice Command Examples

- `reply item gmail_1 Sounds good, I will send it today`
- `forward item slack_1 to boss@company.com`
- `mark spam item gmail_1`
- `forward item gphoto_1 to ramp`
- `move item gdrive_1 account archive@company.com`

## Production Integration Notes

- Gmail: requires OAuth scope `https://www.googleapis.com/auth/gmail.modify`.
- Slack: bot token needs scopes for reading history and posting messages (`channels:history`, `groups:history`, `chat:write`).
- GDrive / Photos: still mock in this scaffold.
- Add webhook handlers or polling workers for near-real-time delivery.
- Store events in Postgres and push updates via WebSockets for mobile efficiency.
