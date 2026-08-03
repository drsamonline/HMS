"""
HHMS Database Dependencies

Provides reusable FastAPI database dependency aliases.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]

__all__ = [
    "DatabaseSession",
]