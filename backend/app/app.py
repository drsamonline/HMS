"""
HHMS Application Bootstrap
==========================

Creates and configures the single FastAPI application instance.

Application bootstrap is responsible only for assembling the
application components. Business logic belongs to services,
database access belongs to repositories, and HTTP endpoints belong
to API routers.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations
from contextlib import asynccontextmanager
from app.services.maintenance_scheduler import maintenance_scheduler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.config.logging import configure_logging
from app.config.settings import get_settings
from app.middleware import (
    ProcessTimeMiddleware,
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestLoggingMiddleware,
    register_exception_handlers,
)


@asynccontextmanager
async def _lifespan(_application):
    await maintenance_scheduler.start()
    try:
        yield
    finally:
        await maintenance_scheduler.stop()

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
        lifespan=_lifespan,
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

    # Outermost layer: brute-force throttle on the login route. Being
    # added last it wraps every inner middleware and rejects over-budget
    # attempts before they ever reach authentication work (Argon2).
    application.add_middleware(
        RateLimitMiddleware,
        limit=settings.LOGIN_RATE_LIMIT_ATTEMPTS,
        window_seconds=float(settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS),
    )

    register_exception_handlers(application)

    application.include_router(
        api_router,
        prefix=settings.API_V1_PREFIX,
    )

    _register_favicon_route(application)
    _mount_frontend(application)

    return application


def _register_favicon_route(application: FastAPI) -> None:
    """Serve the HHMS favicon at /favicon.ico.

    Browsers request ``/favicon.ico`` automatically; without an explicit
    handler this produced a noisy 404.  The bundled SVG icon is served
    with the correct media type regardless of whether the static GUI
    bundle is mounted, and every other common browser icon path falls
    back to the same file via the frontend mount below.
    """
    from pathlib import Path

    from fastapi import Response

    from app.config.runtime_paths import frontend_directory

    candidates = []
    root = frontend_directory()
    if root is not None:
        candidates.append(Path(root) / "favicon.svg")
    # Fallback for API-only deployments that still ship the repo layout.
    candidates.append(Path(__file__).resolve().parents[2] / "frontend" / "favicon.svg")

    icon_path = next((p for p in candidates if p.is_file()), None)
    if icon_path is None:  # pragma: no cover - icon missing from checkout
        return

    icon_bytes = icon_path.read_bytes()

    @application.get("/favicon.ico", include_in_schema=False)
    async def favicon() -> Response:
        return Response(
            content=icon_bytes,
            media_type="image/svg+xml",
            headers={"Cache-Control": "public, max-age=86400"},
        )


def _mount_frontend(application: FastAPI) -> None:
    """Serve the bundled HHMS GUI so the app is usable from a browser.

    The static client (``frontend/``) talks to the same origin under
    ``/api/v1``, which also keeps CORS irrelevant for the portable
    single-machine deployment.  When no bundle is present the server
    simply stays API-only.
    """
    from app.config.runtime_paths import frontend_directory

    root = frontend_directory()
    if root is None:
        return

    from fastapi.staticfiles import StaticFiles

    # html=True => "/" serves index.html and unknown paths fall back to it.
    application.mount("/", StaticFiles(directory=str(root), html=True), name="hhms-ui")


app = create_application()


__all__ = [
    "app",
    "create_application",
]