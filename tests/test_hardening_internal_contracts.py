"""Internal API boundary invariants and contract regression tests."""

from dataclasses import FrozenInstanceError, fields, is_dataclass
from datetime import date

import pytest

from openipe.api.internal import InternalAPI
from openipe.api.internal.contracts import (
    CheckInCreateContract,
    CredentialsContract,
    InboxCreateContract,
    ReorderContract,
    TaskCreateContract,
    TodayQueryContract,
    UserContract,
)
from openipe.api.internal.errors import InvalidContextError, InternalNotFoundError
from openipe.core.models.task import TaskPriority
from tests.internal_support import admin, make_internal


def test_public_contracts_are_immutable_and_have_no_transport_types():
    contracts = [CredentialsContract, InboxCreateContract, ReorderContract, TaskCreateContract,
                 TodayQueryContract, UserContract, CheckInCreateContract]
    for contract in contracts:
        assert is_dataclass(contract)
        instance = contract(**{
            "CredentialsContract": {"username": "a", "password": "b"},
            "InboxCreateContract": {"text": "x"},
            "ReorderContract": {"ids": (1, 2)},
            "TaskCreateContract": {"title": "x"},
            "TodayQueryContract": {},
            "UserContract": {
                "id": 1, "username": "a", "display_name": "A", "is_admin": True,
                "is_active": True, "created_at": __import__("datetime").datetime.now(),
                "updated_at": __import__("datetime").datetime.now(), "last_login_at": None,
            },
            "CheckInCreateContract": {"date": date(2026, 1, 1)},
        }[contract.__name__])
        with pytest.raises(FrozenInstanceError):
            setattr(instance, fields(contract)[0].name, None)


def test_internal_api_requires_a_context_for_protected_calls(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        with pytest.raises(InvalidContextError):
            api.inbox.list(None)
        with pytest.raises(InvalidContextError):
            api.users.list(None)
    finally:
        connection.close()


def test_internal_outputs_are_contracts_not_models_or_sqlite_rows(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        inbox = api.inbox.create(context, InboxCreateContract("✨ \u0301 SQL-like ' text\nline"))
        task = api.tasks.create(context, TaskCreateContract("task", priority=TaskPriority.HIGH))
        assert inbox.__class__.__module__.startswith("openipe.api.internal")
        assert task.__class__.__module__.startswith("openipe.api.internal")
        assert not hasattr(task, "user_id")
        assert "sqlite3" not in repr(task)
        assert inbox.text.startswith("✨")
    finally:
        connection.close()


def test_contract_input_fields_survive_round_trip_and_explicit_null_clears_values(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        task = api.tasks.create(context, TaskCreateContract("task", description="  detail  ", is_today=True))
        assert task.description == "detail"
        updated = api.tasks.update(context, task.id, description=None, is_today=False)
        assert updated.description is None
        assert updated.is_today is False
    finally:
        connection.close()


def test_cross_user_records_are_invisible_to_internal_queries(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, first = admin(api)
        second_user = api.users.create(first, "second", "Second", "second-pass")
        second = api.authenticate(api.auth.login("second", "second-pass").access_token)
        record = api.inbox.create(first, "private")
        assert api.inbox.list(second) == []
        with pytest.raises(InternalNotFoundError):
            api.inbox.get(second, record.id)
        with pytest.raises(InternalNotFoundError):
            api.inbox.archive(second, record.id)
        assert api.users.get(first, second_user.id).username == "second"
    finally:
        connection.close()
