"""HHMS Homoeopathic Case Record API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.case_record import CaseRecordCreate, CaseRecordRead, CaseRecordUpdate
from app.services.case_record import case_record_service

router = APIRouter(prefix="/case-records", tags=["Homoeopathic Case Records"])


def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])


@router.get("", response_model=list[CaseRecordRead])
async def list_case_records(
    db: DatabaseSession,
    _: CurrentUserDependency,
    patient_id: int = Query(gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[CaseRecordRead]:
    return await case_record_service.list_by_patient(db, patient_id, skip, limit)


@router.post("", response_model=CaseRecordRead, status_code=status.HTTP_201_CREATED)
async def create_case_record(
    case_in: CaseRecordCreate,
    db: DatabaseSession,
    current_user: CurrentUserDependency,
) -> CaseRecordRead:
    return await case_record_service.create(db, case_in, _user_id(current_user))


@router.post("/patient/{patient_id}/renew-current-year", response_model=CaseRecordRead)
async def renew_current_year_case(patient_id:int, db:DatabaseSession, current_user:CurrentUserDependency, visit_id:int|None=None, admission_id:int|None=None)->CaseRecordRead:
    return await case_record_service.renew_current_year(db, patient_id, _user_id(current_user), visit_id, admission_id)

@router.get("/{case_record_id}", response_model=CaseRecordRead)
async def get_case_record(
    case_record_id: int,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> CaseRecordRead:
    return await case_record_service.get_by_id(db, case_record_id)


@router.patch("/{case_record_id}", response_model=CaseRecordRead)
async def update_case_record(
    case_record_id: int,
    case_in: CaseRecordUpdate,
    db: DatabaseSession,
    _: CurrentUserDependency,
) -> CaseRecordRead:
    return await case_record_service.update(db, case_record_id, case_in)


__all__ = ["router"]
