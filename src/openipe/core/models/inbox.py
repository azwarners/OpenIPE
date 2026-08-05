"""Inbox idea-capture domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class InboxStatus(StrEnum):
    UNPROCESSED = "unprocessed"
    PROCESSED = "processed"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


@dataclass(frozen=True, slots=True)
class InboxItem:
    id: int
    user_id: int
    text: str
    status: InboxStatus
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
    archived_at: datetime | None
