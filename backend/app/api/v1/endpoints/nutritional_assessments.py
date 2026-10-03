"""HHMS Nutritional Assessment API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.nutritional_assessment import NutritionalAssessmentCreate, NutritionalAssessmentUpdate, NutritionalAssessmentRead
from app.services.nutritional_assessment import nutritionalAssessment_service

router = APIRouter(prefix="/nutritional-assessments", tags=["Nutritional Assessments"])

def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])

@router.get("", response_model=list[NutritionalAssessmentRead])
async def list_items(db: DatabaseSession, _: CurrentUserDependency, admission_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)) -> list[NutritionalAssessmentRead]:
    return await nutritionalAssessment_service.list(db, admission_id, skip, limit)

@router.post("", response_model=NutritionalAssessmentRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: NutritionalAssessmentCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> NutritionalAssessmentRead:
    data.recorded_by = _user_id(current_user)
    return await nutritionalAssessment_service.create(db, data)

@router.get("/{object_id}", response_model=NutritionalAssessmentRead)
async def get_item(object_id: int, db: DatabaseSession, _: CurrentUserDependency) -> NutritionalAssessmentRead:
    return await nutritionalAssessment_service.get(db, object_id)

@router.patch("/{object_id}", response_model=NutritionalAssessmentRead)
async def update_item(object_id: int, data: NutritionalAssessmentUpdate, db: DatabaseSession, _: CurrentUserDependency) -> NutritionalAssessmentRead:
    return await nutritionalAssessment_service.update(db, object_id, data)

__all__ = ["router"]
