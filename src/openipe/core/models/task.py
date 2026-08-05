"""Task domain model."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


class TaskStatus(StrEnum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class TaskPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    user_id: int
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
