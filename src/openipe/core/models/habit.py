"""Habit and habit check-in domain models."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class HabitFrequencyType(StrEnum):
    DAILY = "daily"
    WEEKDAYS = "weekdays"
    SELECTED_DAYS = "selected_days"
    TIMES_PER_WEEK = "times_per_week"


class HabitCheckInStatus(StrEnum):
    COMPLETED = "completed"
    SKIPPED = "skipped"
    NOT_DONE = "not_done"


@dataclass(frozen=True, slots=True)
class Habit:
    id: int
    user_id: int
    title: str
    description: str | None
    frequency_type: HabitFrequencyType
    frequency_config: dict
    minimum_version: str | None
    stack_id: int | None
    position: int
    active: bool
    source_inbox_item_id: int | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


@dataclass(frozen=True, slots=True)
class HabitCheckIn:
    id: int
    user_id: int
    habit_id: int
    date: date
    status: HabitCheckInStatus
    note: str | None
    created_at: datetime
    updated_at: datetime
