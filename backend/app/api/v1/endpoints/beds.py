"""
HHMS Bed API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.bed import (
    BedCreate,
    BedRead,
    BedUpdate,
)
from app.services.bed import bed_service


router = APIRouter(
    prefix="/beds",
    tags=["IPD Beds"],
)


@router.get(
    "",
    response_model=list[BedRead],
)
async def list_beds(
    db: DatabaseSession,
    _: CurrentUserDependency,
    ward: str | None = Query(
        default=None,
        max_length=100,
    ),
    occupancy_status: str | None = Query(
        default=None,
        max_length=20,
    ),
    active_only: bool = Query(
        default=True,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),
) -> list[BedRead]:
    return await bed_service.list(
        db,
        ward=ward,
        occupancy_status=occupancy_status,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=BedRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_bed(
    bed_in: BedCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> BedRead:
    return await bed_service.create(
        db,
        bed_in,
    )


@router.get(
    "/{bed_id}",
    response_model=BedRead,
)
async def get_bed(
    bed_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> BedRead:
    return await bed_service.get(
        db,
        bed_id,
    )


@router.patch(
    "/{bed_id}",
    response_model=BedRead,
)
async def update_bed(
    bed_id: int,
    bed_in: BedUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> BedRead:
    return await bed_service.update(
        db,
        bed_id=bed_id,
        data=bed_in,
    )


__all__ = [
    "router",
]