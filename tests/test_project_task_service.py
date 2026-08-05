from datetime import date

import pytest

from openipe.application.auth_service import AuthService
from openipe.application.inbox_service import InboxService
from openipe.application.project_service import ProjectService
from openipe.application.task_service import TaskService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.project import ProjectStatus
from openipe.core.models.task import TaskPriority, TaskStatus
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, ProjectService(connection), TaskService(connection), InboxService(connection)


def test_project_tasks_and_progress(tmp_path):
    connection, user, projects, tasks, _ = services(tmp_path)
    try:
        project = projects.create(user.id, "Build OpenIPE", "First release")
        first = tasks.create(user.id, "Implement API", project_id=project.id, priority=TaskPriority.HIGH)
        second = tasks.create(user.id, "Write docs", project_id=project.id, due_date=date(2026, 12, 31))
        assert projects.progress(user.id, project.id) == ([first.id, second.id], 2, 0, 2)
        tasks.complete(user.id, first.id)
        assert projects.progress(user.id, project.id) == ([first.id, second.id], 2, 1, 1)
        assert [task.id for task in projects.task_list(user.id, project.id)] == [second.id, first.id]
    finally:
        connection.close()


def test_next_action_enforces_project_ownership_and_open_state(tmp_path):
    connection, user, projects, tasks, _ = services(tmp_path)
    try:
        project = projects.create(user.id, "Build OpenIPE")
        task = tasks.create(user.id, "Next action", project_id=project.id)
        assert projects.set_next_action(user.id, project.id, task.id).next_action_task_id == task.id
        tasks.complete(user.id, task.id)
        assert projects.get(user.id, project.id).next_action_task_id is None
        other_project = projects.create(user.id, "Other project")
        other_task = tasks.create(user.id, "Other task", project_id=other_project.id)
        with pytest.raises(ValidationError, match="belong to the project"):
            projects.set_next_action(user.id, project.id, other_task.id)
        with pytest.raises(ValidationError, match="must be open"):
            projects.set_next_action(user.id, project.id, task.id)
    finally:
        connection.close()


def test_task_lifecycle_and_project_moves_clear_next_action(tmp_path):
    connection, user, projects, tasks, _ = services(tmp_path)
    try:
        first_project = projects.create(user.id, "First")
        second_project = projects.create(user.id, "Second")
        task = tasks.create(user.id, "Move me", project_id=first_project.id)
        projects.set_next_action(user.id, first_project.id, task.id)
        moved = tasks.update(user.id, task.id, project_id=second_project.id)
        assert moved.project_id == second_project.id
        assert projects.get(user.id, first_project.id).next_action_task_id is None
        completed = tasks.complete(user.id, task.id)
        assert completed.status == TaskStatus.COMPLETED
        with pytest.raises(ValidationError, match="Only open"):
            tasks.complete(user.id, task.id)
        reopened = tasks.reopen(user.id, task.id)
        assert reopened.completed_at is None
        cancelled = tasks.cancel(user.id, task.id)
        assert cancelled.status == TaskStatus.CANCELLED
        with pytest.raises(ValidationError, match="Only completed"):
            tasks.reopen(user.id, task.id)
    finally:
        connection.close()


def test_project_lifecycle_clears_next_action(tmp_path):
    connection, user, projects, tasks, _ = services(tmp_path)
    try:
        project = projects.create(user.id, "Finish project")
        task = tasks.create(user.id, "Final action", project_id=project.id)
        projects.set_next_action(user.id, project.id, task.id)
        completed = projects.complete(user.id, project.id)
        assert completed.status == ProjectStatus.COMPLETED
        assert completed.completed_at is not None
        assert completed.next_action_task_id is None
        with pytest.raises(ValidationError, match="can be resumed"):
            projects.resume(user.id, project.id)
    finally:
        connection.close()


def test_inbox_conversions_preserve_source_and_original(tmp_path):
    connection, user, projects, tasks, inbox = services(tmp_path)
    try:
        item = inbox.create(user.id, "Build the release")
        task = tasks.create(user.id, item.text, source_inbox_item_id=item.id)
        project = projects.create(user.id, item.text, source_inbox_item_id=item.id)
        assert task.source_inbox_item_id == item.id
        assert project.source_inbox_item_id == item.id
        assert inbox.get(user.id, item.id).status.value == "unprocessed"
        with pytest.raises(NotFoundError):
            tasks.create(user.id + 1, "Cross user", source_inbox_item_id=item.id)
    finally:
        connection.close()
