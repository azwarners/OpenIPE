"""Transport-independent local API for OpenIPE first-party clients."""

from .api import InternalAPI
from .context import InternalContext
from .errors import (
    InternalAPIError, InternalAuthenticationError, InternalInactiveUserError,
    InternalNotFoundError, InternalPermissionDeniedError, InternalValidationError,
)

__all__ = [
    "InternalAPI", "InternalContext", "InternalAPIError", "InternalAuthenticationError",
    "InternalInactiveUserError", "InternalNotFoundError", "InternalPermissionDeniedError",
    "InternalValidationError",
]
