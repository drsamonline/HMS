"""HHMS user-role association ORM model."""
from __future__ import annotations
from sqlalchemy import ForeignKey, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class UserRole(Base):
    __tablename__ = "UserRole"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("User.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("Role.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("User.id", ondelete="SET NULL"), nullable=True)
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_role_user_role"),)

__all__ = ["UserRole"]
