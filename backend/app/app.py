"""
HHMS Application Bootstrap
==========================

Creates and configures the FastAPI application.

Application bootstrap is responsible only for assembling the
application components. Business logic belongs to services,
database access belongs to repositories, and HTTP endpoints belong
to API routers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.middleware import (
    ProcessTimeMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    register_exception_handlers,
)


def create_application() -> FastAPI:
    """
    Create and configure the HHMS FastAPI application.

    Returns
    -------
    FastAPI
        Fully configured FastAPI application instance.
    """

    settings = get_settings()

    logger = configure_logging()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_middleware(
        RequestIDMiddleware,
    )

    application.add_middleware(
        ProcessTimeMiddleware,
    )

    application.add_middleware(
        RequestLoggingMiddleware,
        logger=logger,
    )

    register_exception_handlers(application)

    return application


app = create_application()


__all__ = [
    "app",
    "create_application",
]