"""HHMS IPD Assessment API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.ipd_assessment import IPDAssessmentCreate, IPDAssessmentUpdate, IPDAssessmentRead
from app.services.ipd_assessment import iPDAssessment_service

router = APIRouter(prefix="/ipd-assessments", tags=["IPD Assessments"])

def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])

@router.get("", response_model=list[IPDAssessmentRead])
async def list_items(db: DatabaseSession, _: CurrentUserDependency, admission_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)) -> list[IPDAssessmentRead]:
    return await iPDAssessment_service.list(db, admission_id, skip, limit)

@router.post("", response_model=IPDAssessmentRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: IPDAssessmentCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> IPDAssessmentRead:
    data.recorded_by = _user_id(current_user)
    return await iPDAssessment_service.create(db, data)

@router.get("/{object_id}", response_model=IPDAssessmentRead)
async def get_item(object_id: int, db: DatabaseSession, _: CurrentUserDependency) -> IPDAssessmentRead:
    return await iPDAssessment_service.get(db, object_id)

@router.patch("/{object_id}", response_model=IPDAssessmentRead)
async def update_item(object_id: int, data: IPDAssessmentUpdate, db: DatabaseSession, _: CurrentUserDependency) -> IPDAssessmentRead:
    return await iPDAssessment_service.update(db, object_id, data)

__all__ = ["router"]
