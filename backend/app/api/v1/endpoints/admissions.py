"""
HHMS Admission API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.admission import (
    AdmissionCreate,
    AdmissionRead,
    AdmissionUpdate,
)
from app.services.admission import admission_service


router = APIRouter(
    prefix="/admissions",
    tags=["IPD Admissions"],
)


@router.get(
    "",
    response_model=list[AdmissionRead],
)
async def list_admissions(
    db: DatabaseSession,
    _: CurrentUserDependency,
    status: str | None = Query(
        default=None,
        max_length=20,
    ),
    patient_id: int | None = Query(
        default=None,
        gt=0,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
) -> list[AdmissionRead]:
    return await admission_service.list(
        db,
        status=status,
        patient_id=patient_id,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=AdmissionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_admission(
    admission_in: AdmissionCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> AdmissionRead:
    return await admission_service.create(
        db,
        admission_in=admission_in,
    )


@router.get(
    "/{admission_id}",
    response_model=AdmissionRead,
)
async def get_admission(
    admission_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> AdmissionRead:
    return await admission_service.get_by_id(
        db,
        admission_id=admission_id,
    )


@router.patch(
    "/{admission_id}",
    response_model=AdmissionRead,
)
async def update_admission(
    admission_id: int,
    admission_in: AdmissionUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> AdmissionRead:
    return await admission_service.update(
        db,
        admission_id=admission_id,
        admission_in=admission_in,
    )


__all__ = [
    "router",
]