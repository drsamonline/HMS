"""
HHMS CRUD package.

Provides reusable CRUD infrastructure for all database entities.

Future entity-specific CRUD classes should inherit from CRUDBase.
"""

from __future__ import annotations

from app.crud.base import CRUDBase

__all__ = [
    "CRUDBase",
]