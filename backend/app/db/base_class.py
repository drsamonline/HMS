"""
HHMS SQLAlchemy Declarative Base

Provides the abstract base class inherited by every ORM model
within the HHMS project.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


PrimaryKey = Annotated[int, mapped_column(Integer, primary_key=True, index=True)]


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    Every database model in HHMS must inherit from this class.
    """

    pass


class BaseModel(Base):
    """
    Abstract base model.

    Provides common columns shared across all database entities.
    """

    __abstract__ = True

    id: Mapped[PrimaryKey]

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp.",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last modification timestamp.",
    )