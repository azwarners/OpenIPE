"""Habit stack organization and progress service."""

from __future__ import annotations

from datetime import date, datetime, UTC
import sqlite3

from openipe.application.habit_service import HabitService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.habit_stack import HabitStack
from openipe.persistence.repositories.habit_repository import HabitRepository
from openipe.persistence.repositories.habit_stack_repository import HabitStackRepository

UNSET = object()


class HabitStackService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = HabitStackRepository(connection)
        self.habits = HabitRepository(connection)
        self.habit_service = HabitService(connection)

    def create(self, user_id, name, description=None) -> HabitStack:
        return self.repository.create(user_id, _name(name), _description(description))

    def list(self, user_id, active=None) -> list[HabitStack]:
        return self.repository.list(user_id, active)

    def get(self, user_id, stack_id) -> HabitStack:
        stack = self.repository.get(user_id, stack_id)
        if stack is None:
            raise NotFoundError("Habit stack not found")
        return stack

    def update(self, user_id, stack_id, name=UNSET, description=UNSET, active=UNSET) -> HabitStack:
        stack = self.get(user_id, stack_id)
        if stack.archived_at is not None and active is not UNSET and active:
            raise ValidationError("Archived habit stacks cannot be activated")
        return self.repository.update(
            user_id, stack_id,
            _name(name) if name is not UNSET and name is not None else stack.name,
            _description(description) if description is not UNSET else stack.description,
            bool(active) if active is not UNSET else stack.active,
            stack.archived_at,
        )

    def archive(self, user_id, stack_id) -> HabitStack:
        stack = self.get(user_id, stack_id)
        if stack.archived_at is not None:
            return stack
        return self.repository.update(user_id, stack_id, stack.name, stack.description, False, datetime.now(UTC))

    def add_habit(self, user_id, stack_id, habit_id):
        stack = self.get(user_id, stack_id)
        habit = self.habit_service.get(user_id, habit_id)
        if not stack.active or stack.archived_at is not None:
            raise ValidationError("Inactive habit stacks cannot receive habits")
        position = self.habits.max_position_in_stack(user_id, stack_id) + 1
        return self.habits.set_stack(user_id, habit.id, stack.id, position)

    def remove_habit(self, user_id, stack_id, habit_id):
        self.get(user_id, stack_id)
        habit = self.habit_service.get(user_id, habit_id)
        if habit.stack_id != stack_id:
            raise ValidationError("Habit does not belong to the stack")
        return self.habits.set_stack(user_id, habit_id, None, 0)

    def reorder_stacks(self, user_id, stack_ids: list[int]) -> None:
        stacks = self.repository.list(user_id, active=True)
        _require_exact_ids([stack.id for stack in stacks], stack_ids, "stacks")
        self.repository.reorder(user_id, stack_ids)

    def reorder_habits(self, user_id, stack_id, habit_ids: list[int]) -> None:
        self.get(user_id, stack_id)
        habits = self.habits.list_by_stack(user_id, stack_id)
        _require_exact_ids([habit.id for habit in habits], habit_ids, "habits")
        self.habits.reorder_in_stack(user_id, stack_id, habit_ids)

    def habits_in_stack(self, user_id, stack_id):
        self.get(user_id, stack_id)
        return self.habits.list_by_stack(user_id, stack_id)

    def unstacked_habits(self, user_id):
        return [habit for habit in self.habits.list(user_id, active=True) if habit.stack_id is None]

    def progress(self, user_id, stack_id, selected_date: date):
        habits = self.habits_in_stack(user_id, stack_id)
        scheduled = [habit for habit in habits if self.habit_service.is_scheduled(user_id, habit, selected_date)]
        completed = sum(
            self.habit_service.get_check_in(user_id, habit.id, selected_date) is not None
            and self.habit_service.get_check_in(user_id, habit.id, selected_date).status.value == "completed"
            for habit in scheduled
        )
        return completed, len(scheduled)


def _require_exact_ids(expected, actual, label):
    if len(actual) != len(set(actual)) or set(expected) != set(actual):
        raise ValidationError(f"Reordered {label} must contain each current item exactly once")


def _name(value):
    value = value.strip()
    if not value:
        raise ValidationError("Habit stack name must not be empty")
    return value


def _description(value):
    if value is None:
        return None
    value = value.strip()
    return value or None
