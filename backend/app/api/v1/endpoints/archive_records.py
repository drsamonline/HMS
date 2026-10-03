"""HHMS ArchiveRecord API endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.archive_record import ArchiveRecordCreate, ArchiveRecordRead, ArchiveRecordUpdate
from app.services.archive_record import archive_record_service

router = APIRouter(prefix="/archive-records", tags=["Medical Records"])

@router.get("", response_model=list[ArchiveRecordRead])
async def list_archive_records(
    db: DatabaseSession, _: CurrentUserDependency,
    patient_file_id: int = Query(gt=0), skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ArchiveRecordRead]:
    return await archive_record_service.list_by_patient_file(
        db, patient_file_id, skip, limit
    )

@router.post("", response_model=ArchiveRecordRead, status_code=status.HTTP_201_CREATED)
async def create_archive_record(
    record_in: ArchiveRecordCreate, db: DatabaseSession, _: CurrentUserDependency,
) -> ArchiveRecordRead:
    return await archive_record_service.create(db, record_in)

@router.get("/{archive_id}", response_model=ArchiveRecordRead)
async def get_archive_record(
    archive_id: int, db: DatabaseSession, _: CurrentUserDependency,
) -> ArchiveRecordRead:
    return await archive_record_service.get_by_id(db, archive_id)

@router.patch("/{archive_id}", response_model=ArchiveRecordRead)
async def update_archive_record(
    archive_id: int, record_in: ArchiveRecordUpdate,
    db: DatabaseSession, _: CurrentUserDependency,
) -> ArchiveRecordRead:
    return await archive_record_service.update(db, archive_id, record_in)

__all__ = ["router"]
