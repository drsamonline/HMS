"""HHMS Pain Assessment API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.pain_assessment import PainAssessmentCreate, PainAssessmentUpdate, PainAssessmentRead
from app.services.pain_assessment import painAssessment_service

router = APIRouter(prefix="/pain-assessments", tags=["Pain Assessments"])

def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])

@router.get("", response_model=list[PainAssessmentRead])
async def list_items(db: DatabaseSession, _: CurrentUserDependency, admission_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)) -> list[PainAssessmentRead]:
    return await painAssessment_service.list(db, admission_id, skip, limit)

@router.post("", response_model=PainAssessmentRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: PainAssessmentCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> PainAssessmentRead:
    data.recorded_by = _user_id(current_user)
    return await painAssessment_service.create(db, data)

@router.get("/{object_id}", response_model=PainAssessmentRead)
async def get_item(object_id: int, db: DatabaseSession, _: CurrentUserDependency) -> PainAssessmentRead:
    return await painAssessment_service.get(db, object_id)

@router.patch("/{object_id}", response_model=PainAssessmentRead)
async def update_item(object_id: int, data: PainAssessmentUpdate, db: DatabaseSession, _: CurrentUserDependency) -> PainAssessmentRead:
    return await painAssessment_service.update(db, object_id, data)

__all__ = ["router"]
