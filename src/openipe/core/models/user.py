"""User domain model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class User:
    id: int
    username: str
    display_name: str
    password_hash: str
    is_admin: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
