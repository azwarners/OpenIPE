"""Today dashboard aggregation service."""

from __future__ import annotations

from datetime import date
import sqlite3

from openipe.core.models.task import TaskStatus
from openipe.persistence.repositories.goal_association_repository import GoalAssociationRepository
from openipe.persistence.repositories.goal_repository import GoalRepository
from openipe.persistence.repositories.habit_repository import HabitCheckInRepository, HabitRepository
from openipe.persistence.repositories.habit_stack_repository import HabitStackRepository
from openipe.persistence.repositories.project_repository import ProjectRepository
from openipe.persistence.repositories.task_repository import TaskRepository
from openipe.application.habit_service import HabitService


class TodayService:
    def __init__(self, connection: sqlite3.Connection):
        self.tasks = TaskRepository(connection)
        self.projects = ProjectRepository(connection)
        self.habits = HabitRepository(connection)
        self.checkins = HabitCheckInRepository(connection)
        self.stacks = HabitStackRepository(connection)
        self.habit_service = HabitService(connection)
        self.goals = GoalRepository(connection)
        self.associations = GoalAssociationRepository(connection)

    def get(self, user_id: int, selected_date: date | None = None, include_completed: bool = False) -> dict:
        selected_date = selected_date or date.today()
        task_records = self.tasks.list(user_id)
        active_tasks = [task for task in task_records if task.status == TaskStatus.OPEN and _task_selected(task, selected_date)]
        completed_tasks = [
            task for task in task_records
            if include_completed and task.status == TaskStatus.COMPLETED and _task_selected(task, selected_date)
        ]
        stacks = []
        for stack in self.stacks.list(user_id, active=True):
            habits = self.habits.list_by_stack(user_id, stack.id)
            scheduled = [habit for habit in habits if self.habit_service.is_scheduled(user_id, habit, selected_date)]
            if not scheduled:
                continue
            stacks.append(self._stack_payload(user_id, stack, scheduled, selected_date))
        unstacked = [
            habit for habit in self.habits.list(user_id, active=True)
            if habit.stack_id is None and self.habit_service.is_scheduled(user_id, habit, selected_date)
        ]
        completed_habits = []
        if include_completed:
            for habit in self.habits.list(user_id, active=True):
                checkin = self.checkins.get(user_id, habit.id, selected_date)
                if checkin is not None and checkin.status.value == "completed":
                    completed_habits.append(self._habit_payload(user_id, habit, checkin.status.value, selected_date))
        return {
            "date": selected_date,
            "tasks": [self._task_payload(user_id, task, selected_date) for task in active_tasks],
            "habit_stacks": stacks,
            "unstacked_habits": [self._habit_payload(user_id, habit, selected_date=selected_date) for habit in unstacked],
            "completed": {
                "tasks": [self._task_payload(user_id, task, selected_date) for task in completed_tasks],
                "habits": completed_habits,
            },
        }

    def _task_payload(self, user_id, task, selected_date):
        project = self.projects.get(user_id, task.project_id) if task.project_id else None
        return {
            "id": task.id, "title": task.title, "description": task.description,
            "project": {"id": project.id, "title": project.title} if project else None,
            "goals": self._goal_payloads(user_id, "task", task.id), "priority": task.priority,
            "due_date": task.due_date, "is_today": task.is_today, "status": task.status,
            "overdue": task.due_date is not None and task.due_date < selected_date,
        }

    def _stack_payload(self, user_id, stack, habits, selected_date):
        payloads = [self._habit_payload(user_id, habit, selected_date=selected_date) for habit in habits]
        completed = sum(item["today_status"] == "completed" for item in payloads)
        return {"id": stack.id, "name": stack.name, "completed_count": completed,
                "scheduled_count": len(habits), "habits": payloads}

    def _habit_payload(self, user_id, habit, status=None, selected_date=None):
        selected_date = selected_date or date.today()
        checkin = self.checkins.get(user_id, habit.id, selected_date)
        return {
            "id": habit.id, "title": habit.title, "minimum_version": habit.minimum_version,
            "today_status": status or (checkin.status if checkin else None), "position": habit.position,
            "goals": self._goal_payloads(user_id, "habit", habit.id),
        }

    def _goal_payloads(self, user_id, kind, related_id):
        payloads = []
        for goal_id in self.associations.goal_ids_for_related(kind, related_id):
            goal = self.goals.get(user_id, goal_id)
            if goal is not None:
                payloads.append({"id": goal_id, "title": goal.title})
        return payloads


def _task_selected(task, selected_date):
    return task.is_today or (task.due_date is not None and task.due_date <= selected_date)
