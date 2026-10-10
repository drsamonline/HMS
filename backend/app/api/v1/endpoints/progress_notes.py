"""HHMS Clinical Progress Note API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.progress_note import ProgressNoteCreate, ProgressNoteUpdate, ProgressNoteRead
from app.services.progress_note import progressNote_service

router = APIRouter(prefix="/progress-notes", tags=["Clinical Progress Notes"])

def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])

@router.get("", response_model=list[ProgressNoteRead])
async def list_items(db: DatabaseSession, _: CurrentUserDependency, admission_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)) -> list[ProgressNoteRead]:
    return await progressNote_service.list(db, admission_id, skip, limit)

@router.post("", response_model=ProgressNoteRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: ProgressNoteCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> ProgressNoteRead:
    data.recorded_by = _user_id(current_user)
    return await progressNote_service.create(db, data)

@router.get("/{object_id}", response_model=ProgressNoteRead)
async def get_item(object_id: int, db: DatabaseSession, _: CurrentUserDependency) -> ProgressNoteRead:
    return await progressNote_service.get(db, object_id)

@router.patch("/{object_id}", response_model=ProgressNoteRead)
async def update_item(object_id: int, data: ProgressNoteUpdate, db: DatabaseSession, _: CurrentUserDependency) -> ProgressNoteRead:
    return await progressNote_service.update(db, object_id, data)

__all__ = ["router"]
