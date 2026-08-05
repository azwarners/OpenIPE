from datetime import date

import pytest

from openipe.application.auth_service import AuthService
from openipe.application.goal_service import GoalService
from openipe.application.habit_service import HabitService
from openipe.application.project_service import ProjectService
from openipe.application.task_service import TaskService
from openipe.core.errors import NotFoundError
from openipe.core.models.habit import HabitCheckInStatus
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, GoalService(connection), ProjectService(connection), TaskService(connection), HabitService(connection)


def test_goal_associations_and_evidence(tmp_path):
    connection, user, goals, projects, tasks, habits = services(tmp_path)
    try:
        goal = goals.create(user.id, "Publish OpenIPE")
        project = projects.create(user.id, "Release project")
        task = tasks.create(user.id, "Write release notes", project_id=project.id)
        habit = habits.create(user.id, "Work on release")
        goals.associate_project(user.id, goal.id, project.id)
        goals.associate_task(user.id, goal.id, task.id)
        goals.associate_habit(user.id, goal.id, habit.id)
        assert goals.associated_ids(user.id, goal.id) == {
            "project_ids": [project.id], "task_ids": [task.id], "habit_ids": [habit.id]
        }
        today = date.today()
        habits.check_in(user.id, habit.id, today, HabitCheckInStatus.COMPLETED)
        evidence = goals.evidence(user.id, goal.id, today)
        assert evidence["projects_total"] == 1
        assert evidence["projects_completed"] == 0
        assert evidence["tasks_total"] == 1
        assert evidence["tasks_open"] == 1
        assert evidence["habits_scheduled"] >= 1
        assert evidence["habits_completed"] == 1
        projects.complete(user.id, project.id)
        tasks.complete(user.id, task.id)
        evidence = goals.evidence(user.id, goal.id, today)
        assert evidence["projects_completed"] == 1
        assert evidence["tasks_completed"] == 1
        goals.remove_association(user.id, goal.id, task.id, "task")
        assert goals.associated_ids(user.id, goal.id)["task_ids"] == []
    finally:
        connection.close()


def test_association_requires_same_user_owned_records(tmp_path):
    connection, user, goals, projects, tasks, habits = services(tmp_path)
    try:
        goal = goals.create(user.id, "My goal")
        other = AuthService(connection).create_user(user, "other", "Other", "other-pass")
        other_project = projects.create(other.id, "Other project")
        other_task = tasks.create(other.id, "Other task")
        other_habit = habits.create(other.id, "Other habit")
        with pytest.raises(NotFoundError):
            goals.associate_project(user.id, goal.id, other_project.id)
        with pytest.raises(NotFoundError):
            goals.associate_task(user.id, goal.id, other_task.id)
        with pytest.raises(NotFoundError):
            goals.associate_habit(user.id, goal.id, other_habit.id)
    finally:
        connection.close()


def test_duplicate_associations_are_idempotent(tmp_path):
    connection, user, goals, projects, _, _ = services(tmp_path)
    try:
        goal = goals.create(user.id, "Goal")
        project = projects.create(user.id, "Project")
        goals.associate_project(user.id, goal.id, project.id)
        goals.associate_project(user.id, goal.id, project.id)
        assert goals.associated_ids(user.id, goal.id)["project_ids"] == [project.id]
    finally:
        connection.close()
