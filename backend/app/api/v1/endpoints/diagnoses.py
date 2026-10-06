"""HHMS Diagnosis API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.diagnosis import DiagnosisCreate, DiagnosisRead, DiagnosisUpdate
from app.services.diagnosis import diagnosis_service

router = APIRouter(prefix="/diagnoses", tags=["Diagnoses"])


def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])


@router.get("", response_model=list[DiagnosisRead])
async def list_diagnoses(
    db: DatabaseSession,
    _: CurrentUserDependency,
    case_record_id: int = Query(gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[DiagnosisRead]:
    return await diagnosis_service.list_by_case(db, case_record_id, skip, limit)


@router.post("", response_model=DiagnosisRead, status_code=status.HTTP_201_CREATED)
async def create_diagnosis(
    diagnosis_in: DiagnosisCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> DiagnosisRead:
    return await diagnosis_service.create(db, diagnosis_in, _user_id(current_user))


@router.get("/{diagnosis_id}", response_model=DiagnosisRead)
async def get_diagnosis(
    diagnosis_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DiagnosisRead:
    return await diagnosis_service.get_by_id(db, diagnosis_id)


@router.patch("/{diagnosis_id}", response_model=DiagnosisRead)
async def update_diagnosis(
    diagnosis_id: int,
    diagnosis_in: DiagnosisUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> DiagnosisRead:
    return await diagnosis_service.update(db, diagnosis_id, diagnosis_in)


__all__ = ["router"]
