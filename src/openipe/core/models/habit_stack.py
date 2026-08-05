"""Habit stack domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class HabitStack:
    id: int
    user_id: int
    name: str
    description: str | None
    position: int
    active: bool
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
