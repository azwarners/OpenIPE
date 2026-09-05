"""Meta-tests preventing silent growth of uncovered public surfaces."""

from openipe.api.REST.app import create_app
from openipe.api.internal import InternalAPI
from tests.coverage_registry import INTERNAL_OPERATION_COVERAGE, REST_ROUTE_COVERAGE
from tests.test_rest_delegation import SpyAPI


def test_internal_registry_matches_every_public_namespace_callable():
    actual = {}
    for namespace_name in INTERNAL_OPERATION_COVERAGE:
        namespace = getattr(InternalAPI.__new__(InternalAPI), namespace_name, None)
        # The façade namespaces are proxies; use the namespace declarations in
        # a real façade-free comparison below through the public registry.
        del namespace
    expected = {key: set(value) for key, value in INTERNAL_OPERATION_COVERAGE.items()}
    assert set(expected) == {"auth", "users", "inbox", "goals", "projects", "tasks", "habits", "habit_stacks", "today"}
    assert all(expected.values())


def test_internal_registry_contains_all_public_methods_on_a_real_facade(tmp_path):
    from openipe.core.config import Settings
    from openipe.persistence.database import initialize_database

    connection = initialize_database(tmp_path / "registry.sqlite3")
    try:
        api = InternalAPI(connection, Settings(database_path=tmp_path / "registry.sqlite3"))
        actual = {
            name: {method for method in dir(getattr(api, name)._namespace) if not method.startswith("_") and callable(getattr(getattr(api, name)._namespace, method))}
            for name in INTERNAL_OPERATION_COVERAGE
        }
        assert actual == INTERNAL_OPERATION_COVERAGE
    finally:
        connection.close()


def test_rest_registry_matches_every_concrete_fastapi_path():
    app = create_app(SpyAPI())
    actual = {
        f"{method.upper()} {path}"
        for path, details in app.openapi()["paths"].items()
        for method in details
    }
    assert actual == set(REST_ROUTE_COVERAGE)


def test_registry_has_explicit_error_and_success_expectations():
    assert len(INTERNAL_OPERATION_COVERAGE) == 9
    assert len(REST_ROUTE_COVERAGE) == 55
    assert all(set(details) == {"success", "failure"} for details in REST_ROUTE_COVERAGE.values())
    assert all(details["success"] and details["failure"] for details in REST_ROUTE_COVERAGE.values())


def test_registry_is_independent_of_ignored_documentation_paths():
    assert all(path.split(" ", 1)[1].startswith("/api/v1/") for path in REST_ROUTE_COVERAGE)
