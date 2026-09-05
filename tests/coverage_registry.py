"""Machine-readable coverage declarations checked by Wave 3 meta-tests."""

INTERNAL_OPERATION_COVERAGE = {
    "auth": {"initial_admin", "login", "logout", "current_user", "change_password"},
    "users": {"list", "get", "create", "update"},
    "inbox": {"list", "create", "get", "update", "delete", "process", "archive", "discard", "create_task", "create_project", "create_habit"},
    "goals": {"list", "get", "create", "update", "lifecycle", "pause", "resume", "achieve", "abandon", "archive", "associate", "remove", "associated_ids", "evidence"},
    "projects": {"list", "get", "create", "update", "lifecycle", "tasks", "set_next_action", "clear_next_action", "progress", "pause", "resume", "complete", "cancel", "archive"},
    "tasks": {"list", "create", "get", "update", "lifecycle", "complete", "reopen", "cancel"},
    "habits": {"list", "get", "create", "update", "lifecycle", "check_in", "get_check_in", "recent_check_ins", "delete_check_in", "activate", "deactivate", "archive"},
    "habit_stacks": {"list", "get", "create", "update", "lifecycle", "add_habit", "remove_habit", "reorder_stacks", "reorder_habits", "unstacked", "progress", "archive"},
    "today": {"get"},
}

# Paths are the concrete route-handler surface exposed by FastAPI.  The
# registry is deliberately independent of app.openapi() so a newly added path
# fails the meta-test until it receives explicit coverage documentation.
_REST_ROUTE_PATHS = {
    "/api/v1/auth/change-password", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/me",
    "/api/v1/goals", "/api/v1/goals/{goal_id}", "/api/v1/goals/{goal_id}/habits/{habit_id}",
    "/api/v1/goals/{goal_id}/projects/{project_id}", "/api/v1/goals/{goal_id}/tasks/{task_id}",
    "/api/v1/habit-stacks", "/api/v1/habit-stacks/reorder", "/api/v1/habit-stacks/{stack_id}",
    "/api/v1/habit-stacks/{stack_id}/habits/reorder", "/api/v1/habit-stacks/{stack_id}/habits/{habit_id}",
    "/api/v1/habits", "/api/v1/habits/{habit_id}", "/api/v1/habits/{habit_id}/check-ins",
    "/api/v1/habits/{habit_id}/check-ins/{checkin_date}", "/api/v1/inbox", "/api/v1/inbox/{item_id}",
    "/api/v1/inbox/{item_id}/create-habit", "/api/v1/inbox/{item_id}/create-project",
    "/api/v1/inbox/{item_id}/create-task", "/api/v1/projects", "/api/v1/projects/{project_id}",
    "/api/v1/projects/{project_id}/next-action", "/api/v1/projects/{project_id}/next-action/{task_id}",
    "/api/v1/projects/{project_id}/tasks", "/api/v1/setup/initial-admin", "/api/v1/tasks",
    "/api/v1/tasks/{task_id}", "/api/v1/tasks/{task_id}/{action}", "/api/v1/today", "/api/v1/users",
    "/api/v1/users/{user_id}",
}

_REST_ROUTE_METHODS = {}


def _declare(method, *paths):
    for path in paths:
        _REST_ROUTE_METHODS.setdefault(path, set()).add(method)


_declare("GET", "/api/v1/auth/me", "/api/v1/users", "/api/v1/users/{user_id}", "/api/v1/inbox", "/api/v1/inbox/{item_id}", "/api/v1/goals", "/api/v1/goals/{goal_id}", "/api/v1/projects", "/api/v1/projects/{project_id}", "/api/v1/projects/{project_id}/tasks", "/api/v1/tasks", "/api/v1/tasks/{task_id}", "/api/v1/habits", "/api/v1/habits/{habit_id}", "/api/v1/habits/{habit_id}/check-ins", "/api/v1/habit-stacks", "/api/v1/habit-stacks/{stack_id}", "/api/v1/today")
_declare("POST", "/api/v1/setup/initial-admin", "/api/v1/auth/login", "/api/v1/auth/logout", "/api/v1/auth/change-password", "/api/v1/users", "/api/v1/inbox", "/api/v1/inbox/{item_id}/create-task", "/api/v1/inbox/{item_id}/create-project", "/api/v1/inbox/{item_id}/create-habit", "/api/v1/goals", "/api/v1/goals/{goal_id}/projects/{project_id}", "/api/v1/goals/{goal_id}/tasks/{task_id}", "/api/v1/goals/{goal_id}/habits/{habit_id}", "/api/v1/projects", "/api/v1/projects/{project_id}/next-action/{task_id}", "/api/v1/tasks", "/api/v1/tasks/{task_id}/{action}", "/api/v1/habits", "/api/v1/habits/{habit_id}/check-ins", "/api/v1/habit-stacks", "/api/v1/habit-stacks/reorder", "/api/v1/habit-stacks/{stack_id}/habits/reorder", "/api/v1/habit-stacks/{stack_id}/habits/{habit_id}")
_declare("PATCH", "/api/v1/users/{user_id}", "/api/v1/inbox/{item_id}", "/api/v1/goals/{goal_id}", "/api/v1/projects/{project_id}", "/api/v1/tasks/{task_id}", "/api/v1/habits/{habit_id}", "/api/v1/habit-stacks/{stack_id}")
_declare("DELETE", "/api/v1/inbox/{item_id}", "/api/v1/goals/{goal_id}/projects/{project_id}", "/api/v1/goals/{goal_id}/tasks/{task_id}", "/api/v1/goals/{goal_id}/habits/{habit_id}", "/api/v1/projects/{project_id}/next-action", "/api/v1/habits/{habit_id}/check-ins/{checkin_date}", "/api/v1/habit-stacks/{stack_id}/habits/{habit_id}")

REST_ROUTE_COVERAGE = {
    f"{method} {path}": {
        "success": "test_every_collection_route_returns_a_schema_valid_success",
        "failure": "test_route_query_and_path_validation_matrix_returns_422",
    }
    for path, methods in _REST_ROUTE_METHODS.items()
    for method in methods
}
