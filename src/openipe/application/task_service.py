"""Task lifecycle and project-assignment application service."""

from datetime import UTC, date, datetime
import sqlite3

from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.task import Task, TaskPriority, TaskStatus
from openipe.persistence.repositories.inbox_repository import InboxRepository
from openipe.persistence.repositories.project_repository import ProjectRepository
from openipe.persistence.repositories.task_repository import TaskRepository

UNSET = object()


class TaskService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = TaskRepository(connection)
        self.projects = ProjectRepository(connection)
        self.inbox = InboxRepository(connection)

    def create(self, user_id, title, description=None, project_id=None, priority=TaskPriority.NORMAL,
               due_date=None, is_today=False, source_inbox_item_id=None) -> Task:
        if project_id is not None and self.projects.get(user_id, project_id) is None:
            raise NotFoundError("Project not found")
        if source_inbox_item_id is not None and self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        return self.repository.create(user_id, _title(title), _description(description), project_id,
                                      _priority(priority), due_date, is_today, source_inbox_item_id)

    def list(self, user_id, status=None, project_id=None):
        return self.repository.list(user_id, status, project_id)

    def get(self, user_id, task_id) -> Task:
        task = self.repository.get(user_id, task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return task

    def update(self, user_id, task_id, title=UNSET, description=UNSET, project_id=UNSET,
               status=UNSET, priority=UNSET, due_date=UNSET, is_today=UNSET,
               source_inbox_item_id=UNSET) -> Task:
        task = self.get(user_id, task_id)
        new_project_id = project_id if project_id is not UNSET else task.project_id
        if new_project_id is not None and self.projects.get(user_id, new_project_id) is None:
            raise NotFoundError("Project not found")
        if source_inbox_item_id is not UNSET and source_inbox_item_id is not None and \
                self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        new_status = status if status is not UNSET and status is not None else task.status
        new_priority = _priority(priority if priority is not UNSET and priority is not None else task.priority)
        if not isinstance(new_status, TaskStatus):
            raise ValidationError("Invalid task status")
        if status is not UNSET:
            _validate_transition(task.status, new_status)
        completed_at = task.completed_at
        archived_at = task.archived_at
        if new_status == TaskStatus.COMPLETED:
            completed_at = completed_at or datetime.now(UTC)
        elif new_status in {TaskStatus.OPEN, TaskStatus.CANCELLED}:
            completed_at = None
        if new_status == TaskStatus.ARCHIVED:
            archived_at = archived_at or datetime.now(UTC)
        if new_status != TaskStatus.ARCHIVED:
            archived_at = None
        updated = self.repository.update(
            user_id, task_id,
            _title(title) if title is not UNSET and title is not None else task.title,
            _description(description) if description is not UNSET else task.description,
            new_project_id, new_status, new_priority,
            due_date if due_date is not UNSET else task.due_date,
            is_today if is_today is not UNSET else task.is_today,
            source_inbox_item_id if source_inbox_item_id is not UNSET else task.source_inbox_item_id,
            completed_at, archived_at,
        )
        if task.project_id != new_project_id or new_status != TaskStatus.OPEN:
            self.projects.clear_next_action_for_task(user_id, task_id)
        return updated

    def complete(self, user_id, task_id):
        return self.update(user_id, task_id, status=TaskStatus.COMPLETED)

    def reopen(self, user_id, task_id):
        return self.update(user_id, task_id, status=TaskStatus.OPEN)

    def cancel(self, user_id, task_id):
        return self.update(user_id, task_id, status=TaskStatus.CANCELLED)


def _validate_transition(current, new):
    if current == TaskStatus.ARCHIVED and new != TaskStatus.ARCHIVED:
        raise ValidationError("Archived tasks cannot be reopened or changed")
    if new == TaskStatus.COMPLETED and current != TaskStatus.OPEN:
        raise ValidationError("Only open tasks can be completed")
    if new == TaskStatus.OPEN and current != TaskStatus.COMPLETED:
        raise ValidationError("Only completed tasks can be reopened")
    if new == TaskStatus.CANCELLED and current != TaskStatus.OPEN:
        raise ValidationError("Only open tasks can be cancelled")


def _title(value):
    value = value.strip()
    if not value:
        raise ValidationError("Task title must not be empty")
    return value


def _description(value):
    if value is None:
        return None
    value = value.strip()
    return value or None


def _priority(value):
    try:
        return value if isinstance(value, TaskPriority) else TaskPriority(value)
    except ValueError as error:
        raise ValidationError("Invalid task priority") from error
