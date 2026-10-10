"""Hospital statistics API."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query
from uuid import UUID

from app.dependencies.auth import CurrentUserDependency
from app.dependencies.database import DatabaseSession
from app.schemas.statistics import HospitalStatistics
from app.services.statistics import statistics_service

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/hospital", response_model=HospitalStatistics)
async def get_hospital_statistics(
    db: DatabaseSession,
    _: CurrentUserDependency,
    start_date: date = Query(..., description="Inclusive reporting start date."),
    end_date: date = Query(..., description="Inclusive reporting end date."),
    department_id: UUID | None = Query(None),
    service_id: UUID | None = Query(None),
) -> HospitalStatistics:
    return await statistics_service.get_hospital_statistics(
        db,
        start_date=start_date,
        end_date=end_date,
        department_id=department_id,
        service_id=service_id,
    )


__all__ = ["router"]
