"""
Health endpoints for HHMS.

Provides liveness, readiness and health endpoints used by
deployment platforms, load balancers and monitoring systems.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.settings import Settings

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class HealthResponse(BaseModel):
    """Standard response returned by all health endpoints."""

    status: Literal["healthy"]
    service: str
    version: str


def _response() -> HealthResponse:
    """Create a standard health response."""

    settings = Settings.get_settings()

    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@router.get(
    "/live",
    response_model=HealthResponse,
    summary="Liveness Probe",
)
async def liveness() -> HealthResponse:
    """
    Return application liveness.

    Returns:
        HealthResponse: Indicates the process is running.
    """

    return _response()


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness Probe",
)
async def readiness() -> HealthResponse:
    """
    Return application readiness.

    Returns:
        HealthResponse: Indicates the application is ready
        to receive requests.
    """

    return _response()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Status",
)
async def health() -> HealthResponse:
    """
    Return application health.

    Returns:
        HealthResponse: General application health.
    """

    return _response()