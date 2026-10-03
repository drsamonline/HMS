"""
HHMS Core Package
=================

Exports the core utilities used throughout the HHMS application.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from .constants import (
    API_V1,
    APP_ENCODING,
    DEFAULT_DATE_FORMAT,
    DEFAULT_DATETIME_FORMAT,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TIMEZONE,
    MAX_PAGE_SIZE,
    PASSWORD_MIN_LENGTH,
    AppointmentStatus,
    AuditAction,
    Environment,
    Gender,
    InventoryTransaction,
    PaymentStatus,
    RecordStatus,
    UserRole,
    VisitType,
)
from .exceptions import (
    AuditException,
    AuthenticationException,
    AuthorizationException,
    BusinessRuleException,
    ConfigurationException,
    DatabaseException,
    DuplicateResourceException,
    ExternalServiceException,
    FileStorageException,
    HHMSException,
    ReportGenerationException,
    ResourceNotFoundException,
    ValidationException,
)
from .security import (
    hash_password,
    needs_rehash,
    verify_password,
)
from .utils import (
    chunks,
    generate_uuid,
    is_blank,
    normalize_string,
    remove_none_values,
    utc_now,
)

__all__ = [
    # Constants
    "API_V1",
    "APP_ENCODING",
    "DEFAULT_TIMEZONE",
    "DEFAULT_DATE_FORMAT",
    "DEFAULT_DATETIME_FORMAT",
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "PASSWORD_MIN_LENGTH",
    # Enums
    "Environment",
    "UserRole",
    "Gender",
    "RecordStatus",
    "AppointmentStatus",
    "PaymentStatus",
    "VisitType",
    "InventoryTransaction",
    "AuditAction",
    # Exceptions
    "HHMSException",
    "ValidationException",
    "AuthenticationException",
    "AuthorizationException",
    "ResourceNotFoundException",
    "DuplicateResourceException",
    "DatabaseException",
    "ConfigurationException",
    "BusinessRuleException",
    "FileStorageException",
    "ExternalServiceException",
    "AuditException",
    "ReportGenerationException",
    # Security
    "hash_password",
    "verify_password",
    "needs_rehash",
    # Utilities
    "utc_now",
    "generate_uuid",
    "is_blank",
    "normalize_string",
    "remove_none_values",
    "chunks",
]