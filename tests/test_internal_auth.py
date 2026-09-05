import pytest

from openipe.api.internal.errors import InternalAuthenticationError, InternalInactiveUserError, InternalValidationError
from tests.internal_support import admin, make_internal


def test_internal_authentication_and_revocation(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        result, context = admin(api)
        assert api.auth.current_user(context).username == "admin"
        api.auth.logout(result.access_token)
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(result.access_token)
    finally:
        connection.close()


def test_initial_admin_and_password_change_are_internal(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        result, context = admin(api)
        with pytest.raises(InternalValidationError):
            api.auth.initial_admin("other", "Other", "other-pass")
        api.auth.change_password(context, "admin-pass", "new-admin-pass")
        with pytest.raises(InternalAuthenticationError):
            api.authenticate(result.access_token)
    finally:
        connection.close()


def test_invalid_and_inactive_authentication_are_public_errors(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        with pytest.raises(InternalAuthenticationError):
            api.auth.login("admin", "wrong-password")
        user = api.users.create(context, "inactive", "Inactive", "inactive-pass")
        api.users.update(context, user.id, is_active=False)
        with pytest.raises(InternalInactiveUserError):
            api.auth.login("inactive", "inactive-pass")
    finally:
        connection.close()
