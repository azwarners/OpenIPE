"""Immutable value contracts shared by REST and future local clients."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from openipe.core.models.goal import GoalStatus
from openipe.core.models.habit import HabitCheckInStatus, HabitFrequencyType
from openipe.core.models.inbox import InboxStatus
from openipe.core.models.project import ProjectStatus
from openipe.core.models.task import TaskPriority, TaskStatus


# Input values are deliberately separate from REST/Pydantic request models.
@dataclass(frozen=True, slots=True)
class CredentialsContract:
    username: str; password: str

@dataclass(frozen=True, slots=True)
class UserCreateContract:
    username: str; display_name: str; password: str; is_admin: bool = False

@dataclass(frozen=True, slots=True)
class UserUpdateContract:
    display_name: str | None = None; is_active: bool | None = None
    provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class ChangePasswordContract:
    current_password: str; new_password: str

@dataclass(frozen=True, slots=True)
class InboxCreateContract:
    text: str

@dataclass(frozen=True, slots=True)
class TaskCreateContract:
    title: str; description: str | None = None; project_id: int | None = None
    priority: TaskPriority = TaskPriority.NORMAL; due_date: date | None = None
    is_today: bool = False; source_inbox_item_id: int | None = None

@dataclass(frozen=True, slots=True)
class ProjectCreateContract:
    title: str; description: str | None = None; source_inbox_item_id: int | None = None

@dataclass(frozen=True, slots=True)
class HabitCreateContract:
    title: str; description: str | None = None
    frequency_type: HabitFrequencyType = HabitFrequencyType.DAILY
    frequency_config: dict[str, Any] | None = None; minimum_version: str | None = None
    source_inbox_item_id: int | None = None

@dataclass(frozen=True, slots=True)
class StackCreateContract:
    name: str; description: str | None = None

@dataclass(frozen=True, slots=True)
class TodayQueryContract:
    selected_date: date | None = None; include_completed: bool = False


@dataclass(frozen=True, slots=True)
class InitialAdminContract:
    username: str; display_name: str; password: str

@dataclass(frozen=True, slots=True)
class InboxUpdateContract:
    text: str | None = None; status: InboxStatus | None = None

@dataclass(frozen=True, slots=True)
class InboxTaskConversionContract:
    description: str | None = None; project_id: int | None = None
    priority: TaskPriority = TaskPriority.NORMAL; due_date: date | None = None; is_today: bool = False

@dataclass(frozen=True, slots=True)
class InboxHabitConversionContract:
    description: str | None = None; frequency_type: HabitFrequencyType = HabitFrequencyType.DAILY
    frequency_config: dict[str, Any] | None = None; minimum_version: str | None = None

@dataclass(frozen=True, slots=True)
class GoalCreateContract:
    title: str; description: str | None = None; target_date: date | None = None
    source_inbox_item_id: int | None = None

@dataclass(frozen=True, slots=True)
class GoalUpdateContract:
    title: str | None = None; description: str | None = None; status: GoalStatus | None = None
    target_date: date | None = None; source_inbox_item_id: int | None = None
    provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class ProjectUpdateContract:
    title: str | None = None; description: str | None = None; status: ProjectStatus | None = None
    source_inbox_item_id: int | None = None; provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class TaskUpdateContract:
    title: str | None = None; description: str | None = None; project_id: int | None = None
    status: TaskStatus | None = None; priority: TaskPriority | None = None; due_date: date | None = None
    is_today: bool | None = None; source_inbox_item_id: int | None = None
    provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class HabitUpdateContract:
    title: str | None = None; description: str | None = None
    frequency_type: HabitFrequencyType | None = None; frequency_config: dict[str, Any] | None = None
    minimum_version: str | None = None; active: bool | None = None; archived: bool | None = None
    source_inbox_item_id: int | None = None; provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class StackUpdateContract:
    name: str | None = None; description: str | None = None; active: bool | None = None
    archived: bool | None = None; provided: frozenset[str] = frozenset()

@dataclass(frozen=True, slots=True)
class ReorderContract:
    ids: tuple[int, ...]

@dataclass(frozen=True, slots=True)
class CheckInCreateContract:
    date: date; status: HabitCheckInStatus = HabitCheckInStatus.COMPLETED; note: str | None = None


@dataclass(frozen=True, slots=True)
class UserContract:
    id: int; username: str; display_name: str; is_admin: bool; is_active: bool
    created_at: datetime; updated_at: datetime; last_login_at: datetime | None

@dataclass(frozen=True, slots=True)
class LoginContract:
    access_token: str; expires_at: datetime; user: UserContract

@dataclass(frozen=True, slots=True)
class InboxContract:
    id: int; text: str; status: InboxStatus; created_at: datetime; updated_at: datetime
    processed_at: datetime | None; archived_at: datetime | None

@dataclass(frozen=True, slots=True)
class TaskContract:
    id: int; title: str; description: str | None; project_id: int | None
    status: TaskStatus; priority: TaskPriority; due_date: date | None; is_today: bool
    source_inbox_item_id: int | None; created_at: datetime; updated_at: datetime
    completed_at: datetime | None; archived_at: datetime | None

@dataclass(frozen=True, slots=True)
class ProjectContract:
    id: int; title: str; description: str | None; status: ProjectStatus
    next_action_task_id: int | None; source_inbox_item_id: int | None
    created_at: datetime; updated_at: datetime; completed_at: datetime | None
    archived_at: datetime | None; task_ids: list[int]; total_task_count: int
    completed_task_count: int; open_task_count: int

@dataclass(frozen=True, slots=True)
class GoalEvidenceContract:
    projects_total: int; projects_completed: int; tasks_total: int; tasks_completed: int
    tasks_open: int; habits_scheduled: int; habits_completed: int

@dataclass(frozen=True, slots=True)
class GoalContract:
    id: int; title: str; description: str | None; status: GoalStatus; target_date: date | None
    created_at: datetime; updated_at: datetime; achieved_at: datetime | None
    archived_at: datetime | None; source_inbox_item_id: int | None; project_ids: list[int]
    task_ids: list[int]; habit_ids: list[int]; evidence: GoalEvidenceContract

@dataclass(frozen=True, slots=True)
class HabitContract:
    id: int; title: str; description: str | None; frequency_type: HabitFrequencyType
    frequency_config: dict[str, Any]; minimum_version: str | None; stack_id: int | None
    position: int; active: bool; source_inbox_item_id: int | None; created_at: datetime
    updated_at: datetime; archived_at: datetime | None

@dataclass(frozen=True, slots=True)
class CheckInContract:
    id: int; habit_id: int; date: date; status: HabitCheckInStatus; note: str | None
    created_at: datetime; updated_at: datetime

@dataclass(frozen=True, slots=True)
class HabitStackContract:
    id: int; name: str; description: str | None; position: int; active: bool
    created_at: datetime; updated_at: datetime; archived_at: datetime | None
    completed_count: int; scheduled_count: int; habits: list[HabitContract]

@dataclass(frozen=True, slots=True)
class TodayGoalContract:
    id: int; title: str

@dataclass(frozen=True, slots=True)
class TodayProjectContract:
    id: int; title: str

@dataclass(frozen=True, slots=True)
class TodayTaskContract:
    id: int; title: str; description: str | None; project: TodayProjectContract | None
    goals: list[TodayGoalContract]; priority: TaskPriority; due_date: date | None
    is_today: bool; status: TaskStatus; overdue: bool

@dataclass(frozen=True, slots=True)
class TodayHabitContract:
    id: int; title: str; minimum_version: str | None; today_status: HabitCheckInStatus | None
    position: int; goals: list[TodayGoalContract]

@dataclass(frozen=True, slots=True)
class TodayStackContract:
    id: int; name: str; completed_count: int; scheduled_count: int
    habits: list[TodayHabitContract]

@dataclass(frozen=True, slots=True)
class TodayCompletedContract:
    tasks: list[TodayTaskContract]; habits: list[TodayHabitContract]

@dataclass(frozen=True, slots=True)
class TodayContract:
    date: date; tasks: list[TodayTaskContract]; habit_stacks: list[TodayStackContract]
    unstacked_habits: list[TodayHabitContract]; completed: TodayCompletedContract
