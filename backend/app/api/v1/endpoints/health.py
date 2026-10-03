"""
HHMS Health Endpoints
=====================

Provides liveness, readiness and general health endpoints used
by deployment platforms, load balancers and monitoring systems.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config.settings import get_settings
from app.network.discovery import server_id
from app.schemas.health import HealthResponse
from app.services.maintenance import maintenance_service


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


def _response() -> HealthResponse:
    """
    Create the standard health response.

    Returns
    -------
    HealthResponse
        Current application health information.
    """

    settings = get_settings()

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

    A successful response indicates that the application
    process is running and able to handle requests.

    Returns
    -------
    HealthResponse
        Current application liveness information.
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

    The current readiness contract verifies that the application
    endpoint itself is operational. External dependency checks
    are intentionally not introduced until a formal readiness
    contract is defined.

    Returns
    -------
    HealthResponse
        Current application readiness information.
    """

    return _response()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Status",
)
async def health() -> HealthResponse:
    """
    Return general application health.

    Returns
    -------
    HealthResponse
        Current application health information.
    """

    return _response()


@router.get("/system", summary="Live system health")
async def system_health() -> dict[str, object]:
    return await maintenance_service.health()


__all__ = [
    "router",
]

@router.get(
    "/discovery",
    summary="LAN Discovery Information",
)
async def discovery_info() -> dict[str, object]:
    """Return the connection metadata used by HHMS LAN clients."""
    settings = get_settings()
    return {
        "protocol": "hhms-lan-v1",
        "enabled": settings.DISCOVERY_ENABLED,
        "server_id": server_id(),
        "name": settings.DISCOVERY_NAME,
        "http_port": int(settings.SERVER_PORT),
        "discovery_port": int(settings.DISCOVERY_PORT),
        "api_base": settings.API_V1_PREFIX,
    }
