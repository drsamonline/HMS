"""HHMS configurable department service/subsection model."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.mixins import AuditMixin, UUIDPrimaryKeyMixin


class DepartmentService(Base, UUIDPrimaryKeyMixin, AuditMixin):
    """A configurable service/subsection belonging to a department."""

    __tablename__ = "department_services"

    department_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("departments.id", name="fk_department_services_department"),
        nullable=False,
        index=True,
    )
    parent_service_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "department_services.id",
            name="fk_department_services_parent",
        ),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_type: Mapped[str] = mapped_column(
        String(30), nullable=False, default="service", server_default="service"
    )
    supports_gender_breakdown: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    supports_new_old: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    supports_fulfillment_mode: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    def __repr__(self) -> str:
        return f"DepartmentService(code={self.code!r}, name={self.name!r})"


__all__ = ["DepartmentService"]
