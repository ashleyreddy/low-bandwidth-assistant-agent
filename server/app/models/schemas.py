from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    gmail = "gmail"
    slack = "slack"
    gdrive = "gdrive"
    gphotos = "gphotos"


class FeedKind(str, Enum):
    message = "message"
    image = "image"


class FeedItem(BaseModel):
    id: str
    source: SourceType
    account: str
    kind: FeedKind
    title: str
    body: str = ""
    summary: str
    preview_url: str | None = None
    received_at: datetime


class FeedResponse(BaseModel):
    items: list[FeedItem]


class MessageAction(str, Enum):
    reply = "reply"
    forward = "forward"
    mark_spam = "mark_spam"
    archive = "archive"


class ImageAction(str, Enum):
    forward_to_ramp = "forward_to_ramp"
    move_account = "move_account"


class ActionRequest(BaseModel):
    action: MessageAction | ImageAction
    target: str | None = Field(default=None, description="recipient/account depending on action")
    body: str | None = Field(default=None, description="reply content when action=reply")


class ActionResult(BaseModel):
    success: bool
    item_id: str
    action: str
    detail: str


class VoiceCommandRequest(BaseModel):
    transcript: str


class VoiceCommandResponse(BaseModel):
    command: Literal["reply", "forward", "mark_spam", "archive", "forward_to_ramp", "move_account", "unknown"]
    item_id: str | None = None
    target: str | None = None
    body: str | None = None
    confidence: float
