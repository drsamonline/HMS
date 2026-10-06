"""
Designation ORM model for HHMS.

Represents a staff designation within the hospital
organizational structure.
"""

from __future__ import annotations

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import DesignationType
from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class Designation(
    Base,
    UUIDPrimaryKeyMixin,
    AuditMixin,
):
    """
    Master entity representing a staff designation.
    """

    __tablename__ = "designations"

    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_designations_code",
        ),
        UniqueConstraint(
            "name",
            name="uq_designations_name",
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

    designation_type: Mapped[DesignationType] = mapped_column(
        ENUM(
            DesignationType,
            name="designation_type_enum",
            create_type=True,
        ),
        nullable=False,
    )

    def __repr__(self) -> str:
        """
        Return a developer-friendly representation.
        """
        return (
            "Designation("
            f"code={self.code!r}, "
            f"name={self.name!r}, "
            f"type={self.designation_type.value!r}"
            ")"
        )


__all__ = [
    "Designation",
]