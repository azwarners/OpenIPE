"""Transport-independent errors exposed by the internal API."""


class InternalAPIError(Exception):
    """Base class for errors that are meaningful to local API consumers."""


class InvalidContextError(InternalAPIError):
    """Raised when a protected operation receives no authenticated context."""


class InternalAuthenticationError(InternalAPIError):
    """Authentication failed or a presented token is invalid."""


class InternalInactiveUserError(InternalAPIError):
    """The requested operation targets an inactive account."""


class InternalPermissionDeniedError(InternalAPIError):
    """The authenticated actor lacks permission for an operation."""


class InternalNotFoundError(InternalAPIError):
    """A requested resource is not visible or does not exist."""


class InternalValidationError(InternalAPIError):
    """A domain validation or lifecycle rule rejected the operation."""
