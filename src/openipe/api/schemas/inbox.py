"""Inbox API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from openipe.core.models.inbox import InboxStatus
from openipe.core.models.task import TaskPriority
from openipe.core.models.habit import HabitFrequencyType


class InboxCreateRequest(BaseModel):
    text: str = Field(min_length=1)


class InboxUpdateRequest(BaseModel):
    text: str | None = Field(default=None, min_length=1)
    status: InboxStatus | None = None


class InboxResponse(BaseModel):
    id: int
    text: str
    status: InboxStatus
    created_at: datetime
    updated_at: datetime
    processed_at: datetime | None
    archived_at: datetime | None


class CreateTaskFromInboxRequest(BaseModel):
    description: str | None = None
    project_id: int | None = Field(default=None, gt=0)
    priority: TaskPriority = TaskPriority.NORMAL
    due_date: date | None = None
    is_today: bool = False


class CreateProjectFromInboxRequest(BaseModel):
    description: str | None = None


class CreateHabitFromInboxRequest(BaseModel):
    description: str | None = None
    frequency_type: HabitFrequencyType = HabitFrequencyType.DAILY
    frequency_config: dict[str, Any] = Field(default_factory=dict)
    minimum_version: str | None = None
