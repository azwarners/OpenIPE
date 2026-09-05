import pytest

from openipe.api.internal.errors import InternalNotFoundError, InternalPermissionDeniedError
from tests.internal_support import admin, make_internal


def test_admin_user_operations_and_authorization(tmp_path):
    api, connection = make_internal(tmp_path)
    try:
        _, context = admin(api)
        user = api.users.create(context, "user", "User", "user-pass")
        assert api.users.get(context, user.id).username == "user"
        assert len(api.users.list(context)) == 2
        token = api.auth.login("user", "user-pass").access_token
        with pytest.raises(InternalPermissionDeniedError):
            api.authorize_admin(api.authenticate(token))
        with pytest.raises(InternalNotFoundError):
            api.users.get(context, 9999)
    finally:
        connection.close()
