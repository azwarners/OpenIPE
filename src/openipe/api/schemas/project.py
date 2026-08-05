"""Project API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from openipe.core.models.project import ProjectStatus


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class ProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: ProjectStatus | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: ProjectStatus
    next_action_task_id: int | None
    source_inbox_item_id: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
    task_ids: list[int]
    total_task_count: int
    completed_task_count: int
    open_task_count: int
