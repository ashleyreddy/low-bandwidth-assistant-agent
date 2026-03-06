from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.connectors.base import Connector
from app.models.schemas import (
    ActionRequest,
    ActionResult,
    FeedItem,
    FeedKind,
    SourceType,
)
from app.services.summarizer import shortest_message_or_summary


class MockGmailConnector(Connector):
    name = "gmail"

    async def fetch(self) -> list[FeedItem]:
        body = "Your invoice #9912 is ready. Total due: $132.45. Due date is next Friday."
        return [
            FeedItem(
                id="gmail_1",
                source=SourceType.gmail,
                account="ops@company.com",
                kind=FeedKind.message,
                title="Invoice is ready",
                body=body,
                summary=shortest_message_or_summary(body),
                received_at=datetime.now(UTC) - timedelta(minutes=7),
            )
        ]

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        return ActionResult(
            success=True,
            item_id=item_id,
            action=str(req.action),
            detail=f"Gmail action '{req.action}' queued for {item_id}",
        )


class MockSlackConnector(Connector):
    name = "slack"

    async def fetch(self) -> list[FeedItem]:
        body = "Can you review the Q2 forecast before 3 PM?"
        return [
            FeedItem(
                id="slack_1",
                source=SourceType.slack,
                account="#finance",
                kind=FeedKind.message,
                title="New Slack mention",
                body=body,
                summary=shortest_message_or_summary(body),
                received_at=datetime.now(UTC) - timedelta(minutes=2),
            )
        ]

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        return ActionResult(
            success=True,
            item_id=item_id,
            action=str(req.action),
            detail=f"Slack action '{req.action}' queued for {item_id}",
        )


class MockGooglePhotosConnector(Connector):
    name = "gphotos"

    async def fetch(self) -> list[FeedItem]:
        caption = "Photo of meal receipt from lunch with vendor."
        return [
            FeedItem(
                id="gphoto_1",
                source=SourceType.gphotos,
                account="personal@gmail.com",
                kind=FeedKind.image,
                title="New photo uploaded",
                body=caption,
                summary=shortest_message_or_summary(caption),
                preview_url="https://example.com/mock-receipt.jpg",
                received_at=datetime.now(UTC) - timedelta(minutes=1),
            )
        ]

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        return ActionResult(
            success=True,
            item_id=item_id,
            action=str(req.action),
            detail=f"Google Photos action '{req.action}' queued for {item_id}",
        )


class MockGDriveConnector(Connector):
    name = "gdrive"

    async def fetch(self) -> list[FeedItem]:
        body = "Shared file: March Tax Docs"
        return [
            FeedItem(
                id="gdrive_1",
                source=SourceType.gdrive,
                account="finance@gmail.com",
                kind=FeedKind.image,
                title="New scanned document",
                body=body,
                summary=shortest_message_or_summary(body),
                preview_url="https://example.com/mock-drive-doc.jpg",
                received_at=datetime.now(UTC) - timedelta(minutes=5),
            )
        ]

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        return ActionResult(
            success=True,
            item_id=item_id,
            action=str(req.action),
            detail=f"Google Drive action '{req.action}' queued for {item_id}",
        )
