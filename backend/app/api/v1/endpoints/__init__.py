"""
HHMS API v1 Endpoints Package
=============================

Endpoint package for version 1 of the HHMS API.

Individual endpoint routers are registered by
``app.api.v1.api``.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router

__all__ = [
    "auth_router",
    "health_router",
]