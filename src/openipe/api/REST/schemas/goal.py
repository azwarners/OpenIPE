"""Goal API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from openipe.api.internal.contracts import GoalStatus


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    target_date: date | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class GoalUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    status: GoalStatus | None = None
    target_date: date | None = None
    source_inbox_item_id: int | None = Field(default=None, gt=0)


class GoalResponse(BaseModel):
    id: int
    title: str
    description: str | None
    status: GoalStatus
    target_date: date | None
    created_at: datetime
    updated_at: datetime
    achieved_at: datetime | None
    archived_at: datetime | None
    source_inbox_item_id: int | None
    project_ids: list[int]
    task_ids: list[int]
    habit_ids: list[int]
    evidence: "GoalEvidence"


class GoalEvidence(BaseModel):
    projects_total: int
    projects_completed: int
    tasks_total: int
    tasks_completed: int
    tasks_open: int
    habits_scheduled: int
    habits_completed: int


GoalResponse.model_rebuild()
