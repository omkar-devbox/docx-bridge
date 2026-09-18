"""Exception classes for document component handlers."""


class HandlerError(Exception):
    """Base exception for all handler errors."""
    pass


class HandlerNotFoundError(HandlerError):
    """Raised when no suitable handler can be found for a tag or type."""
    pass


class RegistrationError(HandlerError):
    """Raised when a handler fails to register or invalid registration occurs."""
    pass


class ResolutionError(HandlerError):
    """Raised when resolving a handler for an element or type fails."""
    pass


class ConversionError(HandlerError):
    """Raised when converting an element to/from JSON AST fails."""
    pass


class ValidationError(HandlerError):
    """Raised when element schema or property validation fails."""
    pass


__all__ = [
    "HandlerError",
    "HandlerNotFoundError",
    "RegistrationError",
    "ResolutionError",
    "ConversionError",
    "ValidationError",
]
