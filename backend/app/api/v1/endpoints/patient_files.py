"""HHMS PatientFile API endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.patient_file import PatientFileCreate, PatientFileRead, PatientFileUpdate
from app.services.patient_file import patient_file_service

router = APIRouter(prefix="/patient-files", tags=["Medical Records"])

@router.get("", response_model=list[PatientFileRead])
async def list_patient_files(
    db: DatabaseSession, _: CurrentUserDependency,
    patient_id: int = Query(gt=0), skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[PatientFileRead]:
    return await patient_file_service.list_by_patient(db, patient_id, skip, limit)

@router.post("", response_model=PatientFileRead, status_code=status.HTTP_201_CREATED)
async def create_patient_file(
    file_in: PatientFileCreate, db: DatabaseSession, _: CurrentUserDependency,
) -> PatientFileRead:
    return await patient_file_service.create(db, file_in)

@router.get("/{patient_file_id}", response_model=PatientFileRead)
async def get_patient_file(
    patient_file_id: int, db: DatabaseSession, _: CurrentUserDependency,
) -> PatientFileRead:
    return await patient_file_service.get_by_id(db, patient_file_id)

@router.patch("/{patient_file_id}", response_model=PatientFileRead)
async def update_patient_file(
    patient_file_id: int, file_in: PatientFileUpdate,
    db: DatabaseSession, _: CurrentUserDependency,
) -> PatientFileRead:
    return await patient_file_service.update(db, patient_file_id, file_in)

__all__ = ["router"]
