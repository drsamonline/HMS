"""
Version 1 API package for HHMS.

This package exposes the root API router for version 1.
"""

from __future__ import annotations

from .api import api_router

__all__ = [
    "api_router",
]