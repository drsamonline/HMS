"""
HHMS API Package
================

Root API package for the Hospital Homoeopathic Management System.

The versioned API implementation is maintained under
``app.api.v1``. This package exposes the version 1 root router
as the public API entry point.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.api.v1.api import api_router


__all__ = [
    "api_router",
]