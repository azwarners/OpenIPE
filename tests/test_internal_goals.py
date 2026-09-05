import pytest

from openipe.api.internal.errors import InternalNotFoundError, InternalValidationError
from tests.internal_support import admin, make_internal


def test_goal_lifecycle_and_evidence_contract(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, "Goal")
        assert goal.evidence.tasks_total == 0
        assert api.goals.pause(context, goal.id).status.value == "paused"
        assert api.goals.resume(context, goal.id).status.value == "active"
        assert api.goals.achieve(context, goal.id).status.value == "achieved"
        with pytest.raises(InternalValidationError):
            api.goals.resume(context, goal.id)
        with pytest.raises(InternalNotFoundError):
            api.goals.get(context, 9999)
    finally:
        connection.close()
