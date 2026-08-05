"""Goal lifecycle application service."""

from __future__ import annotations

import sqlite3
from datetime import UTC, date, datetime, timedelta

from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.goal import Goal, GoalStatus
from openipe.core.models.habit import HabitCheckInStatus
from openipe.persistence.repositories.goal_association_repository import GoalAssociationRepository
from openipe.persistence.repositories.goal_repository import GoalRepository
from openipe.persistence.repositories.habit_repository import HabitRepository
from openipe.persistence.repositories.inbox_repository import InboxRepository
from openipe.persistence.repositories.project_repository import ProjectRepository
from openipe.persistence.repositories.task_repository import TaskRepository
from openipe.application.habit_service import HabitService

UNSET = object()


class GoalService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = GoalRepository(connection)
        self.inbox = InboxRepository(connection)
        self.associations = GoalAssociationRepository(connection)
        self.projects = ProjectRepository(connection)
        self.tasks = TaskRepository(connection)
        self.habits = HabitRepository(connection)
        self.habit_service = HabitService(connection)

    def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        target_date: date | None = None,
        source_inbox_item_id: int | None = None,
    ) -> Goal:
        if source_inbox_item_id is not None and self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        return self.repository.create(
            user_id,
            _validate_title(title),
            _normalize_description(description),
            target_date,
            source_inbox_item_id,
        )

    def list(self, user_id: int, status: GoalStatus | None = None) -> list[Goal]:
        return self.repository.list(user_id, status)

    def get(self, user_id: int, goal_id: int) -> Goal:
        goal = self.repository.get(user_id, goal_id)
        if goal is None:
            raise NotFoundError("Goal not found")
        return goal

    def update(
        self,
        user_id: int,
        goal_id: int,
        title: str | None | object = UNSET,
        description: str | None | object = UNSET,
        status: GoalStatus | None | object = UNSET,
        target_date: date | None | object = UNSET,
        source_inbox_item_id: int | None | object = UNSET,
    ) -> Goal:
        goal = self.get(user_id, goal_id)
        if (
            source_inbox_item_id is not UNSET
            and source_inbox_item_id is not None
            and self.inbox.get(user_id, source_inbox_item_id) is None
        ):
            raise NotFoundError("Source inbox item not found")
        new_status = status if status is not UNSET and status is not None else goal.status
        if not isinstance(new_status, GoalStatus):
            raise ValidationError("Invalid goal status")
        self._validate_transition(goal.status, new_status)
        achieved_at = goal.achieved_at
        archived_at = goal.archived_at
        now = datetime.now(UTC)
        if new_status == GoalStatus.ACHIEVED:
            achieved_at = achieved_at or now
        elif new_status in {GoalStatus.ACTIVE, GoalStatus.PAUSED, GoalStatus.ABANDONED}:
            achieved_at = None
        if new_status == GoalStatus.ARCHIVED:
            archived_at = archived_at or now
        return self.repository.update(
            user_id,
            goal_id,
            _validate_title(title) if title is not UNSET and title is not None else goal.title,
            _normalize_description(description) if description is not UNSET else goal.description,
            new_status,
            target_date if target_date is not UNSET else goal.target_date,
            achieved_at,
            archived_at,
            source_inbox_item_id
            if source_inbox_item_id is not UNSET
            else goal.source_inbox_item_id,
        )

    def pause(self, user_id: int, goal_id: int) -> Goal:
        return self.update(user_id, goal_id, status=GoalStatus.PAUSED)

    def resume(self, user_id: int, goal_id: int) -> Goal:
        return self.update(user_id, goal_id, status=GoalStatus.ACTIVE)

    def achieve(self, user_id: int, goal_id: int) -> Goal:
        return self.update(user_id, goal_id, status=GoalStatus.ACHIEVED)

    def abandon(self, user_id: int, goal_id: int) -> Goal:
        return self.update(user_id, goal_id, status=GoalStatus.ABANDONED)

    def archive(self, user_id: int, goal_id: int) -> Goal:
        return self.update(user_id, goal_id, status=GoalStatus.ARCHIVED)

    def associate_project(self, user_id: int, goal_id: int, project_id: int) -> Goal:
        self._associate(user_id, goal_id, project_id, "project")
        return self.get(user_id, goal_id)

    def associate_task(self, user_id: int, goal_id: int, task_id: int) -> Goal:
        self._associate(user_id, goal_id, task_id, "task")
        return self.get(user_id, goal_id)

    def associate_habit(self, user_id: int, goal_id: int, habit_id: int) -> Goal:
        self._associate(user_id, goal_id, habit_id, "habit")
        return self.get(user_id, goal_id)

    def remove_association(self, user_id: int, goal_id: int, related_id: int, kind: str) -> None:
        self.get(user_id, goal_id)
        self._get_related(user_id, related_id, kind)
        self.associations.remove(kind, goal_id, related_id)

    def associated_ids(self, user_id: int, goal_id: int) -> dict[str, list[int]]:
        self.get(user_id, goal_id)
        return {
            "project_ids": self.associations.ids("project", goal_id),
            "task_ids": self.associations.ids("task", goal_id),
            "habit_ids": self.associations.ids("habit", goal_id),
        }

    def evidence(self, user_id: int, goal_id: int, selected_date: date | None = None) -> dict[str, int]:
        ids = self.associated_ids(user_id, goal_id)
        project_records = [self.projects.get(user_id, item_id) for item_id in ids["project_ids"]]
        task_records = [self.tasks.get(user_id, item_id) for item_id in ids["task_ids"]]
        habit_records = [self.habits.get(user_id, item_id) for item_id in ids["habit_ids"]]
        selected_date = selected_date or date.today()
        scheduled = completed = 0
        start = selected_date - timedelta(days=selected_date.weekday())
        for habit in habit_records:
            if habit is None:
                continue
            current = start
            while current <= selected_date:
                if self.habit_service.is_scheduled(user_id, habit, current):
                    scheduled += 1
                    checkin = self.habit_service.get_check_in(user_id, habit.id, current)
                    if checkin is not None and checkin.status == HabitCheckInStatus.COMPLETED:
                        completed += 1
                current += timedelta(days=1)
        return {
            "projects_total": len([item for item in project_records if item is not None]),
            "projects_completed": len([item for item in project_records if item is not None and item.status.value == "completed"]),
            "tasks_total": len([item for item in task_records if item is not None]),
            "tasks_completed": len([item for item in task_records if item is not None and item.status.value == "completed"]),
            "tasks_open": len([item for item in task_records if item is not None and item.status.value == "open"]),
            "habits_scheduled": scheduled,
            "habits_completed": completed,
        }

    def _associate(self, user_id: int, goal_id: int, related_id: int, kind: str) -> None:
        self.get(user_id, goal_id)
        self._get_related(user_id, related_id, kind)
        self.associations.add(kind, goal_id, related_id)

    def _get_related(self, user_id: int, related_id: int, kind: str):
        repository = {"project": self.projects, "task": self.tasks, "habit": self.habits}[kind]
        if repository.get(user_id, related_id) is None:
            raise NotFoundError(f"{kind.title()} not found")

    @staticmethod
    def _validate_transition(current: GoalStatus, new: GoalStatus) -> None:
        if current == GoalStatus.ARCHIVED and new != GoalStatus.ARCHIVED:
            raise ValidationError("Archived goals cannot be resumed or changed")
        if new == GoalStatus.PAUSED and current != GoalStatus.ACTIVE:
            raise ValidationError("Only active goals can be paused")
        if new == GoalStatus.ACTIVE and current not in {GoalStatus.ACTIVE, GoalStatus.PAUSED}:
            raise ValidationError("Only paused goals can be resumed")
        if new in {GoalStatus.ACHIEVED, GoalStatus.ABANDONED} and current not in {
            GoalStatus.ACTIVE,
            GoalStatus.PAUSED,
        }:
            raise ValidationError("Only active or paused goals can change lifecycle state")


def _validate_title(title: str) -> str:
    normalized = title.strip()
    if not normalized:
        raise ValidationError("Goal title must not be empty")
    return normalized


def _normalize_description(description: str | None) -> str | None:
    if description is None:
        return None
    normalized = description.strip()
    return normalized or None
