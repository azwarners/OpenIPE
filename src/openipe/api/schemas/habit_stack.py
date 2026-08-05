"""Habit stack API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from .habit import HabitResponse


class HabitStackCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class HabitStackUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    active: bool | None = None
    archived: bool | None = None


class ReorderRequest(BaseModel):
    ids: list[int]


class HabitStackResponse(BaseModel):
    id: int
    name: str
    description: str | None
    position: int
    active: bool
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    completed_count: int
    scheduled_count: int
    habits: list[HabitResponse]
