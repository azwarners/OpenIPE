"""Authenticated actor context shared by local clients."""

from dataclasses import dataclass

from openipe.core.models.user import User


@dataclass(frozen=True, slots=True)
class InternalContext:
    """The authenticated actor resolved by :class:`InternalAPI`."""

    actor: User
