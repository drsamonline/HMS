"""
HHMS Dispensing API Endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.dispense import (
    DispenseCreate,
    DispenseRead,
)
from app.services.dispense import dispense_service


router = APIRouter(
    prefix="/dispenses",
    tags=["Pharmacy Dispensing"],
)


@router.post(
    "",
    response_model=DispenseRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_dispense(
    dispense_in: DispenseCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DispenseRead:
    return await dispense_service.create(
        db,
        dispense_in,
    )


@router.get(
    "/{dispense_id}",
    response_model=DispenseRead,
)
async def get_dispense(
    dispense_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DispenseRead:
    return await dispense_service.get(
        db,
        dispense_id,
    )


@router.get(
    "/prescription-item/{prescription_item_id}",
    response_model=list[DispenseRead],
)
async def list_item_dispenses(
    prescription_item_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> list[DispenseRead]:
    return await dispense_service.list_by_prescription_item(
        db,
        prescription_item_id,
    )


__all__ = ["router"]