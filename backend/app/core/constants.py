"""
HHMS Core Constants

Application-wide immutable constants.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from enum import Enum


APP_ENCODING = "utf-8"

API_V1 = "/api/v1"

DEFAULT_TIMEZONE = "Asia/Kolkata"

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_PAGE_SIZE = 20

MAX_PAGE_SIZE = 100

PASSWORD_MIN_LENGTH = 8


class Environment(str, Enum):
    """Application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class UserRole(str, Enum):
    """System user roles."""

    ADMIN = "admin"

    SUPER_ADMIN = "super_admin"

    DOCTOR = "doctor"

    RMO = "rmo"

    RECEPTIONIST = "receptionist"

    PHARMACIST = "pharmacist"

    LAB_TECHNICIAN = "lab_technician"

    ACCOUNTANT = "accountant"

    NURSE = "nurse"

    STORE_MANAGER = "store_manager"

    HR = "hr"

    PATIENT = "patient"


class Gender(str, Enum):
    """Gender values."""

    MALE = "male"

    FEMALE = "female"

    OTHER = "other"


class RecordStatus(str, Enum):
    """Common database record status."""

    ACTIVE = "active"

    INACTIVE = "inactive"

    ARCHIVED = "archived"

    DELETED = "deleted"


class AppointmentStatus(str, Enum):
    """Patient appointment status."""

    SCHEDULED = "scheduled"

    CHECKED_IN = "checked_in"

    CONSULTING = "consulting"

    COMPLETED = "completed"

    CANCELLED = "cancelled"

    NO_SHOW = "no_show"


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"

    PARTIAL = "partial"

    PAID = "paid"

    REFUNDED = "refunded"

    CANCELLED = "cancelled"


class VisitType(str, Enum):
    """Visit types."""

    OPD = "opd"

    IPD = "ipd"

    EMERGENCY = "emergency"

    FOLLOW_UP = "follow_up"


class InventoryTransaction(str, Enum):
    """Inventory transaction types."""

    PURCHASE = "purchase"

    SALE = "sale"

    RETURN = "return"

    ADJUSTMENT = "adjustment"

    CONSUMPTION = "consumption"


class AuditAction(str, Enum):
    """Audit trail actions."""

    CREATE = "create"

    UPDATE = "update"

    DELETE = "delete"

    LOGIN = "login"

    LOGOUT = "logout"

    EXPORT = "export"