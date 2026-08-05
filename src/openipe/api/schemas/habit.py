"""Habit and check-in API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from openipe.core.models.habit import HabitCheckInStatus, HabitFrequencyType


class HabitCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    frequency_type: HabitFrequencyType = HabitFrequencyType.DAILY
    frequency_config: dict[str, Any] = Field(default_factory=dict)
    minimum_version: str | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class HabitUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    frequency_type: HabitFrequencyType | None = None
    frequency_config: dict[str, Any] | None = None
    minimum_version: str | None = None
    active: bool | None = None
    archived: bool | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class HabitResponse(BaseModel):
    id: int
    title: str
    description: str | None
    frequency_type: HabitFrequencyType
    frequency_config: dict[str, Any]
    minimum_version: str | None
    stack_id: int | None
    position: int
    active: bool
    source_inbox_item_id: int | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class HabitCheckInRequest(BaseModel):
    date: date
    status: HabitCheckInStatus = HabitCheckInStatus.COMPLETED
    note: str | None = None


class HabitCheckInResponse(BaseModel):
    id: int
    habit_id: int
    date: date
    status: HabitCheckInStatus
    note: str | None
    created_at: datetime
    updated_at: datetime
