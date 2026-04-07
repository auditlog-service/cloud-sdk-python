"""Custom exceptions for SAP Audit Log NG (OTLP/gRPC) Service."""


class AuditLogNGError(Exception):
    """Base exception for audit log NG operations."""

    pass


class ClientCreationError(AuditLogNGError):
    """Raised when audit log NG client creation fails."""

    pass


class TransportError(AuditLogNGError):
    """Raised when gRPC transport operations fail."""

    pass


class ValidationError(AuditLogNGError):
    """Raised when audit event validation fails."""

    pass
