import ast
from pathlib import Path

import pytest


REST_ROOT = Path(__file__).parents[1] / "src" / "openipe" / "api" / "REST"


def test_rest_has_no_core_application_or_persistence_imports():
    forbidden = ("openipe.core", "openipe.application", "openipe.persistence", "sqlite3")
    violations = []
    for path in REST_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if name.startswith(forbidden):
                    violations.append(f"{path}:{node.lineno}: {name}")
    assert violations == []


def test_rest_dependency_does_not_expose_connection():
    from openipe.api.REST import dependencies

    assert not hasattr(dependencies, "get_connection")


def test_rest_factory_requires_an_injected_internal_api():
    from openipe.api.REST.app import create_app

    with pytest.raises(TypeError):
        create_app()  # type: ignore[call-arg]


def test_rest_does_not_read_internal_implementation_details():
    forbidden_attributes = {
        "actor", "connection", "database", "db", "settings", "auth_service",
        "inbox_service", "goal_service", "project_service", "task_service",
        "habit_service", "stack_service", "today_service", "_namespace",
    }
    violations = []
    for path in REST_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in forbidden_attributes:
                violations.append(f"{path}:{node.lineno}: .{node.attr}")
    assert violations == []
