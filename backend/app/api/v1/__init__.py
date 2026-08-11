"""
HHMS API v1 Package
===================

Public package interface for version 1 of the HHMS API.

The versioned API package exposes the root v1 router. Individual
endpoint routers are registered by ``app.api.v1.api``.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.api.v1.api import api_router


__all__ = [
    "api_router",
]