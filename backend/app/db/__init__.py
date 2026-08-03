"""
HHMS Database Package
=====================

Exports the database foundation components used throughout
the HHMS application.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from .base import Base, BaseModel
from .init_db import create_database, drop_database
from .session import (
    get_db,
    get_engine,
    get_session_factory,
)

__all__ = [
    "Base",
    "BaseModel",
    "get_engine",
    "get_session_factory",
    "get_db",
    "create_database",
    "drop_database",
]