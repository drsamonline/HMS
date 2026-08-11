"""
HHMS Patient API Endpoints.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.patient import (
    PatientCreate,
    PatientRead,
    PatientUpdate,
)
from app.services.patient import patient_service


router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)


@router.get(
    "",
    response_model=list[PatientRead],
)
async def list_patients(
    db: DatabaseSession,
    _: CurrentUserDependency,
    search: str | None = Query(
        default=None,
        max_length=100,
    ),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PatientRead]:
    return await patient_service.list(
        db,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    patient_in: PatientCreate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PatientRead:
    return await patient_service.create(
        db,
        patient_in=patient_in,
    )


@router.get(
    "/{patient_id}",
    response_model=PatientRead,
)
async def get_patient(
    patient_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PatientRead:
    return await patient_service.get_by_id(
        db,
        patient_id=patient_id,
    )


@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
)
async def update_patient(
    patient_id: int,
    patient_in: PatientUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PatientRead:
    return await patient_service.update(
        db,
        patient_id=patient_id,
        patient_in=patient_in,
    )


@router.delete(
    "/{patient_id}",
    response_model=PatientRead,
)
async def deactivate_patient(
    patient_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> PatientRead:
    return await patient_service.deactivate(
        db,
        patient_id=patient_id,
    )


__all__ = [
    "router",
]