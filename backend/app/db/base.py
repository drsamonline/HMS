"""
HHMS Database Base

Imports all SQLAlchemy ORM models so that they are registered
with SQLAlchemy metadata and Alembic autogeneration.

During the initial project phase this module only exposes the
declarative base. Model imports will be added as modules are
implemented.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.db.base_class import Base, BaseModel

__all__ = [
    "Base",
    "BaseModel",
]

# ---------------------------------------------------------------------
# Future Model Imports
# ---------------------------------------------------------------------
#
# Import every ORM model below as they are implemented.
#
# Example:
#
# from app.models.patient import Patient
# from app.models.doctor import Doctor
# from app.models.visit import Visit
#
# These imports intentionally remain absent until the corresponding
# packages are created to avoid circular dependencies and unnecessary
# import errors.
#
# ---------------------------------------------------------------------