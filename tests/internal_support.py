from openipe.api.internal import InternalAPI
from openipe.core.config import Settings
from openipe.persistence.database import initialize_database


def make_internal(tmp_path):
    connection = initialize_database(tmp_path / "internal.sqlite3")
    api = InternalAPI(connection, Settings(database_path=tmp_path / "internal.sqlite3"))
    return api, connection


def admin(api):
    api.auth.initial_admin("admin", "Administrator", "admin-pass")
    result = api.auth.login("admin", "admin-pass")
    return result, api.authenticate(result.access_token)
