"""Goal domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    ACHIEVED = "achieved"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Goal:
    id: int
    user_id: int
    title: str
    description: str | None
    status: GoalStatus
    target_date: date | None
    created_at: datetime
    updated_at: datetime
    achieved_at: datetime | None
    archived_at: datetime | None
    source_inbox_item_id: int | None
