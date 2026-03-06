from __future__ import annotations

import os


def summarize(text: str, max_chars: int) -> str:
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "..."


def shortest_message_or_summary(text: str) -> str:
    max_chars = int(os.getenv("SUMMARY_MAX_CHARS", "220"))
    summary = summarize(text, max_chars)
    return text if len(text) <= len(summary) else summary
