from datetime import date

from tests.internal_support import admin, make_internal


def test_today_selected_date_and_completed_section(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, "Today", due_date=date(2026, 1, 1), is_today=True)
        api.tasks.complete(context, task.id)
        result = api.today.get(context, date(2026, 1, 2), include_completed=True)
        assert result.date == date(2026, 1, 2)
        assert result.completed.tasks[0].id == task.id
        assert result.completed.tasks[0].overdue is True
    finally:
        connection.close()
