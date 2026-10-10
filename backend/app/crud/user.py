"""
HHMS User CRUD Compatibility Layer
===================================

Backward-compatible aliases for the legacy User CRUD interface.

The active HHMS architecture uses:

    API
      ↓
    Service
      ↓
    Repository
      ↓
    Database

User-specific persistence is now implemented by
``app.repositories.user.UserRepository``.

This module is retained temporarily so existing imports of
``UserCRUD`` and ``user_crud`` do not break while the application
transitions completely to the Repository/Service architecture.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.repositories.user import (
    UserRepository,
    user_repository,
)


UserCRUD = UserRepository

user_crud = user_repository


__all__ = [
    "UserCRUD",
    "user_crud",
]