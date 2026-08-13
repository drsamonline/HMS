"""HHMS role-permission association ORM model."""
from __future__ import annotations
from sqlalchemy import ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class RolePermission(Base):
    __tablename__ = "RolePermission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("Role.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey("Permission.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission_role_permission"),)

__all__ = ["RolePermission"]
