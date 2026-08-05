"""Authentication and user-account application services."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from openipe.core.config import Settings
from openipe.core.errors import (
    AuthenticationError,
    InactiveUserError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from openipe.core.models.user import User
from openipe.core.security import generate_token, hash_password, hash_token, verify_password
from openipe.persistence.repositories.user_repository import AuthTokenRepository, UserRepository


class AuthService:
    def __init__(self, connection: sqlite3.Connection, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.users = UserRepository(connection)
        self.tokens = AuthTokenRepository(connection)

    def create_initial_admin(self, username: str, display_name: str, password: str) -> User:
        if self.users.count() > 0:
            raise ValidationError("The initial administrator has already been created")
        return self._create_user(username, display_name, password, is_admin=True)

    def login(self, username: str, password: str) -> tuple[User, str, datetime]:
        user = self.users.get_by_username(username.strip())
        if user is None or not verify_password(password, user.password_hash):
            raise AuthenticationError("Invalid username or password")
        if not user.is_active:
            raise InactiveUserError("User account is inactive")
        now = datetime.now(UTC)
        self.users.set_last_login(user.id, now)
        token = generate_token()
        expires_at = now + timedelta(seconds=self.settings.token_expiration)
        self.tokens.create(user.id, hash_token(token), expires_at)
        return self.users.get_by_id(user.id), token, expires_at

    def logout(self, token: str) -> None:
        self.tokens.revoke(hash_token(token), datetime.now(UTC))

    def current_user(self, token: str) -> User:
        user_id = self.tokens.get_user_id(hash_token(token), datetime.now(UTC))
        if user_id is None:
            raise AuthenticationError("Invalid or expired access token")
        user = self.users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid or expired access token")
        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise AuthenticationError("Current password is incorrect")
        _validate_password(new_password)
        self.users.update_password(user.id, hash_password(new_password))
        self.tokens.revoke_all_for_user(user.id, datetime.now(UTC))

    def create_user(
        self,
        actor: User,
        username: str,
        display_name: str,
        password: str,
        is_admin: bool = False,
    ) -> User:
        self._require_admin(actor)
        return self._create_user(username, display_name, password, is_admin)

    def set_active(self, actor: User, user_id: int, active: bool) -> User:
        self._require_admin(actor)
        target = self.users.get_by_id(user_id)
        if target is None:
            raise NotFoundError("User not found")
        if target.id == actor.id and not active:
            raise ValidationError("An administrator cannot deactivate their own account")
        self.users.set_active(user_id, active)
        if not active:
            self.tokens.revoke_all_for_user(user_id, datetime.now(UTC))
        return self.users.get_by_id(user_id)

    def get_user(self, actor: User, user_id: int) -> User:
        self._require_admin(actor)
        user = self.users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    def list_users(self, actor: User) -> list[User]:
        self._require_admin(actor)
        return self.users.list()

    def _create_user(
        self, username: str, display_name: str, password: str, is_admin: bool
    ) -> User:
        normalized_username = username.strip()
        normalized_display_name = display_name.strip()
        if not normalized_username:
            raise ValidationError("Username must not be empty")
        if not normalized_display_name:
            raise ValidationError("Display name must not be empty")
        _validate_password(password)
        try:
            return self.users.create(
                normalized_username,
                normalized_display_name,
                hash_password(password),
                is_admin,
            )
        except sqlite3.IntegrityError as error:
            if "users.username" in str(error) or "username" in str(error):
                raise ValidationError("Username is already in use") from error
            raise

    @staticmethod
    def _require_admin(actor: User) -> None:
        if not actor.is_active or not actor.is_admin:
            raise PermissionDeniedError("Administrator permission is required")


def _validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
