from tests.internal_support import admin, make_internal


def test_goal_association_contracts_and_removal(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        goal = api.goals.create(context, "Goal")
        project = api.projects.create(context, "Project")
        result = api.goals.associate(context, goal.id, project.id, "project")
        assert result.project_ids == [project.id]
        api.goals.remove(context, goal.id, project.id, "project")
        assert api.goals.get(context, goal.id).project_ids == []
    finally:
        connection.close()
