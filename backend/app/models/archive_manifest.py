"""Yearly archive manifest for HHMS historical data."""
from __future__ import annotations
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class ArchiveManifest(Base):
    __tablename__ = "ArchiveManifest"
    __table_args__ = (UniqueConstraint("archive_year", name="uq_archive_manifest_year"),)
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    archive_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    storage_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="online", index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

__all__=["ArchiveManifest"]
