"""Project domain model."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Project:
    id: int
    user_id: int
    title: str
    description: str | None
    status: ProjectStatus
    next_action_task_id: int | None
    source_inbox_item_id: int | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
