"""
HHMS Custom Exceptions

Defines the custom exception hierarchy used throughout the
Hospital Homoeopathic Management System (HHMS).

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations


class HHMSException(Exception):
    """
    Base exception for the HHMS application.
    """

    default_message = "An unexpected application error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class ValidationException(HHMSException):
    """Raised when validation fails."""

    default_message = "Validation failed."


class AuthenticationException(HHMSException):
    """Raised when authentication fails."""

    default_message = "Authentication failed."


class AuthorizationException(HHMSException):
    """Raised when authorization fails."""

    default_message = "Permission denied."


class ResourceNotFoundException(HHMSException):
    """Raised when a requested resource cannot be found."""

    default_message = "Requested resource was not found."


class DuplicateResourceException(HHMSException):
    """Raised when attempting to create a duplicate resource."""

    default_message = "Resource already exists."


class DatabaseException(HHMSException):
    """Raised for database-related errors."""

    default_message = "Database operation failed."


class ConfigurationException(HHMSException):
    """Raised when application configuration is invalid."""

    default_message = "Application configuration error."


class BusinessRuleException(HHMSException):
    """Raised when a business rule is violated."""

    default_message = "Business rule violation."


class FileStorageException(HHMSException):
    """Raised for file storage errors."""

    default_message = "File storage operation failed."


class ExternalServiceException(HHMSException):
    """Raised when an external service call fails."""

    default_message = "External service error."


class AuditException(HHMSException):
    """Raised when audit operations fail."""

    default_message = "Audit operation failed."


class ReportGenerationException(HHMSException):
    """Raised when report generation fails."""

    default_message = "Report generation failed."