from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

from app.connectors.base import Connector
from app.models.schemas import ActionRequest, ActionResult, FeedItem, FeedKind, SourceType
from app.services.summarizer import shortest_message_or_summary

try:
    from slack_sdk import WebClient
except Exception:  # pragma: no cover
    WebClient = None


class SlackConnector(Connector):
    name = "slack"

    def __init__(self, bot_token: str, channel_ids: list[str], max_messages: int = 10) -> None:
        self.bot_token = bot_token
        self.channel_ids = channel_ids
        self.max_messages = max_messages
        self.client = WebClient(token=bot_token) if WebClient else None

    @classmethod
    def from_env(cls) -> "SlackConnector | None":
        token = os.getenv("SLACK_BOT_TOKEN", "").strip()
        channels = [c.strip() for c in os.getenv("SLACK_CHANNEL_IDS", "").split(",") if c.strip()]
        if not token or not channels:
            return None
        return cls(token, channels, int(os.getenv("SLACK_MAX_MESSAGES", "10")))

    async def fetch(self) -> list[FeedItem]:
        if not self.client:
            return []

        tasks = [asyncio.to_thread(self._fetch_channel, channel) for channel in self.channel_ids]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[FeedItem] = []
        for batch in batches:
            if isinstance(batch, list):
                items.extend(batch)
        return items

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        if not self.client:
            return ActionResult(
                success=False,
                item_id=item_id,
                action=str(req.action),
                detail="slack-sdk is not installed",
            )

        try:
            channel, ts = self._parse_item_id(item_id)
            await asyncio.to_thread(self._run_action, channel, ts, req)
            return ActionResult(
                success=True,
                item_id=item_id,
                action=str(req.action),
                detail=f"Slack action '{req.action}' executed",
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                item_id=item_id,
                action=str(req.action),
                detail=f"Slack action error: {exc}",
            )

    def _fetch_channel(self, channel_id: str) -> list[FeedItem]:
        assert self.client is not None
        resp = self.client.conversations_history(channel=channel_id, limit=self.max_messages)
        messages = resp.get("messages", [])

        result: list[FeedItem] = []
        for msg in messages:
            text = (msg.get("text") or "").strip()
            ts = msg.get("ts")
            if not ts or not text:
                continue
            received = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            result.append(
                FeedItem(
                    id=f"slack_{channel_id}|{ts}",
                    source=SourceType.slack,
                    account=channel_id,
                    kind=FeedKind.message,
                    title="New Slack message",
                    body=text,
                    summary=shortest_message_or_summary(text),
                    received_at=received,
                )
            )
        return result

    def _run_action(self, channel: str, ts: str, req: ActionRequest) -> None:
        assert self.client is not None
        action = str(req.action)

        if action == "reply":
            if not req.body:
                raise ValueError("reply body is required")
            self.client.chat_postMessage(channel=channel, thread_ts=ts, text=req.body)
            return

        if action == "forward":
            if not req.target:
                raise ValueError("forward target is required")
            permalink = self.client.chat_getPermalink(channel=channel, message_ts=ts).get("permalink", "")
            self.client.chat_postMessage(channel=req.target, text=f"Forwarded message: {permalink}")
            return

        if action == "mark_spam":
            self.client.chat_postMessage(channel=channel, thread_ts=ts, text=":warning: Marked as spam")
            return

        if action == "archive":
            self.client.chat_postMessage(channel=channel, thread_ts=ts, text=":file_cabinet: Archived")
            return

        raise ValueError(f"Unsupported action for slack: {action}")

    @staticmethod
    def _parse_item_id(item_id: str) -> tuple[str, str]:
        raw = item_id.split("slack_", 1)[-1]
        parts = raw.split("|", 1)
        if len(parts) != 2:
            raise ValueError("Invalid Slack item id")
        return parts[0], parts[1]
