"""Adversarial authentication and secret-handling tests."""

from datetime import UTC, datetime, timedelta

import pytest

from openipe.api.internal.errors import (
    InternalAuthenticationError,
    InternalPermissionDeniedError,
    InternalValidationError,
)
from openipe.core.errors import AuthenticationError, ValidationError
from openipe.core.security import generate_token, hash_token, verify_password
from tests.internal_support import admin, make_internal


@pytest.mark.parametrize("password", [""])
def test_empty_passwords_are_rejected(password):
    from openipe.core.security import hash_password

    with pytest.raises(ValueError, match="empty"):
        hash_password(password)


def test_tokens_are_opaque_unique_and_stored_only_as_hashes(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        login_result, context = admin(api)
        second = api.auth.login("admin", "admin-pass")
        assert login_result.access_token != second.access_token
        assert hash_token(login_result.access_token) != login_result.access_token
        stored = connection.execute("SELECT token_hash FROM auth_tokens").fetchall()
        assert login_result.access_token not in {row[0] for row in stored}
        assert context.actor.password_hash not in repr(login_result.user)
    finally:
        connection.close()


def test_duplicate_usernames_are_case_insensitive_and_names_are_normalized(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        user = api.users.create(context, "  Alice  ", "  Alice Example  ", "alice-pass")
        assert user.username == "Alice"
        assert user.display_name == "Alice Example"
        with pytest.raises(InternalValidationError):
            api.users.create(context, "ALICE", "Another", "another-pass")
    finally:
        connection.close()


@pytest.mark.parametrize("text", ["", " ", "\t", "\n"])
def test_blank_user_fields_are_rejected(tmp_path, text):
    api, connection = make_internal(tmp_path)
    try:
        with pytest.raises(InternalValidationError):
            api.auth.initial_admin(text, "Admin", "admin-pass")
    finally:
        connection.close()


def test_double_logout_and_unknown_tokens_are_authentication_errors(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        login_result, _ = admin(api)
        api.auth.logout(login_result.access_token)
        api.auth.logout(login_result.access_token)
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(login_result.access_token)
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(generate_token())
    finally:
        connection.close()


def test_deactivation_revokes_existing_tokens_and_self_deactivation_is_blocked(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        login_result, context = admin(api)
        user = api.users.create(context, "user", "User", "user-pass")
        user_token = api.auth.login("user", "user-pass")
        api.users.update(context, user.id, is_active=False)
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(user_token.access_token)
        with pytest.raises(InternalValidationError):
            api.users.update(context, context.actor.id, is_active=False)
        assert api.authenticate(login_result.access_token).actor.is_active
    finally:
        connection.close()


def test_non_admin_cannot_read_or_mutate_administration(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, admin_context = admin(api)
        user = api.users.create(admin_context, "user", "User", "user-pass")
        user_context = api.authenticate(api.auth.login("user", "user-pass").access_token)
        with pytest.raises(InternalPermissionDeniedError):
            api.authorize_admin(user_context)
        with pytest.raises(InternalPermissionDeniedError):
            api.users.list(user_context)
        with pytest.raises(InternalPermissionDeniedError):
            api.users.update(user_context, user.id, display_name="changed")
    finally:
        connection.close()


def test_expiration_boundary_is_enforced_by_auth_service(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        token = api.auth.login("admin", "admin-pass")
        connection.execute(
            "UPDATE auth_tokens SET expires_at = ? WHERE token_hash = ?",
            (datetime.now(UTC).isoformat(), hash_token(token.access_token)),
        )
        connection.commit()
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(token.access_token)
        assert context.actor.username == "admin"
    finally:
        connection.close()


def test_password_change_revokes_all_existing_tokens(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        first, context = admin(api)
        second = api.auth.login("admin", "admin-pass")
        api.auth.change_password(context, "admin-pass", "new-admin-pass")
        for token in (first.access_token, second.access_token):
            with pytest.raises(InternalAuthenticationError):
                api.authenticate(token)
        assert api.auth.login("admin", "new-admin-pass").user.username == "admin"
    finally:
        connection.close()


def test_authentication_errors_do_not_echo_credentials(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        secret = "correct horse battery staple"
        api.auth.initial_admin("admin", "Admin", secret)
        with pytest.raises(InternalAuthenticationError) as error:
            api.auth.login("admin", secret + "-wrong")
        assert secret not in str(error.value)
        assert secret not in repr(error.value)
    finally:
        connection.close()
