"""
HHMS API v1 Router.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.admissions import (
    router as admissions_router,
)
from app.api.v1.endpoints.auth import (
    router as auth_router,
)
from app.api.v1.endpoints.beds import (
    router as beds_router,
)
from app.api.v1.endpoints.discharges import (
    router as discharges_router,
)
from app.api.v1.endpoints.health import (
    router as health_router,
)
from app.api.v1.endpoints.inventory_items import (
    router as inventory_items_router,
)
from app.api.v1.endpoints.medicine_batches import (
    router as medicine_batches_router,
)
from app.api.v1.endpoints.medicines import (
    router as medicines_router,
)
from app.api.v1.endpoints.opd_tokens import (
    router as opd_tokens_router,
)
from app.api.v1.endpoints.patients import (
    router as patients_router,
)
from app.api.v1.endpoints.prescriptions import (
    router as prescriptions_router,
)
from app.api.v1.endpoints.stock_transactions import (
    router as stock_transactions_router,
)
from app.api.v1.endpoints.visits import (
    router as visits_router,
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

api_router.include_router(
    inventory_items_router,
)

api_router.include_router(
    stock_transactions_router,
)

api_router.include_router(
    admissions_router,
)

api_router.include_router(
    beds_router,
)

api_router.include_router(
    discharges_router,
)


__all__ = [
    "api_router",
]