from __future__ import annotations

import asyncio
import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from app.connectors.base import Connector
from app.models.schemas import ActionRequest, ActionResult, FeedItem, FeedKind, SourceType
from app.services.summarizer import shortest_message_or_summary

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except Exception:  # pragma: no cover
    Request = None
    Credentials = None
    build = None


@dataclass
class GmailAccountConfig:
    account: str
    client_id: str
    client_secret: str
    refresh_token: str


class GmailConnector(Connector):
    name = "gmail"

    def __init__(self, accounts: list[GmailAccountConfig], max_results: int = 10) -> None:
        self.accounts = accounts
        self.max_results = max_results

    @classmethod
    def from_env(cls) -> "GmailConnector | None":
        raw = os.getenv("GMAIL_ACCOUNTS_JSON", "").strip()
        if not raw:
            return None

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None

        accounts: list[GmailAccountConfig] = []
        for entry in parsed if isinstance(parsed, list) else []:
            if not isinstance(entry, dict):
                continue
            if not all(entry.get(k) for k in ("account", "client_id", "client_secret", "refresh_token")):
                continue
            accounts.append(
                GmailAccountConfig(
                    account=str(entry["account"]),
                    client_id=str(entry["client_id"]),
                    client_secret=str(entry["client_secret"]),
                    refresh_token=str(entry["refresh_token"]),
                )
            )

        if not accounts:
            return None
        return cls(accounts=accounts, max_results=int(os.getenv("GMAIL_MAX_RESULTS", "10")))

    async def fetch(self) -> list[FeedItem]:
        if not (Credentials and build and Request):
            return []

        tasks = [asyncio.to_thread(self._fetch_account_messages, account) for account in self.accounts]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        items: list[FeedItem] = []
        for batch in batches:
            if isinstance(batch, list):
                items.extend(batch)
        return items

    async def act(self, item_id: str, req: ActionRequest) -> ActionResult:
        if not (Credentials and build and Request):
            return ActionResult(
                success=False,
                item_id=item_id,
                action=str(req.action),
                detail="google-api-python-client/google-auth is not installed",
            )

        gmail_id = item_id.split("gmail_", 1)[-1]
        account, message_id = self._split_item_id(gmail_id)
        account_cfg = next((a for a in self.accounts if a.account == account), None)
        if not account_cfg:
            return ActionResult(success=False, item_id=item_id, action=str(req.action), detail="Unknown Gmail account")

        try:
            await asyncio.to_thread(self._run_action, account_cfg, message_id, req)
            return ActionResult(
                success=True,
                item_id=item_id,
                action=str(req.action),
                detail=f"Gmail action '{req.action}' executed for {account}",
            )
        except Exception as exc:
            return ActionResult(success=False, item_id=item_id, action=str(req.action), detail=f"Gmail action error: {exc}")

    def _service_for_account(self, account: GmailAccountConfig):
        creds = Credentials(
            token=None,
            refresh_token=account.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=account.client_id,
            client_secret=account.client_secret,
            scopes=["https://www.googleapis.com/auth/gmail.modify"],
        )
        creds.refresh(Request())
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def _fetch_account_messages(self, account: GmailAccountConfig) -> list[FeedItem]:
        service = self._service_for_account(account)
        listing = (
            service.users()
            .messages()
            .list(userId="me", maxResults=self.max_results, q="in:inbox -category:promotions")
            .execute()
        )

        result: list[FeedItem] = []
        for message in listing.get("messages", []):
            msg_id = message.get("id")
            if not msg_id:
                continue
            payload = (
                service.users()
                .messages()
                .get(userId="me", id=msg_id, format="full", metadataHeaders=["Subject", "From", "Date"])
                .execute()
            )
            headers = {h.get("name", ""): h.get("value", "") for h in payload.get("payload", {}).get("headers", [])}
            subject = headers.get("Subject") or "(No subject)"
            body = self._extract_body(payload.get("payload", {}))
            received = self._received_at(headers.get("Date"))
            raw_id = f"{account.account}|{msg_id}"

            result.append(
                FeedItem(
                    id=f"gmail_{raw_id}",
                    source=SourceType.gmail,
                    account=account.account,
                    kind=FeedKind.message,
                    title=subject,
                    body=body,
                    summary=shortest_message_or_summary(body or subject),
                    received_at=received,
                )
            )

        return result

    def _run_action(self, account: GmailAccountConfig, message_id: str, req: ActionRequest) -> None:
        service = self._service_for_account(account)
        users = service.users().messages()

        action = str(req.action)
        if action == "reply":
            if not req.body:
                raise ValueError("reply body is required")
            original = users.get(userId="me", id=message_id, format="metadata", metadataHeaders=["Subject", "From"]).execute()
            headers = {h.get("name", ""): h.get("value", "") for h in original.get("payload", {}).get("headers", [])}
            to_addr = headers.get("From", "")
            subject = headers.get("Subject", "")
            reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}" if subject else "Re:"
            raw = (
                f"To: {to_addr}\r\n"
                f"Subject: {reply_subject}\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n\r\n"
                f"{req.body}"
            )
            encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
            service.users().messages().send(userId="me", body={"raw": encoded}).execute()
            return

        if action == "forward":
            if not req.target:
                raise ValueError("forward target is required")
            original = users.get(userId="me", id=message_id, format="full").execute()
            subject = self._header_map(original).get("Subject", "")
            body = self._extract_body(original.get("payload", {}))
            fwd_subject = f"Fwd: {subject}" if subject else "Fwd:"
            raw = (
                f"To: {req.target}\r\n"
                f"Subject: {fwd_subject}\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n\r\n"
                f"{body}"
            )
            encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")
            users.send(userId="me", body={"raw": encoded}).execute()
            return

        if action == "mark_spam":
            users.modify(userId="me", id=message_id, body={"addLabelIds": ["SPAM"], "removeLabelIds": ["INBOX"]}).execute()
            return

        if action == "archive":
            users.modify(userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}).execute()
            return

        raise ValueError(f"Unsupported action for gmail: {action}")

    @staticmethod
    def _split_item_id(raw: str) -> tuple[str, str]:
        parts = raw.split("|", 1)
        if len(parts) != 2:
            raise ValueError("Invalid Gmail item id")
        return parts[0], parts[1]

    @staticmethod
    def _header_map(payload: dict[str, Any]) -> dict[str, str]:
        return {h.get("name", ""): h.get("value", "") for h in payload.get("payload", {}).get("headers", [])}

    @staticmethod
    def _received_at(date_header: str | None) -> datetime:
        if not date_header:
            return datetime.now(timezone.utc)
        try:
            dt = parsedate_to_datetime(date_header)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return datetime.now(timezone.utc)

    @classmethod
    def _extract_body(cls, payload: dict[str, Any]) -> str:
        data = payload.get("body", {}).get("data")
        if data:
            return cls._decode(data)

        for part in payload.get("parts", []) or []:
            mime = part.get("mimeType", "")
            if mime == "text/plain" and part.get("body", {}).get("data"):
                return cls._decode(part["body"]["data"])
            if part.get("parts"):
                nested = cls._extract_body(part)
                if nested:
                    return nested
        return ""

    @staticmethod
    def _decode(data: str) -> str:
        # Gmail API body is base64url encoded and may be missing padding.
        padded = data + "=" * (-len(data) % 4)
        try:
            return base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8", errors="replace")
        except Exception:
            return ""
