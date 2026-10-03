"""
HHMS Medicine API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.medicine import (
    MedicineCreate,
    MedicineRead,
    MedicineUpdate,
)
from app.services.medicine import medicine_service


router = APIRouter(
    prefix="/medicines",
    tags=["Medicines"],
)


@router.get(
    "",
    response_model=list[MedicineRead],
)
async def list_medicines(
    db: DatabaseSession,
    _: CurrentUserDependency,
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    active_only: bool = Query(default=True),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[MedicineRead]:
    return await medicine_service.list(
        db,
        search=search,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=MedicineRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_medicine(
    medicine_in: MedicineCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineRead:
    return await medicine_service.create(
        db,
        medicine_in,
    )


@router.get(
    "/{medicine_id}",
    response_model=MedicineRead,
)
async def get_medicine(
    medicine_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineRead:
    return await medicine_service.get(
        db,
        medicine_id,
    )


@router.patch(
    "/{medicine_id}",
    response_model=MedicineRead,
)
async def update_medicine(
    medicine_id: int,
    medicine_in: MedicineUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineRead:
    return await medicine_service.update(
        db,
        medicine_id,
        medicine_in,
    )


__all__ = [
    "router",
]