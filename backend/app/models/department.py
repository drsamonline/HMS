"""
Department ORM model for HHMS.

Represents an organizational department within the hospital.
"""

from __future__ import annotations

from sqlalchemy import Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DepartmentType
from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class Department(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Hospital department.
    """

    __tablename__ = "departments"

    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_departments_code",
        ),
        UniqueConstraint(
            "name",
            name="uq_departments_name",
        ),
    )

    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    department_type: Mapped[DepartmentType] = mapped_column(
        Enum(
            DepartmentType,
            name="department_type_enum",
        ),
        nullable=False,
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            "Department("
            f"code={self.code!r}, "
            f"name={self.name!r}"
            ")"
        )


__all__ = [
    "Department",
]