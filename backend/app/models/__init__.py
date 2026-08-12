"""
HHMS ORM Model Package.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from .admission import Admission
from .audit_log import AuditLog
from .base import (
    Base,
    NAMING_CONVENTION,
    metadata,
)
from .bed import Bed
from .department import Department
from .designation import Designation
from .dispense_record import DispenseRecord
from .dispensing_record import DispensingRecord
from .investigation import Investigation
from .investigation_result import InvestigationResult
from .inventory_item import InventoryItem
from .invoice import Invoice
from .medical_document import MedicalDocument
from .medicine import Medicine
from .medicine_batch import MedicineBatch
from .mixins import (
    ActiveMixin,
    AuditMixin,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from .opd_token import OPDToken
from .patient import Patient
from .payment import Payment
from .permission import Permission
from .prescription import Prescription
from .prescription_item import PrescriptionItem
from .role import Role
from .role_permission import RolePermission
from .stock_batch import StockBatch
from .stock_transaction import StockTransaction
from .user import User
from .user_role import UserRole
from .visit import Visit


__all__ = [
    "Base",
    "metadata",
    "NAMING_CONVENTION",

    "UUIDPrimaryKeyMixin",
    "TimestampMixin",
    "ActiveMixin",
    "SoftDeleteMixin",
    "AuditMixin",

    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",

    "Department",
    "Designation",

    "Patient",
    "Visit",
    "OPDToken",

    "Prescription",
    "PrescriptionItem",

    "Medicine",
    "MedicineBatch",
    "DispenseRecord",
    "DispensingRecord",

    "InventoryItem",
    "StockBatch",
    "StockTransaction",

    "Admission",
    "Bed",

    "Investigation",
    "InvestigationResult",

    "Invoice",
    "Payment",

    "MedicalDocument",
    "AuditLog",
]