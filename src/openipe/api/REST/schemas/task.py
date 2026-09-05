"""Task API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from openipe.api.internal.contracts import TaskPriority, TaskStatus


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    project_id: int | None = Field(default=None, gt=0)
    priority: TaskPriority = TaskPriority.NORMAL
    due_date: date | None = None
    is_today: bool = False
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    project_id: int | None = Field(default=None, gt=0)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: date | None = None
    is_today: bool | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    project_id: int | None
    status: TaskStatus
    priority: TaskPriority
    due_date: date | None
    is_today: bool
    source_inbox_item_id: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
