"""
HHMS Dependency Package
=======================

Centralized exports for reusable FastAPI dependencies.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.dependencies.auth import (
    CurrentUserDependency,
    get_current_user,
)
from app.dependencies.database import DatabaseSession


__all__ = [
    "CurrentUserDependency",
    "DatabaseSession",
    "get_current_user",
]