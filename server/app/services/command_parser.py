from __future__ import annotations

import re

from app.models.schemas import VoiceCommandResponse


def parse_voice_command(transcript: str) -> VoiceCommandResponse:
    lower = transcript.lower().strip()
    item_match = re.search(r"(?:id|item)\s+([a-z0-9_\-]+)", lower)
    item_id = item_match.group(1) if item_match else None

    if "mark" in lower and "spam" in lower:
        return VoiceCommandResponse(command="mark_spam", item_id=item_id, confidence=0.89)
    if "archive" in lower:
        return VoiceCommandResponse(command="archive", item_id=item_id, confidence=0.88)
    if "forward" in lower and "ramp" in lower:
        return VoiceCommandResponse(
            command="forward_to_ramp",
            item_id=item_id,
            target="receipts@ramp.com",
            confidence=0.92,
        )
    if "move" in lower and "account" in lower:
        acct_match = re.search(r"account\s+([\w.+\-]+@[\w\-.]+)", lower)
        return VoiceCommandResponse(
            command="move_account",
            item_id=item_id,
            target=acct_match.group(1) if acct_match else None,
            confidence=0.84,
        )
    if "forward" in lower:
        target_match = re.search(r"to\s+([\w.+\-]+@[\w\-.]+)", lower)
        return VoiceCommandResponse(
            command="forward",
            item_id=item_id,
            target=target_match.group(1) if target_match else None,
            confidence=0.85,
        )
    if "reply" in lower:
        body = transcript.split("reply", 1)[-1].strip() if "reply" in transcript.lower() else None
        return VoiceCommandResponse(command="reply", item_id=item_id, body=body or None, confidence=0.82)

    return VoiceCommandResponse(command="unknown", confidence=0.2)
