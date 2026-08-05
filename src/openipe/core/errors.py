"""Shared foundation errors."""


class OpenIPEError(Exception):
    """Base class for expected OpenIPE errors."""


class AuthenticationError(OpenIPEError):
    """Credentials or bearer token are invalid."""


class InactiveUserError(OpenIPEError):
    """The user account is inactive."""


class NotFoundError(OpenIPEError):
    """A requested record does not exist in the caller's scope."""


class PermissionDeniedError(OpenIPEError):
    """The authenticated user lacks permission for an operation."""


class ValidationError(OpenIPEError):
    """A domain value does not satisfy an application rule."""
