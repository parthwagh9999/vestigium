"""Custom exception hierarchy for structured error handling.

All exceptions map to specific HTTP status codes and are handled
by the global exception handlers in the main application.
"""

from __future__ import annotations


class VestigiumError(Exception):
    """Base exception for all VESTIGIUM errors."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(VestigiumError):
    """Resource not found (HTTP 404)."""

    def __init__(self, resource: str = "Resource", resource_id: str = "") -> None:
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"
        super().__init__(message=detail, status_code=404)


class AlreadyExistsError(VestigiumError):
    """Resource already exists (HTTP 409)."""

    def __init__(self, resource: str = "Resource", field: str = "", value: str = "") -> None:
        detail = f"{resource} already exists"
        if field and value:
            detail = f"{resource} with {field} '{value}' already exists"
        super().__init__(message=detail, status_code=409)


class AuthenticationError(VestigiumError):
    """Authentication failed (HTTP 401)."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message=message, status_code=401)


class AuthorizationError(VestigiumError):
    """Authorization failed — insufficient permissions (HTTP 403)."""

    def __init__(self, message: str = "You do not have permission to perform this action") -> None:
        super().__init__(message=message, status_code=403)


class ValidationError(VestigiumError):
    """Input validation error (HTTP 422)."""

    def __init__(self, message: str = "Validation error", errors: list[dict] | None = None) -> None:
        self.errors = errors or []
        super().__init__(message=message, status_code=422)


class RateLimitError(VestigiumError):
    """Rate limit exceeded (HTTP 429)."""

    def __init__(self, message: str = "Rate limit exceeded. Please try again later.") -> None:
        super().__init__(message=message, status_code=429)


class TransformError(VestigiumError):
    """Transform execution error (HTTP 500)."""

    def __init__(self, transform_name: str = "", message: str = "Transform execution failed") -> None:
        detail = f"Transform '{transform_name}' failed: {message}" if transform_name else message
        super().__init__(message=detail, status_code=500)


class PluginError(VestigiumError):
    """Plugin system error (HTTP 500)."""

    def __init__(self, plugin_id: str = "", message: str = "Plugin error") -> None:
        detail = f"Plugin '{plugin_id}': {message}" if plugin_id else message
        super().__init__(message=detail, status_code=500)


class DatabaseError(VestigiumError):
    """Database operation error (HTTP 500)."""

    def __init__(self, message: str = "A database error occurred") -> None:
        super().__init__(message=message, status_code=500)


class ExportError(VestigiumError):
    """Export operation error (HTTP 500)."""

    def __init__(self, format_name: str = "", message: str = "Export failed") -> None:
        detail = f"Export to {format_name} failed: {message}" if format_name else message
        super().__init__(message=detail, status_code=500)


class ImportError_(VestigiumError):
    """Import operation error (HTTP 400).

    Named with trailing underscore to avoid shadowing the builtin ImportError.
    """

    def __init__(self, format_name: str = "", message: str = "Import failed") -> None:
        detail = f"Import from {format_name} failed: {message}" if format_name else message
        super().__init__(message=detail, status_code=400)
