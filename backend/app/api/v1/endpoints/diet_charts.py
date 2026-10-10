"""HHMS Diet Chart API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.diet_chart import DietChartCreate, DietChartUpdate, DietChartRead
from app.services.diet_chart import dietChart_service

router = APIRouter(prefix="/diet-charts", tags=["Diet Charts"])

def _user_id(user: CurrentUserDependency) -> int:
    return int(user["sub"])

@router.get("", response_model=list[DietChartRead])
async def list_items(db: DatabaseSession, _: CurrentUserDependency, admission_id: int = Query(gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=100, ge=1, le=200)) -> list[DietChartRead]:
    return await dietChart_service.list(db, admission_id, skip, limit)

@router.post("", response_model=DietChartRead, status_code=status.HTTP_201_CREATED)
async def create_item(data: DietChartCreate, db: DatabaseSession, current_user: CurrentUserDependency) -> DietChartRead:
    data.recorded_by = _user_id(current_user)
    return await dietChart_service.create(db, data)

@router.get("/{object_id}", response_model=DietChartRead)
async def get_item(object_id: int, db: DatabaseSession, _: CurrentUserDependency) -> DietChartRead:
    return await dietChart_service.get(db, object_id)

@router.patch("/{object_id}", response_model=DietChartRead)
async def update_item(object_id: int, data: DietChartUpdate, db: DatabaseSession, _: CurrentUserDependency) -> DietChartRead:
    return await dietChart_service.update(db, object_id, data)

__all__ = ["router"]
