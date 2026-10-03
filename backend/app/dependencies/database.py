"""
HHMS Database Dependencies
==========================

Reusable FastAPI dependency declarations for asynchronous
SQLAlchemy database sessions.

The actual session lifecycle is managed by ``app.db.session``.
This module only exposes the dependency interface used by
routers and services.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db


DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


__all__ = [
    "DatabaseSession",
]