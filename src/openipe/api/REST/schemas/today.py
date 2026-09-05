"""Today API schemas."""

from datetime import date

from pydantic import BaseModel

from openipe.api.internal.contracts import TaskPriority, TaskStatus, HabitCheckInStatus


class TodayGoalSummary(BaseModel):
    id: int
    title: str


class TodayProjectSummary(BaseModel):
    id: int
    title: str


class TodayTask(BaseModel):
    id: int
    title: str
    description: str | None
    project: TodayProjectSummary | None
    goals: list[TodayGoalSummary]
    priority: TaskPriority
    due_date: date | None
    is_today: bool
    status: TaskStatus
    overdue: bool


class TodayHabit(BaseModel):
    id: int
    title: str
    minimum_version: str | None
    today_status: HabitCheckInStatus | None
    position: int
    goals: list[TodayGoalSummary]


class TodayHabitStack(BaseModel):
    id: int
    name: str
    completed_count: int
    scheduled_count: int
    habits: list[TodayHabit]


class TodayCompleted(BaseModel):
    tasks: list[TodayTask]
    habits: list[TodayHabit]


class TodayResponse(BaseModel):
    date: date
    tasks: list[TodayTask]
    habit_stacks: list[TodayHabitStack]
    unstacked_habits: list[TodayHabit]
    completed: TodayCompleted
