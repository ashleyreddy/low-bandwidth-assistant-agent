from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.schemas import ActionRequest, ActionResult, FeedItem


class Connector(ABC):
    name: str

    @abstractmethod
    async def fetch(self) -> list[FeedItem]:
        raise NotImplementedError

    @abstractmethod
    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        raise NotImplementedError
