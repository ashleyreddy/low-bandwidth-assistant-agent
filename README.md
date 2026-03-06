# Low Bandwidth Assistant Agent

A two-part assistant system:
- `server/`: FastAPI backend with connector adapters (Gmail, Slack, Google Drive, Google Photos).
- `ios/LowBandwidthAssistant/`: iOS SwiftUI client with feed actions and voice commands.

The backend currently ships with mock connectors so the app runs immediately. Replace mocks with OAuth-powered connectors for production.

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

Endpoints:
- `GET /healthz`
- `GET /v1/feed`
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

## Voice Command Examples

- `reply item gmail_1 Sounds good, I will send it today`
- `forward item slack_1 to boss@company.com`
- `mark spam item gmail_1`
- `forward item gphoto_1 to ramp`
- `move item gdrive_1 account archive@company.com`

## Production Integration Notes

- Gmail / GDrive / Photos: use Google OAuth 2.0 with per-account token storage.
- Slack: use Events API + Web API for action operations.
- Add webhook handlers or polling workers for near-real-time delivery.
- Store events in Postgres and push updates via WebSockets for mobile efficiency.
