from datetime import UTC, datetime, timedelta

import pytest

from openipe.application.auth_service import AuthService
from openipe.core.config import Settings
from openipe.core.errors import (
    AuthenticationError,
    InactiveUserError,
    PermissionDeniedError,
    ValidationError,
)
from openipe.core.security import hash_password, verify_password
from openipe.persistence.database import initialize_database


def service(tmp_path, token_expiration=3600):
    connection = initialize_database(tmp_path / "openipe.sqlite3")
    settings = Settings(token_expiration=token_expiration)
    return connection, AuthService(connection, settings)


def test_password_hashes_are_salted_and_verifiable():
    first = hash_password("correct horse battery staple")
    second = hash_password("correct horse battery staple")
    assert first != second
    assert verify_password("correct horse battery staple", first)
    assert not verify_password("wrong password", first)
    assert not verify_password("correct horse battery staple", "invalid")


def test_initial_admin_is_one_time_only(tmp_path):
    connection, auth = service(tmp_path)
    try:
        admin = auth.create_initial_admin("admin", "Administrator", "admin-pass")
        assert admin.is_admin
        with pytest.raises(ValidationError, match="already been created"):
            auth.create_initial_admin("other", "Other", "other-pass")
    finally:
        connection.close()


def test_login_token_me_current_user_and_logout(tmp_path):
    connection, auth = service(tmp_path)
    try:
        admin = auth.create_initial_admin("admin", "Administrator", "admin-pass")
        user, token, expires_at = auth.login("admin", "admin-pass")
        assert user.id == admin.id
        assert expires_at > datetime.now(UTC)
        assert auth.current_user(token).id == admin.id
        auth.logout(token)
        with pytest.raises(AuthenticationError):
            auth.current_user(token)
    finally:
        connection.close()


def test_login_rejects_bad_password_and_inactive_user(tmp_path):
    connection, auth = service(tmp_path)
    try:
        admin = auth.create_initial_admin("admin", "Administrator", "admin-pass")
        with pytest.raises(AuthenticationError):
            auth.login("admin", "bad-pass")
        user = auth.create_user(admin, "user", "User", "user-pass")
        auth.set_active(admin, user.id, False)
        with pytest.raises(InactiveUserError):
            auth.login("user", "user-pass")
    finally:
        connection.close()


def test_expired_token_is_rejected(tmp_path):
    connection, auth = service(tmp_path, token_expiration=-1)
    try:
        auth.create_initial_admin("admin", "Administrator", "admin-pass")
        _, token, _ = auth.login("admin", "admin-pass")
        with pytest.raises(AuthenticationError):
            auth.current_user(token)
    finally:
        connection.close()


def test_password_change_revokes_existing_tokens(tmp_path):
    connection, auth = service(tmp_path)
    try:
        user = auth.create_initial_admin("admin", "Administrator", "admin-pass")
        _, token, _ = auth.login("admin", "admin-pass")
        auth.change_password(user, "admin-pass", "new-admin-pass")
        with pytest.raises(AuthenticationError):
            auth.current_user(token)
        logged_in, _, _ = auth.login("admin", "new-admin-pass")
        assert logged_in.id == user.id
    finally:
        connection.close()


def test_admin_user_management_and_permissions(tmp_path):
    connection, auth = service(tmp_path)
    try:
        admin = auth.create_initial_admin("admin", "Administrator", "admin-pass")
        user = auth.create_user(admin, "user", "User", "user-pass")
        assert auth.list_users(admin) == [admin, user]
        with pytest.raises(PermissionDeniedError):
            auth.create_user(user, "other", "Other", "other-pass")
        auth.set_active(admin, user.id, False)
        assert not auth.get_user(admin, user.id).is_active
        with pytest.raises(ValidationError, match="own account"):
            auth.set_active(admin, admin.id, False)
    finally:
        connection.close()


@pytest.mark.parametrize(
    "username,display_name,password",
    [("", "Name", "valid-pass"), ("user", "", "valid-pass"), ("user", "User", "short")],
)
def test_user_validation(tmp_path, username, display_name, password):
    connection, auth = service(tmp_path)
    try:
        with pytest.raises(ValidationError):
            auth.create_initial_admin(username, display_name, password)
    finally:
        connection.close()
