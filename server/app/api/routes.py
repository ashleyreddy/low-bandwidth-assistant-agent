from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import (
    ActionRequest,
    ActionResult,
    ConnectorStatus,
    FeedResponse,
    VoiceCommandRequest,
    VoiceCommandResponse,
)
from app.services.command_parser import parse_voice_command
from app.services.feed_service import FeedService

router = APIRouter(prefix="/v1", tags=["assistant"])
service = FeedService()


@router.get("/feed", response_model=FeedResponse)
async def get_feed() -> FeedResponse:
    return await service.fetch_feed()


@router.get("/connectors", response_model=list[ConnectorStatus])
async def get_connectors() -> list[ConnectorStatus]:
    return service.connector_status()


@router.post("/items/{item_id}/action", response_model=ActionResult)
async def action_item(item_id: str, req: ActionRequest) -> ActionResult:
    return await service.dispatch_action(item_id, req)


@router.post("/voice/command", response_model=VoiceCommandResponse)
async def parse_command(req: VoiceCommandRequest) -> VoiceCommandResponse:
    return parse_voice_command(req.transcript)
