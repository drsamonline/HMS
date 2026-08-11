"""
HHMS API v1 Router
==================

Root API router for version 1 of the HHMS API.

Individual endpoint routers are registered here. Business logic
must remain in the Service Layer and database access must remain
in the Repository Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router


api_router = APIRouter()

api_router.include_router(
    health_router,
)

api_router.include_router(
    auth_router,
)


__all__ = [
    "api_router",
]