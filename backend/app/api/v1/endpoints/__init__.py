"""
API endpoint package exports for HHMS API v1.

This package exposes all endpoint routers that belong to
version 1 of the HHMS API.
"""

from __future__ import annotations

from .health import router as health_router

__all__ = [
    "health_router",
]