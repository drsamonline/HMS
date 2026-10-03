"""
HHMS Repository Package
=======================

Public exports for the HHMS persistence/repository layer.

Repositories are responsible for database access only.
Business logic belongs to the Service Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.repositories.base import RepositoryBase
from app.repositories.role import (
    RoleRepository,
    role_repository,
)
from app.repositories.user import (
    UserRepository,
    user_repository,
)

__all__ = [
    "RepositoryBase",
    "UserRepository",
    "user_repository",
    "RoleRepository",
    "role_repository",
]