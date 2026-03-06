from __future__ import annotations

from app.connectors.base import Connector
from app.connectors.gmail_connector import GmailConnector
from app.connectors.mock_connectors import (
    MockGDriveConnector,
    MockGmailConnector,
    MockGooglePhotosConnector,
    MockSlackConnector,
)
from app.connectors.slack_connector import SlackConnector
from app.models.schemas import ActionRequest, ActionResult, FeedResponse


class FeedService:
    def __init__(self) -> None:
        gmail = GmailConnector.from_env()
        slack = SlackConnector.from_env()

        self.connectors: list[Connector] = [
            gmail if gmail else MockGmailConnector(),
            slack if slack else MockSlackConnector(),
            MockGDriveConnector(),
            MockGooglePhotosConnector(),
        ]

    async def fetch_feed(self) -> FeedResponse:
        items = []
        for connector in self.connectors:
            items.extend(await connector.fetch())
        items.sort(key=lambda x: x.received_at, reverse=True)
        return FeedResponse(items=items)

    async def dispatch_action(self, item_id: str, req: ActionRequest) -> ActionResult:
        prefix = item_id.split("_", 1)[0]
        for connector in self.connectors:
            if connector.name.startswith(prefix):
                return await connector.act(item_id, req)

        return ActionResult(
            success=False,
            item_id=item_id,
            action=str(req.action),
            detail=f"No connector found for item '{item_id}'",
        )
