import pytest

from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from tests.internal_support import admin, make_internal


def test_project_progress_and_next_action_rules(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        project = api.projects.create(context, "Project")
        task = api.tasks.create(context, "Next", project_id=project.id)
        assert api.projects.set_next_action(context, project.id, task.id).next_action_task_id == task.id
        assert api.projects.get(context, project.id).open_task_count == 1
        other = api.tasks.create(context, "Not in project")
        with pytest.raises(InternalValidationError):
            api.projects.set_next_action(context, project.id, other.id)
        assert api.tasks.complete(context, task.id).status.value == "completed"
        assert api.tasks.reopen(context, task.id).status.value == "open"
        with pytest.raises(InternalNotFoundError):
            api.tasks.get(context, 9999)
    finally:
        connection.close()
