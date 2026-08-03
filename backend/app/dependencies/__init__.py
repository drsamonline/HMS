"""
HHMS Dependency Package
=======================

Centralized exports for reusable FastAPI dependencies.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from .auth import (
    CurrentUser,
    CurrentUserDependency,
    get_current_user,
)
from .database import DatabaseSession

__all__ = [
    "CurrentUser",
    "CurrentUserDependency",
    "DatabaseSession",
    "get_current_user",
]