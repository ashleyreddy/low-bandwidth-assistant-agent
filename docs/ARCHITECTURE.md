# Architecture

## Server

- `app/api/routes.py`: feed, action, and voice command APIs.
- `app/connectors/`: source adapters (currently mock).
- `app/services/feed_service.py`: aggregates connector data.
- `app/services/summarizer.py`: low-bandwidth summary strategy.
- `app/services/command_parser.py`: transcript -> structured command.

## Client (iOS)

- `ContentView`: list + action controls + voice controls.
- `FeedViewModel`: API orchestration.
- `VoiceRecognizer`: speech capture via `Speech` + `AVFoundation`.
- `APIClient`: backend integration.

## Next Production Steps

1. Replace mock connectors with real API clients and OAuth token refresh.
2. Add auth between mobile app and backend (JWT + refresh flow).
3. Add persistent data store and idempotent action execution.
4. Add APNs push notifications for new feed items.
