"""Inbox idea-capture application service."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from openipe.core.errors import NotFoundError, ValidationError
from openipe.core.models.inbox import InboxItem, InboxStatus
from openipe.persistence.repositories.inbox_repository import InboxRepository


class InboxService:
    def __init__(self, connection: sqlite3.Connection):
        self.repository = InboxRepository(connection)

    def create(self, user_id: int, text: str) -> InboxItem:
        normalized_text = _validate_text(text)
        return self.repository.create(user_id, normalized_text)

    def list(self, user_id: int, status: InboxStatus | None = None) -> list[InboxItem]:
        return self.repository.list(user_id, status)

    def get(self, user_id: int, item_id: int) -> InboxItem:
        item = self.repository.get(user_id, item_id)
        if item is None:
            raise NotFoundError("Inbox item not found")
        return item

    def update(
        self,
        user_id: int,
        item_id: int,
        text: str | None = None,
        status: InboxStatus | None = None,
    ) -> InboxItem:
        item = self.get(user_id, item_id)
        normalized_text = _validate_text(text) if text is not None else item.text
        new_status = status or item.status
        now = datetime.now(UTC)
        processed_at = item.processed_at
        archived_at = item.archived_at
        if new_status == InboxStatus.PROCESSED:
            processed_at = processed_at or now
            archived_at = None
        elif new_status == InboxStatus.ARCHIVED:
            archived_at = archived_at or now
        elif new_status == InboxStatus.UNPROCESSED:
            processed_at = None
            archived_at = None
        elif new_status == InboxStatus.DISCARDED:
            processed_at = None
            archived_at = None
        return self.repository.update(
            user_id, item_id, normalized_text, new_status, processed_at, archived_at
        )

    def delete(self, user_id: int, item_id: int) -> InboxItem:
        return self.update(user_id, item_id, status=InboxStatus.ARCHIVED)


def _validate_text(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise ValidationError("Inbox text must not be empty")
    return normalized
