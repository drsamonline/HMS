"""
HHMS Application Entry Point
============================

Public ASGI entry point for the Hospital Homoeopathic Management
System.

The authoritative FastAPI application is created by
``app.app``. This module intentionally exposes that application
without creating a second FastAPI instance.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from app.app import app


__all__ = [
    "app",
]