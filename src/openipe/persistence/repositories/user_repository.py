"""User and authentication-token persistence."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from openipe.core.models.user import User


class UserRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def count(self) -> int:
        return self.connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    def create(
        self,
        username: str,
        display_name: str,
        password_hash: str,
        is_admin: bool = False,
    ) -> User:
        now = _timestamp(datetime.now(UTC))
        cursor = self.connection.execute(
            """
            INSERT INTO users(
                username, display_name, password_hash, is_admin, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, display_name, password_hash, int(is_admin), now, now),
        )
        self.connection.commit()
        return self.get_by_id(cursor.lastrowid)

    def get_by_id(self, user_id: int) -> User | None:
        row = self.connection.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return _to_user(row) if row else None

    def get_by_username(self, username: str) -> User | None:
        row = self.connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return _to_user(row) if row else None

    def list(self) -> list[User]:
        rows = self.connection.execute("SELECT * FROM users ORDER BY id").fetchall()
        return [_to_user(row) for row in rows]

    def set_last_login(self, user_id: int, when: datetime) -> None:
        self.connection.execute(
            "UPDATE users SET last_login_at = ?, updated_at = ? WHERE id = ?",
            (_timestamp(when), _timestamp(when), user_id),
        )
        self.connection.commit()

    def set_active(self, user_id: int, active: bool) -> None:
        now = _timestamp(datetime.now(UTC))
        self.connection.execute(
            "UPDATE users SET is_active = ?, updated_at = ? WHERE id = ?",
            (int(active), now, user_id),
        )
        self.connection.commit()

    def update_display_name(self, user_id: int, display_name: str) -> None:
        now = _timestamp(datetime.now(UTC))
        self.connection.execute(
            "UPDATE users SET display_name = ?, updated_at = ? WHERE id = ?",
            (display_name, now, user_id),
        )
        self.connection.commit()

    def update_password(self, user_id: int, password_hash: str) -> None:
        now = _timestamp(datetime.now(UTC))
        self.connection.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (password_hash, now, user_id),
        )
        self.connection.commit()


class AuthTokenRepository:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection

    def create(self, user_id: int, token_hash: str, expires_at: datetime) -> None:
        self.connection.execute(
            """
            INSERT INTO auth_tokens(user_id, token_hash, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                token_hash,
                _timestamp(datetime.now(UTC)),
                _timestamp(expires_at),
            ),
        )
        self.connection.commit()

    def get_user_id(self, token_hash: str, now: datetime) -> int | None:
        row = self.connection.execute(
            """
            SELECT user_id FROM auth_tokens
            WHERE token_hash = ? AND revoked_at IS NULL AND expires_at > ?
            """,
            (token_hash, _timestamp(now)),
        ).fetchone()
        return row[0] if row else None

    def revoke(self, token_hash: str, when: datetime) -> None:
        self.connection.execute(
            "UPDATE auth_tokens SET revoked_at = ? WHERE token_hash = ? AND revoked_at IS NULL",
            (_timestamp(when), token_hash),
        )
        self.connection.commit()

    def revoke_all_for_user(self, user_id: int, when: datetime) -> None:
        self.connection.execute(
            "UPDATE auth_tokens SET revoked_at = ? WHERE user_id = ? AND revoked_at IS NULL",
            (_timestamp(when), user_id),
        )
        self.connection.commit()


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def _to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        display_name=row["display_name"],
        password_hash=row["password_hash"],
        is_admin=bool(row["is_admin"]),
        is_active=bool(row["is_active"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        last_login_at=(
            datetime.fromisoformat(row["last_login_at"])
            if row["last_login_at"]
            else None
        ),
    )
