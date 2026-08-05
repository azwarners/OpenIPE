from datetime import date, timedelta

from openipe.application.auth_service import AuthService
from openipe.application.goal_service import GoalService
from openipe.application.habit_service import HabitService
from openipe.application.habit_stack_service import HabitStackService
from openipe.application.project_service import ProjectService
from openipe.application.task_service import TaskService
from openipe.application.today_service import TodayService
from openipe.persistence.database import initialize_database


def services(tmp_path):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    auth = AuthService(connection)
    user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
    return connection, user, TaskService(connection), HabitService(connection), HabitStackService(connection), ProjectService(connection), GoalService(connection)


def test_today_selects_tasks_groups_habits_and_includes_goal_context(tmp_path):
    connection, user, tasks, habits, stacks, projects, goals = services(tmp_path)
    try:
        selected = date(2026, 8, 5)
        project = projects.create(user.id, "Release")
        goal = goals.create(user.id, "Publish OpenIPE")
        manual = tasks.create(user.id, "Manual task", project_id=project.id, is_today=True)
        due = tasks.create(user.id, "Due task", due_date=selected)
        overdue = tasks.create(user.id, "Overdue task", due_date=selected - timedelta(days=1))
        tasks.create(user.id, "Future task", due_date=selected + timedelta(days=1))
        goals.associate_task(user.id, goal.id, manual.id)
        stack = stacks.create(user.id, "Morning")
        stacked = habits.create(user.id, "Meditate")
        unstacked = habits.create(user.id, "Plan")
        stacks.add_habit(user.id, stack.id, stacked.id)
        habits.check_in(user.id, stacked.id, selected)
        result = TodayService(connection).get(user.id, selected)
        assert {item["id"] for item in result["tasks"]} == {manual.id, due.id, overdue.id}
        assert any(item["goals"] for item in result["tasks"])
        assert result["habit_stacks"][0]["completed_count"] == 1
        assert result["habit_stacks"][0]["scheduled_count"] == 1
        assert [item["id"] for item in result["unstacked_habits"]] == [unstacked.id]
        assert result["completed"]["tasks"] == []
    finally:
        connection.close()


def test_today_completed_section_and_overdue_flag(tmp_path):
    connection, user, tasks, _, _, _, _ = services(tmp_path)
    try:
        selected = date(2026, 8, 5)
        overdue = tasks.create(user.id, "Complete overdue", due_date=selected - timedelta(days=2))
        tasks.complete(user.id, overdue.id)
        result = TodayService(connection).get(user.id, selected, include_completed=True)
        assert result["tasks"] == []
        assert result["completed"]["tasks"][0]["id"] == overdue.id
        assert result["completed"]["tasks"][0]["overdue"] is True
    finally:
        connection.close()
