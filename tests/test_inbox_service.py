import pytest

from openipe.application.auth_service import AuthService
from openipe.application.inbox_service import InboxService
from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.inbox import InboxStatus
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, InboxService(connection)


def test_capture_edit_and_list_are_user_scoped(tmp_path):
    connection, user, inbox = services(tmp_path)
    try:
        item = inbox.create(user.id, "  Remember to review the blueprint  ")
        assert item.text == "Remember to review the blueprint"
        assert item.status == InboxStatus.UNPROCESSED
        updated = inbox.update(user.id, item.id, text="Review the blueprint tonight")
        assert updated.text == "Review the blueprint tonight"
        assert inbox.list(user.id) == [updated]
        with pytest.raises(NotFoundError):
            inbox.get(user.id + 1, item.id)
        assert inbox.list(user.id + 1) == []
    finally:
        connection.close()


def test_processing_and_returning_to_unprocessed_tracks_timestamps(tmp_path):
    connection, user, inbox = services(tmp_path)
    try:
        item = inbox.create(user.id, "Process this idea")
        processed = inbox.update(user.id, item.id, status=InboxStatus.PROCESSED)
        assert processed.status == InboxStatus.PROCESSED
        assert processed.processed_at is not None
        returned = inbox.update(user.id, item.id, status=InboxStatus.UNPROCESSED)
        assert returned.status == InboxStatus.UNPROCESSED
        assert returned.processed_at is None
        assert returned.archived_at is None
    finally:
        connection.close()


def test_archive_discard_and_delete_are_soft_operations(tmp_path):
    connection, user, inbox = services(tmp_path)
    try:
        archived = inbox.create(user.id, "Archive this idea")
        archived = inbox.update(user.id, archived.id, status=InboxStatus.ARCHIVED)
        assert archived.archived_at is not None
        assert inbox.get(user.id, archived.id).status == InboxStatus.ARCHIVED

        discarded = inbox.create(user.id, "Discard this idea")
        discarded = inbox.update(user.id, discarded.id, status=InboxStatus.DISCARDED)
        assert discarded.status == InboxStatus.DISCARDED
        deleted = inbox.create(user.id, "Delete means archive")
        inbox.delete(user.id, deleted.id)
        assert inbox.get(user.id, deleted.id).status == InboxStatus.ARCHIVED
    finally:
        connection.close()


def test_empty_capture_and_edit_are_rejected(tmp_path):
    connection, user, inbox = services(tmp_path)
    try:
        with pytest.raises(ValidationError, match="must not be empty"):
            inbox.create(user.id, "   ")
        item = inbox.create(user.id, "Valid idea")
        with pytest.raises(ValidationError, match="must not be empty"):
            inbox.update(user.id, item.id, text=" ")
    finally:
        connection.close()


def test_status_filter_returns_only_matching_items(tmp_path):
    connection, user, inbox = services(tmp_path)
    try:
        first = inbox.create(user.id, "First")
        inbox.create(user.id, "Second")
        inbox.update(user.id, first.id, status=InboxStatus.PROCESSED)
        assert [item.text for item in inbox.list(user.id, InboxStatus.PROCESSED)] == ["First"]
        assert [item.text for item in inbox.list(user.id, InboxStatus.UNPROCESSED)] == ["Second"]
    finally:
        connection.close()
