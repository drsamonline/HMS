"""
Version 1 API router for HHMS.

This module defines the root API router for version 1 of the HHMS API
and registers all endpoint routers belonging to this version.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router)

__all__ = [
    "api_router",
]