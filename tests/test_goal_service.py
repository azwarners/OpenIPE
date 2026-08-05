import pytest

from openipe.application.auth_service import AuthService
from openipe.application.goal_service import GoalService
from openipe.application.inbox_service import InboxService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.goal import GoalStatus
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, GoalService(connection), InboxService(connection)


def test_create_edit_and_list_goal(tmp_path):
    connection, user, goals, _ = services(tmp_path)
    try:
        goal = goals.create(user.id, "  Publish OpenIPE  ", "  Ship the first release  ")
        assert goal.title == "Publish OpenIPE"
        assert goal.description == "Ship the first release"
        assert goal.status == GoalStatus.ACTIVE
        edited = goals.update(user.id, goal.id, title="Publish OpenIPE v0.0.1", description=None)
        assert edited.title == "Publish OpenIPE v0.0.1"
        assert edited.description is None
        assert goals.list(user.id) == [edited]
        with pytest.raises(NotFoundError):
            goals.get(user.id + 1, goal.id)
    finally:
        connection.close()


def test_goal_lifecycle_timestamps_and_resume(tmp_path):
    connection, user, goals, _ = services(tmp_path)
    try:
        goal = goals.create(user.id, "Improve health")
        paused = goals.pause(user.id, goal.id)
        assert paused.status == GoalStatus.PAUSED
        resumed = goals.resume(user.id, goal.id)
        assert resumed.status == GoalStatus.ACTIVE
        achieved = goals.achieve(user.id, goal.id)
        assert achieved.status == GoalStatus.ACHIEVED
        assert achieved.achieved_at is not None
        with pytest.raises(ValidationError, match="Only paused goals can be resumed"):
            goals.resume(user.id, goal.id)
    finally:
        connection.close()


def test_abandon_and_archive_are_terminal_lifecycle_states(tmp_path):
    connection, user, goals, _ = services(tmp_path)
    try:
        abandoned = goals.abandon(user.id, goals.create(user.id, "Different goal").id)
        assert abandoned.status == GoalStatus.ABANDONED
        archived = goals.archive(user.id, abandoned.id)
        assert archived.status == GoalStatus.ARCHIVED
        assert archived.archived_at is not None
        with pytest.raises(ValidationError, match="cannot be resumed"):
            goals.resume(user.id, archived.id)
    finally:
        connection.close()


def test_source_inbox_item_requires_same_user(tmp_path):
    connection, user, goals, inbox = services(tmp_path)
    try:
        item = inbox.create(user.id, "Goal idea")
        goal = goals.create(user.id, "Goal", source_inbox_item_id=item.id)
        assert goal.source_inbox_item_id == item.id
        with pytest.raises(NotFoundError, match="Source inbox"):
            goals.create(user.id + 1, "Other goal", source_inbox_item_id=item.id)
    finally:
        connection.close()


def test_goal_title_must_not_be_empty(tmp_path):
    connection, user, goals, _ = services(tmp_path)
    try:
        with pytest.raises(ValidationError, match="must not be empty"):
            goals.create(user.id, "   ")
    finally:
        connection.close()
