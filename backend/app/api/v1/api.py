"""
HHMS API v1 Router
==================

Root API router for version 1 of the HHMS API.

Individual endpoint routers are registered here. Business logic
must remain in the Service Layer and database access must remain
in the Repository Layer.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.patients import router as patients_router
from app.api.v1.endpoints.visits import router as visits_router
from app.api.v1.endpoints.opd_tokens import (
    router as opd_tokens_router,
)

from app.api.v1.endpoints.prescriptions import (
    router as prescriptions_router,
)
from app.api.v1.endpoints.medicines import (
    router as medicines_router,
)

from app.api.v1.endpoints.medicine_batches import (
    router as medicine_batches_router,
)

api_router = APIRouter()

api_router.include_router(
    health_router,
)

api_router.include_router(
    auth_router,
)

api_router.include_router(
    patients_router,
)

api_router.include_router(
    visits_router,
)

api_router.include_router(
    opd_tokens_router,
)

api_router.include_router(
    prescriptions_router,
)

api_router.include_router(
    medicines_router,
)

api_router.include_router(
    medicine_batches_router,
)

__all__ = [
    "api_router",
]