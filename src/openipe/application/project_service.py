"""Project application service and next-action rules."""

from datetime import UTC, datetime
import sqlite3

from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.project import Project, ProjectStatus
from openipe.core.models.task import TaskStatus
from openipe.persistence.repositories.inbox_repository import InboxRepository
from openipe.persistence.repositories.project_repository import ProjectRepository
from openipe.persistence.repositories.task_repository import TaskRepository

UNSET = object()


class ProjectService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = ProjectRepository(connection)
        self.tasks = TaskRepository(connection)
        self.inbox = InboxRepository(connection)

    def create(self, user_id, title, description=None, source_inbox_item_id=None) -> Project:
        if source_inbox_item_id is not None and self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        return self.repository.create(user_id, _title(title), _description(description), source_inbox_item_id)

    def list(self, user_id, status=None) -> list[Project]:
        return self.repository.list(user_id, status)

    def get(self, user_id, project_id) -> Project:
        project = self.repository.get(user_id, project_id)
        if project is None:
            raise NotFoundError("Project not found")
        return project

    def update(self, user_id, project_id, title=UNSET, description=UNSET, status=UNSET,
               source_inbox_item_id=UNSET) -> Project:
        project = self.get(user_id, project_id)
        if source_inbox_item_id is not UNSET and source_inbox_item_id is not None and \
                self.inbox.get(user_id, source_inbox_item_id) is None:
            raise NotFoundError("Source inbox item not found")
        new_status = status if status is not UNSET and status is not None else project.status
        if not isinstance(new_status, ProjectStatus):
            raise ValidationError("Invalid project status")
        _validate_transition(project.status, new_status)
        completed_at = project.completed_at
        archived_at = project.archived_at
        if new_status == ProjectStatus.COMPLETED:
            completed_at = completed_at or datetime.now(UTC)
        elif new_status in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED, ProjectStatus.CANCELLED}:
            completed_at = None
        if new_status == ProjectStatus.ARCHIVED:
            archived_at = archived_at or datetime.now(UTC)
        next_action = project.next_action_task_id
        if new_status in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED, ProjectStatus.ARCHIVED}:
            next_action = None
        return self.repository.update(
            user_id, project_id,
            _title(title) if title is not UNSET and title is not None else project.title,
            _description(description) if description is not UNSET else project.description,
            new_status, next_action,
            source_inbox_item_id if source_inbox_item_id is not UNSET else project.source_inbox_item_id,
            completed_at, archived_at,
        )

    def pause(self, user_id, project_id):
        return self.update(user_id, project_id, status=ProjectStatus.PAUSED)

    def resume(self, user_id, project_id):
        return self.update(user_id, project_id, status=ProjectStatus.ACTIVE)

    def complete(self, user_id, project_id):
        return self.update(user_id, project_id, status=ProjectStatus.COMPLETED)

    def cancel(self, user_id, project_id):
        return self.update(user_id, project_id, status=ProjectStatus.CANCELLED)

    def archive(self, user_id, project_id):
        return self.update(user_id, project_id, status=ProjectStatus.ARCHIVED)

    def set_next_action(self, user_id, project_id, task_id) -> Project:
        project = self.get(user_id, project_id)
        task = self.tasks.get(user_id, task_id)
        if task is None or task.project_id != project.id:
            raise ValidationError("Next-action task must belong to the project")
        if task.status != TaskStatus.OPEN:
            raise ValidationError("Next-action task must be open")
        if project.status not in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED}:
            raise ValidationError("Only active or paused projects can have a next action")
        return self.repository.set_next_action(user_id, project_id, task_id)

    def clear_next_action(self, user_id, project_id) -> Project:
        project = self.get(user_id, project_id)
        return self.repository.update(
            user_id, project_id, project.title, project.description, project.status, None,
            project.source_inbox_item_id, project.completed_at, project.archived_at,
        )

    def task_list(self, user_id, project_id):
        self.get(user_id, project_id)
        return self.tasks.list(user_id, project_id=project_id)

    def progress(self, user_id, project_id):
        self.get(user_id, project_id)
        task_ids = self.repository.task_ids(user_id, project_id)
        total, completed, open_count = self.repository.progress(user_id, project_id)
        return task_ids, total, completed, open_count


def _validate_transition(current, new):
    if current == ProjectStatus.ARCHIVED and new != ProjectStatus.ARCHIVED:
        raise ValidationError("Archived projects cannot be resumed or changed")
    if new == ProjectStatus.PAUSED and current != ProjectStatus.ACTIVE:
        raise ValidationError("Only active projects can be paused")
    if new == ProjectStatus.ACTIVE and current not in {ProjectStatus.ACTIVE, ProjectStatus.PAUSED}:
        raise ValidationError("Only paused projects can be resumed")
    if new in {ProjectStatus.COMPLETED, ProjectStatus.CANCELLED} and current not in {
        ProjectStatus.ACTIVE, ProjectStatus.PAUSED,
    }:
        raise ValidationError("Only active or paused projects can change lifecycle state")


def _title(value):
    value = value.strip()
    if not value:
        raise ValidationError("Project title must not be empty")
    return value


def _description(value):
    if value is None:
        return None
    value = value.strip()
    return value or None
