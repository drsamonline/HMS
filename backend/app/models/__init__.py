"""
HHMS ORM Model Package
======================

Central registry and public exports for all SQLAlchemy ORM models
used by the Hospital Homoeopathic Management System.

Importing the entity models from this module ensures that their
tables are registered with the application's declarative metadata.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from .base import Base, NAMING_CONVENTION, metadata
from .department import Department
from .designation import Designation
from .mixins import (
    ActiveMixin,
    AuditMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from .permission import Permission
from .role import Role
from .role_permission import RolePermission
from .user import User
from .user_role import UserRole
from .medicine import Medicine
from .prescription import Prescription
from .prescription_item import PrescriptionItem

__all__ = [
    # SQLAlchemy foundation
    "Base",
    "metadata",
    "NAMING_CONVENTION",

    # Shared model mixins
    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "ActiveMixin",
    "SoftDeleteMixin",
    "AuditMixin",

    # Core identity and RBAC entities
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",

    # Hospital master entities
    "Department",
    "Designation",
]    # Clinical prescription and pharmacy
    "Prescription",
    "PrescriptionItem",
    "Medicine",