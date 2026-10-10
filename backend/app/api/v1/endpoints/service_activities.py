"""API endpoints for generic departmental service activities."""
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Query, status
from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.service_activity import ServiceActivityCreate, ServiceActivityRead
from app.services.service_activity import service_activity_manager

router = APIRouter(prefix="/service-activities", tags=["Service Activities"])


@router.get("", response_model=list[ServiceActivityRead])
async def list_service_activities(
    db: DatabaseSession, _: CurrentUserDependency,
    patient_id: int | None = Query(None, gt=0),
    department_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
) -> list[ServiceActivityRead]:
    return await service_activity_manager.list(
        db, patient_id=patient_id, department_id=department_id,
        skip=skip, limit=limit,
    )


@router.post("", response_model=ServiceActivityRead, status_code=status.HTTP_201_CREATED)
async def create_service_activity(
    data: ServiceActivityCreate, db: DatabaseSession, _: CurrentUserDependency,
) -> ServiceActivityRead:
    return await service_activity_manager.create(db, data)


__all__ = ["router"]
