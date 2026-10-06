"""
HHMS Discharge API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.discharge import (
    DischargeCreate,
    DischargeRead,
)
from app.services.discharge import (
    discharge_service,
)


router = APIRouter(
    prefix="/discharges",
    tags=["IPD Discharge"],
)


@router.get(
    "",
    response_model=list[DischargeRead],
)
async def list_discharges(
    db: DatabaseSession,
    _: CurrentUserDependency,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
) -> list[DischargeRead]:
    return await discharge_service.list(
        db,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=DischargeRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_discharge(
    discharge_in: DischargeCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DischargeRead:
    return await discharge_service.create(
        db,
        data=discharge_in,
    )


@router.get(
    "/admission/{admission_id}",
    response_model=DischargeRead,
)
async def get_discharge_by_admission(
    admission_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DischargeRead:
    return await discharge_service.get_by_admission(
        db,
        admission_id,
    )


@router.get(
    "/{discharge_id}",
    response_model=DischargeRead,
)
async def get_discharge(
    discharge_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DischargeRead:
    return await discharge_service.get(
        db,
        discharge_id,
    )


__all__ = [
    "router",
]