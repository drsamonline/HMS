"""
HHMS Medicine Batch API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.medicine_batch import (
    MedicineBatchCreate,
    MedicineBatchRead,
    MedicineBatchUpdate,
)
from app.services.medicine_batch import (
    medicine_batch_service,
)


router = APIRouter(
    prefix="/medicine-batches",
    tags=["Medicine Batches"],
)


@router.get(
    "/medicine/{medicine_id}",
    response_model=list[MedicineBatchRead],
)
async def list_medicine_batches(
    medicine_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
    active_only: bool = Query(default=True),
    available_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[MedicineBatchRead]:
    return await medicine_batch_service.list_by_medicine(
        db,
        medicine_id=medicine_id,
        active_only=active_only,
        available_only=available_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=MedicineBatchRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_medicine_batch(
    batch_in: MedicineBatchCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineBatchRead:
    return await medicine_batch_service.create(
        db,
        batch_in,
    )


@router.get(
    "/{batch_id}",
    response_model=MedicineBatchRead,
)
async def get_medicine_batch(
    batch_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineBatchRead:
    return await medicine_batch_service.get(
        db,
        batch_id,
    )


@router.patch(
    "/{batch_id}",
    response_model=MedicineBatchRead,
)
async def update_medicine_batch(
    batch_id: int,
    batch_in: MedicineBatchUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> MedicineBatchRead:
    return await medicine_batch_service.update(
        db,
        batch_id=batch_id,
        data=batch_in,
    )


__all__ = [
    "router",
]